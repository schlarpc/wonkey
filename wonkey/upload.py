import base64
import os
import struct
import uuid

import flask
import werkzeug

from .bytesfernet import BytesFernet
from .config import config

def handle_upload():
    upload = flask.request.files['file']
    secret = flask.request.form.get('secret', '')

    if secret != config.upload_secret:
        flask.abort(403)

    extension = os.path.splitext(werkzeug.secure_filename(upload.filename))[1]
    if not extension:
        raise ValueError()

    filename = base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf-8').rstrip('=') + extension
    filepath = os.path.join(config.content_dir, filename)

    key = BytesFernet.generate_key()
    fernet = BytesFernet(key)

    with open(filepath, 'wb') as f:
        while True:
            chunk = upload.read(config.chunk_size)
            if not len(chunk):
                break
            encrypted_chunk = fernet.encrypt(chunk)
            metadata = struct.pack('<II', len(chunk), len(encrypted_chunk))
            f.write(metadata + encrypted_chunk)

    return flask.redirect(flask.request.url_root + key + '.' + filename)
