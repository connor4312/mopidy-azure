# Mopidy Azure

A Mopidy extension for playing music from Azure Storage.

## Features

- Stream audio files directly from Azure Blob Storage
- **Enhanced MP3 playback support** with progressive download buffering
- Support for multiple audio formats: MP3, FLAC, OGG, M4A, WAV, AAC, WMA, OPUS
- Automatic audio file detection and format validation
- Metadata caching for improved performance
- Azure Storage integration with SAS token authentication

## Audio Format Support

This extension provides optimized support for streaming audio files from Azure Storage:

- **Progressive Download**: Enabled for MP3, FLAC, OGG, M4A, WAV, and AAC files to improve streaming performance
- **Format Detection**: Automatically identifies audio files by extension
- **Error Handling**: Graceful handling of unsupported formats and scanning errors

## Installation

```bash
pip install Mopidy-Azure
```

## Configuration

Add the following to your Mopidy configuration:

```ini
[azure]
enabled = true
account_name = your_storage_account_name
account_key = your_storage_account_key
songs_container = your_music_container
cache_container = mopidy
```
