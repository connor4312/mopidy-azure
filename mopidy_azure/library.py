import logging
import json
from urllib.parse import quote, unquote
from typing import Optional

from azure.storage.blob import ContainerClient, BlobClient, BlobPrefix
from azure.core.exceptions import ResourceNotFoundError
from mopidy import backend, models, exceptions
from mopidy.audio import scan, tags

logger = logging.getLogger(__name__)
uri_prefix = "az:///"


def uri_for_blob(blob_name: str):
    return uri_prefix + "/".join(quote(x) for x in blob_name.split("/"))


def blob_for_uri(uri: str):
    return unquote(uri[len(uri_prefix) :])


def _tree_to_ref(item):
    if isinstance(item, BlobPrefix):
        return models.Ref.directory(name=item.name[:-1], uri=uri_for_blob(item.name))
    else:
        # Check if this is likely an audio file
        if _is_audio_file(item.name):
            return models.Ref.track(name=item.name, uri=uri_for_blob(item.name))
        else:
            # Treat non-audio files as generic tracks - let the scanner decide
            return models.Ref.track(name=item.name, uri=uri_for_blob(item.name))


def _is_audio_file(filename):
    """Check if a filename appears to be an audio file based on extension."""
    if not filename:
        return False

    audio_extensions = {
        ".mp3",
        ".flac",
        ".ogg",
        ".m4a",
        ".wav",
        ".aac",
        ".wma",
        ".opus",
        ".mp4",
        ".mpeg",
        ".mpga",
    }

    filename_lower = filename.lower()
    return any(filename_lower.endswith(ext) for ext in audio_extensions)


class AzureLibraryProvider(backend.LibraryProvider):
    """Library for browsing files in Azure storage."""

    root_directory = models.Ref.directory(name="Azure", uri=uri_for_blob(""))

    def __init__(self, backend, config):
        super().__init__(backend)

        self._songs: ContainerClient = backend.songs_container_client
        self._cache: ContainerClient = backend.cache_container_client
        self._scanner = scan.Scanner()

    def browse(self, uri: str):
        result = []
        prefix = blob_for_uri(uri)
        logger.info("Browsing files at: %s (prefix %s)", uri, prefix)

        for blob in self._songs.walk_blobs(name_starts_with=prefix):
            logger.info("got blob {}".format(blob.name))
            result.append(_tree_to_ref(blob))

        logger.info("Found %d files", len(result))

        def order(item):
            return (item.type != models.Ref.DIRECTORY, item.name)

        result.sort(key=order)

        return result

    def lookup(self, uri: str) -> models.Track:
        song_blob = self._songs.get_blob_client(blob_for_uri(uri))
        song_etag = song_blob.get_blob_properties().etag

        # Extract filename from URI for format checking
        blob_name = blob_for_uri(uri)
        filename = blob_name.split("/")[-1] if "/" in blob_name else blob_name

        public_uri = self.backend.get_public_uri_for(uri)
        try:
            cached_data = self._get_cached_metadata(etag=song_etag, song_uri=uri)
            if cached_data is not None:
                (song_tags, duration) = cached_data
            else:
                # Check if this looks like an audio file before scanning
                if not _is_audio_file(filename):
                    logger.info(
                        "File %s does not appear to be an audio file, "
                        "but attempting to scan anyway",
                        filename,
                    )

                result = self._scanner.scan(public_uri)
                song_tags = result.tags
                duration = result.duration

            track = tags.convert_tags_to_track(song_tags).replace(
                uri=uri, length=duration
            )

            if cached_data is None:
                self._store_cached_metadata(
                    etag=song_etag, song_uri=uri, song_tags=song_tags, duration=duration
                )
        except exceptions.ScannerError as e:
            logger.warning("Failed looking up %s at %s: %s", uri, public_uri, e)
            track = models.Track(uri=uri)

        return [track]

    def _metadata_blob_for_song_uri(self, uri: str) -> BlobClient:
        """Gets the blob reference for a song at the given URI (az:///...)"""
        return self._cache.get_blob_client(blob_for_uri(uri) + ".metadata")

    def _get_cached_metadata(self, etag: str, song_uri: str) -> Optional[models.Track]:
        """Gets cached metadata for a song at the given URI, if its etag
        matches. If an error occurs or the etag doesn't match, returns None"""

        try:
            meta_json = json.loads(
                self._metadata_blob_for_song_uri(song_uri)
                .download_blob()
                .content_as_text()
            )

            if meta_json["etag"] == etag:
                return (meta_json.get("tags", {}), meta_json.get("duration", 0))
        except ResourceNotFoundError:
            logger.debug("No existing cached metadata for %s", song_uri)
        except Exception as e:
            logger.warning(
                "Unexpected error looking up metadata for %s: %s",
                song_uri,
                e,
            )

        return None

    def _store_cached_metadata(
        self, etag: str, song_uri: str, song_tags: dict, duration: int
    ) -> None:
        """Saved the metadata cache file for the given track into blob storage"""
        if self._cache is None:
            return

        meta_out = json.dumps({"etag": etag, "tags": song_tags, "duration": duration})
        try:
            self._metadata_blob_for_song_uri(song_uri).upload_blob(
                meta_out, overwrite=True
            )
        except Exception as e:
            logger.warning("Error updating stored metadata for %s: %s", song_uri, e)
