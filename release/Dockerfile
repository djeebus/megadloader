ARG MEGASDK_VERSION=3.4.7
ARG VERSION

FROM alpine:3.9 as builder

ARG MEGASDK_VERSION

WORKDIR /wheels

RUN apk add --no-cache git
RUN git clone https://github.com/meganz/sdk.git /sdk

RUN apk add --no-cache \
    autoconf automake libtool \
    'python3<3.7' \
    python3-dev

RUN apk add --no-cache \
    --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ \
    c-ares-dev \
    crypto++-dev \
    curl-dev \
    file \
    freeimage-dev \
    g++ \
    make \
    libsodium-dev \
    libressl2.7-libcrypto \
    libssl1.1 \
    sqlite-dev \
    swig \
    zlib-dev

RUN \
    cd /sdk && \
    git checkout v${MEGASDK_VERSION} && \
    ./autogen.sh && \
    PYTHON_VERSION=3.6 ./configure \
        --disable-silent-rules \
        --enable-python \
        --disable-examples \
        --with-python3 && \
    make && \
    cd bindings/python/ && \
    python3.6 -m pip install wheel && \
    python3.6 setup.py bdist_wheel

RUN cp /sdk/bindings/python/dist/megasdk-${MEGASDK_VERSION}-py2.py3-none-any.whl /wheels

ADD reqs.txt /wheels

RUN python3.6 -m pip wheel \
    --no-cache-dir --disable-pip-version-check \
    -r /wheels/reqs.txt

FROM alpine:3.9 as release

ARG MEGASDK_VERSION
ARG VERSION

COPY --from=builder /wheels /wheels

RUN apk add --no-cache \
    --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ \
    c-ares \
    crypto++ \
    freeimage \
    libcurl \
    libgcc \
    libressl2.7-libcrypto \
    libsodium \
    libssl1.1 \
    libstdc++ \
    'python3<3.7'

# not sure why this is necessary :(
RUN ln -s /usr/lib/libcryptopp.so /usr/lib/libcryptopp.so.5.6
RUN ln -s /usr/lib/python3.6/site-packages/mega/libmega.so /usr/lib/libmega.so.30407

RUN python3.6 -m pip install --no-index --find-links /wheels/ \
    -r /wheels/reqs.txt /wheels/megasdk-${MEGASDK_VERSION}-py2.py3-none-any.whl

ADD megadloader-${VERSION}-py3-none-any.whl /wheels

RUN python3.6 -m pip install --no-index /wheels/megadloader-${VERSION}-py3-none-any.whl

RUN mkdir /config
ADD app.ini /config/

RUN rm /wheels -r

RUN mkdir /data

VOLUME ["/data", "/config"]

EXPOSE 80/tcp

ENTRYPOINT ["/usr/bin/pserve", "/config/app.ini"]
