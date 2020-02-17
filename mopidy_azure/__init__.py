import pathlib

import pkg_resources

from mopidy import config, ext
from mopidy.exceptions import ExtensionError

__version__ = pkg_resources.get_distribution("Mopidy-Azure").version


class Extension(ext.Extension):

    dist_name = "Mopidy-Azure"
    ext_name = "azure"
    version = __version__

    def get_default_config(self):
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["account_name"] = config.String()
        schema["account_key"] = config.Secret()
        schema["container"] = config.String()
        return schema

    def validate_config(self, config):  # no_coverage
        if not config.getboolean("azure", "enabled"):
            return

        if not config.get("azure", "account_key"):
            raise ExtensionError("Azure account_key missing")

        if not config.get("azure", "account_name"):
            raise ExtensionError("Azure account_name missing")

        if not config.get("azure", "container"):
            raise ExtensionError("Azure container missing")

    def setup(self, registry):
        from .actor import AzureBackend

        registry.add("backend", AzureBackend)
