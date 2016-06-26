# wonkey

A minimal file host in Python 3 and Flask with encryption at rest, built for use with ShareX.

## why?

I'm a big fan of [ShareX](https://github.com/ShareX/ShareX), an open source screen capture tool.
For a long while, I've used imgur as a destination for my captures, but I decided I wanted to be
more in control of my data. Hence, this thing.

The name is sort of a play on "one key" per file, as well as the fact that there's no guarantee
that any of this works correctly. Don't share state secrets with it. 😉

## "your crypto is (probably) bad and you should feel bad"

Sure, I won't deny that I'm not good at this. But I think I've given it a solid shot.

The actual at-rest encryption is backed by [Fernet](https://cryptography.io/en/latest/fernet/),
which is a symmetric key cryptosystem implemented by the
[cryptography library](https://github.com/pyca/cryptography). This provides a vetted
implementation of authenticated encryption, with a small wrapper around the format to provide
streaming response capabilities.

Each file stored has a per-file key generated, which is only stored in memory during file creation
or access. It's expressed as part of the URL, so maintaining any request logs will sort of defeat
the purpose. When a client requests a file, the server transparently decrypts the file and streams
it block-by-block using chunked transfer encoding.

I'm not going to pretend to make guarantees about side-channel attacks or anything like that -
that's not the point of this. I just wanted a system where if someone gets access to my box, they
don't suddenly have every screenshot I've taken or file I've shared.

Additionally, if a truncation or authentication failure occurs halfway through decrypting a
streaming response, the server *should* disconnect the socket, letting the browser know that the
file should not be treated as a completed transfer. I haven't tested this thoroughly, however, and
some initial research indicates that this may not be a happy story, depending on your WSGI server:
http://rhodesmill.org/brandon/2013/chunked-wsgi/

## installation

Using Python 3 and virtualenv, make a virtualenv from requirements.txt, then serve wonkey.app
using your favorite WSGI server. Make sure to turn off request URL logging.

If you just want to kick the tires, you can run it with the built in Flask server by running:
`env FLASK_APP=wonkey python -m flask run`

## server configuration

wonkey supports configuration of several parameters through environment variables:

* `CHUNK_SIZE` specifies the encrypted block size used in the Fernet system. This exists to allow
streaming transfers, and can be tweaked based on benchmarking that I have not done.
* `UPLOAD_REDIRECT` specifies a URL that clients should be redirected to if they attempt to
access the root page of the server. By default, they are given a very basic HTML upload form.
* `UPLOAD_SECRET` specifies a shared secret for users to upload to the server. If undefined, anyone
can upload to the server.
* `CONTENT_DIR` specifies the directory for encrypted file storage.

## client configuration

### for ShareX users:

From the main menu, click Destinations -> Destination settings... to open the destination settings.
From there, choose "Custom uploaders" under "Other uploaders".

Enter a name and click add, then configure it like so:

* Request type: POST
* Request URL: https://YOUR_DOMAIN_HERE/
* File form name: file
* Arguments: secret = YOUR_SECRET_HERE
* Response type: Redirection URL

### for web browser usage:

If you leave `UPLOAD_REDIRECT` unconfigured, you can navigate to the application in a web browser
and get a basic upload form.

### for other usage:

* Send a multipart/form-data POST to the application root (that is, /)
* Set "file" to the file you'd like to upload
* Set "secret" to the server's shared `UPLOAD_SECRET`
* You'll be redirected to the uploaded file
