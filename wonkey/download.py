import mimetypes
import os
import re
import struct

import flask
import werkzeug

from .bytesfernet import BytesFernet
from .config import config

def extract_metadata(filepath):
    with open(filepath, 'rb') as f:
        metadata = []
        f.seek(0, os.SEEK_END)
        eof = f.tell()
        f.seek(0)
        while f.tell() < eof:
            size, encrypted_size = struct.unpack('<II', f.read(8))
            metadata.append((size, encrypted_size))
            f.seek(encrypted_size, os.SEEK_CUR)
        return metadata

def decrypt(filepath, key, start, end):
    with open(filepath, 'rb') as f:
        fernet = BytesFernet(key)

        offset = 0
        while True:
            metadata = f.read(8)
            if not len(metadata):
                break
            size, encrypted_size = struct.unpack('<II', metadata)

            if offset + size < start:
                offset += size
                f.seek(encrypted_size, os.SEEK_CUR)
                continue
            elif offset > end:
                break

            encrypted_chunk = f.read(encrypted_size)
            chunk = fernet.decrypt(encrypted_chunk)
            assert size == len(chunk)

            # i have not proven this correct, merely tested it
            yield chunk[max(start - offset, 0) : min(end - offset + 1, len(chunk))]
            offset += size

def range_parser(filesize):
    header = flask.request.headers.get('Range', '')
    match = re.match(r'^bytes=(\d+)?-(\d+)?$', header)
    if not match:
        return None

    start, end = (None if x is None else int(x) for x in match.groups())
    if start is None and end is None:
        return None
    elif start is not None and end is not None and start > end:
        return None
    elif start is not None and start >= filesize:
        return None

    if start is None:
        start = max(filesize - end, 0)
        end = filesize - 1
    if end is None:
        end = filesize - 1
    end = min(end, filesize - 1)
    return (start, end)

def guess_mimetype(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def handle_download(filename):
    secure_filename = werkzeug.secure_filename(filename)
    key, filename = werkzeug.secure_filename(filename).split('.', 1)
    filepath = os.path.join(config.content_dir, filename)
    if not os.path.isfile(filepath):
        flask.abort(404)

    status_code = 200
    headers = {
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'max-age=315360000',
        'ETag': '"{}"'.format(secure_filename)
    }

    metadata = extract_metadata(filepath)
    filesize = sum(chunk[0] for chunk in metadata)
    range_request = range_parser(filesize)
    if range_request:
        headers['Content-Range'] = 'bytes {}-{}/{}'.format(*range_request, filesize)
        status_code = 206

    # check if key works on first block...
    # truncation due to a later bad block is still a bitch, but let's tackle the easy problem
    try:
        assert len(list(decrypt(filepath, key, 0, 0))[0]) == 1
    except Exception:
        flask.abort(404)

    decrypt_generator = decrypt(filepath, key, *(range_request or (0, filesize - 1)))

    response = flask.Response(
        decrypt_generator,
        headers=headers,
        status=status_code,
        mimetype=guess_mimetype(filename))
    return response


