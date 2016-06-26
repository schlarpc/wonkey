import os

import flask

from .bytesfernet import BytesFernet
from .config import config
from .download import handle_download
from .upload import handle_upload

app = flask.Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload():
    if flask.request.method == 'GET':
        if config.upload_redirect:
            return flask.redirect(config.upload_redirect)
        else:
            return flask.render_template('upload.html')
    return handle_upload()

@app.route('/<filename>')
def download(filename):
    return handle_download(filename)

@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

@app.route('/robots.txt')
def robots():
    return flask.send_from_directory(os.path.join(app.root_path, 'static'), 'robots.txt')
