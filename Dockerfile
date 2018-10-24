FROM ubuntu:18.04

RUN \
    apt update && \
    apt install -y apt-utils && \
    apt install -y \
        # backend dependencies
        python3.6-dev python3-distutils python3-pip python3-setuptools python3-wheel \
        # build dependencies
        git autoconf g++ zlib1g-dev make libtool \
        # megasdk dependencies
        swig libfreeimage-dev libcurl4-openssl-dev libc-ares-dev libsqlite3-dev \
        libsodium-dev libcrypto++-dev libssl-dev

RUN python3.6 -m pip install --upgrade pip

RUN git clone https://github.com/meganz/sdk.git

RUN \
    cd sdk && \
    ./autogen.sh && \
    PYTHON_VERSION=3.6 ./configure \
        --disable-silent-rules \
        --enable-python \
        --disable-examples \
        --with-python3 && \
    make && \
    cd bindings/python/ && \
    python3.6 setup.py bdist_wheel

RUN python3.6 -m pip install /sdk/bindings/python/dist/megasdk-*.whl

ADD reqs.txt /src/
RUN python3.6 -m pip install -r/src/reqs.txt

VOLUME ["/src"]
WORKDIR /src
EXPOSE 10101/tcp
ENTRYPOINT python3.6 -m pip install -e /src && pserve /src/app.ini --reload
