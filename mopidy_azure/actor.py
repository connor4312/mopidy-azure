import logging
from datetime import datetime, timedelta

import pykka

from mopidy import backend
from azure.storage.blob import (
    BlobServiceClient,
    generate_container_sas,
    BlobSasPermissions,
)

from mopidy_azure.library import AzureLibraryProvider
from mopidy_azure.playback import AzurePlaybackProvider

logger = logging.getLogger(__name__)
playback_sas_ttl = timedelta(hours=24)


class SharedAccessKey:
    def __init__(self, expires_at: datetime, value: str):
        self.expires_at = expires_at
        self.value = value


class AzureBackend(pykka.ThreadingActor, backend.Backend):
    @property()
    def account_name(self):
        return self._config.get("azure", "account_name")

    @property()
    def container(self):
        return self._config.get("azure", "container")

    @property()
    def account_url(self):
        return "https://{}.blob.core.windows.net".format(self.account_name)

    def __init__(self, config, audio):
        super().__init__()
        self._config = config
        self._sas = SharedAccessKey(datetime.utcnow(), "")

        self.container = config.get("azure", "container")
        self.account_client = BlobServiceClient(
            account_url=self.account_url, credential=config.get("azure", "account_key"),
        )
        self.container_client = self.account_client.get_container_client(self.container)

        self.library = AzureLibraryProvider(backend=self)
        self.playback = AzurePlaybackProvider(audio=audio, backend=self)

        self.uri_schemes = ["soundcloud", "sc"]

    def on_start(self):
        username = self.remote.user.get("username")
        if username is not None:
            logger.info(f"Logged in to SoundCloud as {username!r}")

    def get_playback_sas(self) -> SharedAccessKey:
        """Gets (renewing if necessary) a shared access key for playing back tracks."""

        if self._sas.expires_at > datetime.utcnow() + timedelta(hours=1):
            return self._sas

        expires_at = datetime.utcnow() + playback_sas_ttl
        value = generate_container_sas(
            account_name=self._config.get("azure", "account_name"),
            account_key=self._config.get("azure", "account_key"),
            container_name=self.container,
            permission=BlobSasPermissions(read=True),
            expiry=expires_at,
        )

        self._sas = SharedAccessKey(expires_at, value)
        return self._sas
