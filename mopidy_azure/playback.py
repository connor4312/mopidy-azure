from mopidy.backend import PlaybackProvider
from mopidy.internal import path


class AzurePlaybackProvider(PlaybackProvider):
    def translate_uri(self, uri):
        sas = self.backend.get_playback_sas()
        subpath = path.uri_to_path(uri).as_posix()
        uri = self.backend.account_url + "/" + self.backend.container + subpath + sas
        return uri
