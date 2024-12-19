# pyMS Sync

Syncing your files with some intelligence.
This program sync files between a local directory and a remote directory.
The program constantly watches the local directory. When a new file is created it flags this file creates a new thread 
which checks to see when the file is finished. This is useful for larger files like mass spectrometry files which are 
streamed to the local directory. When no more changes happen to the file, the program performs a MD5 checksum and moves 
the file over to the remote directory. Once the file is moved, the file is moved into the remote directory an MD5 
checksum is performed on the remote file. If the checksums match, the move is finished. If the checksum fails the file 
watches continues to watch the file until the checksums match. Note that there is a 1hr timeout on the file watch per 
file.

## Installation

```bash
pip install -r requirements.txt
pip install pyms_sync
```

## Limitations

Currently, it supports a mounted remote drive only.

## Usage

```bash
pyms_sync --local_dir /path/to/local --remote_dir /path/to/remote
```