import logging
from datetime import datetime, timedelta

import pykka

from mopidy import backend
from azure.storage.blob import (
    BlobServiceClient,
    generate_container_sas,
    BlobSasPermissions,
)


from mopidy_azure.library import AzureLibraryProvider, blob_for_uri
from mopidy_azure.playback import AzurePlaybackProvider

logger = logging.getLogger(__name__)
playback_sas_ttl = timedelta(hours=24)


class SharedAccessKey:
    def __init__(self, expires_at: datetime, value: str):
        self.expires_at = expires_at
        self.value = value


class AzureBackend(pykka.ThreadingActor, backend.Backend):
    @property
    def account_name(self) -> str:
        return str(self._config["azure"]["account_name"])

    @property
    def songs_container(self) -> str:
        return str(self._config["azure"]["songs_container"])

    @property
    def cache_container(self) -> str:
        return str(self._config["azure"]["cache_container"])

    @property
    def account_url(self) -> str:
        return "https://{}.blob.core.windows.net".format(self.account_name)

    def __init__(self, config, audio):
        super().__init__()
        self._config = config
        self._sas = SharedAccessKey(datetime.utcnow(), "")

        self.account_client = BlobServiceClient(
            account_url=self.account_url,
            credential=str(config["azure"]["account_key"]),
        )
        logger.info(
            "url={}, cred={}".format(
                self.account_url, str(config["azure"]["account_key"])
            )
        )
        logger.info(
            "containers: {}".format(list(self.account_client.list_containers()))
        )
        self.songs_container_client = self.account_client.get_container_client(
            self.songs_container
        )
        self.cache_container_client = self.account_client.get_container_client(
            self.cache_container
        )

        self.library = AzureLibraryProvider(backend=self, config=config)
        self.playback = AzurePlaybackProvider(audio=audio, backend=self)

        self.uri_schemes = ["az"]

    def get_playback_sas(self) -> SharedAccessKey:
        """Gets (renewing if necessary) a shared access key for playing back tracks."""

        if self._sas.expires_at > datetime.utcnow() + timedelta(hours=1):
            return self._sas

        expires_at = datetime.utcnow() + playback_sas_ttl
        value = generate_container_sas(
            account_name=self.account_name,
            account_key=self._config["azure"]["account_key"],
            container_name=self.songs_container,
            permission=BlobSasPermissions(read=True),
            expiry=expires_at,
        )

        self._sas = SharedAccessKey(expires_at, value)
        return self._sas

    def get_public_uri_for(self, song_uri: str) -> str:
        """Gets the publicly accessible URI for the song--the blob URI with an
        appropriate shared access key appended"""
        sas = self.get_playback_sas()
        subpath = blob_for_uri(song_uri)
        return (
            self.account_url
            + "/"
            + self.songs_container
            + "/"
            + subpath
            + "?"
            + sas.value
        )
