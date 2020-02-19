from mopidy.backend import PlaybackProvider
from mopidy_azure.library import blob_for_uri


class AzurePlaybackProvider(PlaybackProvider):
    def translate_uri(self, uri):
        return self.backend.get_public_uri_for(uri)
