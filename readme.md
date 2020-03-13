Development
================

1. Install docker
2. Run `npm start`
3. Open [localhost:10101](http://localhost:10101/) in the browser

API Calls
=========

GET /api/status
- returns the status of the app

POST /api/urls/ {mega_url}
- sends the url to the backend

DELETE /api/urls/{url_id}
- deletes a url from the history

GET /api/categories/
- get a list of categories supported by the server

POST /api/categories/ {name}
zz

Install mega-sdk locally
========================

```bash
$ sudo apt install \
    autoconf \
    swig libfreeimage-dev libcurl4-openssl-dev libc-ares-dev libsqlite3-dev \
    libsodium-dev libcrypto++-dev libtool libssl-dev python3.6-dev \
    python3-wheel
$ git clone https://github.com/meganz/sdk.git --branch v3.5.4 --single-branch
$ cd sdk
$ ./autogen.sh
$ PYTHON_VERSION=3.6 ./configure \
    --disable-silent-rules \
    --enable-python \
    --disable-examples \
    --with-python3
$ make
$ cd bindings/python/
$ python setup.py bdist_wheel
$ pip install dist/megasdk-*.whl

```
