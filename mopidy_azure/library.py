import logging

from azure.storage.blob import ContainerClient
from mopidy import backend, models
from mopidy.internal import path

logger = logging.getLogger(__name__)


class AzureLibraryProvider(backend.LibraryProvider):
    """Library for browsing files in Azure storage."""

    root_directory = models.Ref.directory(name="Azure", uri=path.path_to_uri("/"))

    def __init__(self, backend, config):
        super().__init__(backend)

        self._client: ContainerClient = backend.container_client

    def browse(self, uri):
        result = []
        prefix = path.uri_to_path(uri).as_posix().lstrip("/")
        logger.debug("Browsing files at: %s (prefix %s)", uri, prefix)

        for blob in self._client.walk_blobs(name_starts_with=prefix):
            logger.info(blob)
            result.append(
                models.Ref.track(name=blob.name, uri=path.path_to_uri(blob.name))
            )

        def order(item):
            return (item.type != models.Ref.DIRECTORY, item.name)

        result.sort(key=order)

        return result
