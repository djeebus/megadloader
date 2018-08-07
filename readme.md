Install mega-sdk
================

```bash
$ sudo apt install \
    swig libfreeimage-dev libcurl4-openssl-dev libc-ares-dev libsqlite3-dev \
    libsodium-dev libcrypto++-dev libtool libssl-dev python3.6-dev \
    python3-wheel
$ git clone https://github.com/meganz/sdk.git
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



API Calls
=========

GET /api/status 
- returns the status of the app

POST /api/urls/ 
mega_url=$SOME_URL
- sends the url to the backend
