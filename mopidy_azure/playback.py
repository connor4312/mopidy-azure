import logging
from mopidy.backend import PlaybackProvider

logger = logging.getLogger(__name__)


class AzurePlaybackProvider(PlaybackProvider):

    # Supported audio formats that benefit from progressive download
    _AUDIO_FORMATS = {".mp3", ".flac", ".ogg", ".m4a", ".wav", ".aac"}

    def translate_uri(self, uri):
        """Convert Azure URI to publicly accessible blob URL."""
        if not uri or not uri.startswith("az:///"):
            logger.warning("Invalid Azure URI format: %s", uri)
            return None

        try:
            public_uri = self.backend.get_public_uri_for(uri)
            logger.debug("Translated %s to %s", uri, public_uri)
            return public_uri
        except Exception as e:
            logger.error("Failed to translate URI %s: %s", uri, e)
            return None

    def should_download(self, uri):
        """Enable progressive download for supported audio formats.

        This improves playback performance for fixed-length audio files
        like MP3 by buffering the entire file during streaming.
        """
        if not uri:
            return False

        # Extract file extension from URI
        uri_lower = uri.lower()
        for ext in self._AUDIO_FORMATS:
            if uri_lower.endswith(ext):
                logger.debug(f"Enabling progressive download for {ext} file: {uri}")
                return True

        return False
