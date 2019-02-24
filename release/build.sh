#!/usr/bin/env bash

set -e

VERSION=$1
if [[ -z ${VERSION} ]]; then
    echo "usage: $0 VERSION"
    exit 0
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

# build backend assets
cd ${DIR}/.. && VERSION=${VERSION} python setup.py bdist_wheel

# build frontend assets
cd ${DIR}/../ && yarn run build:release

# copy backend reqs
cp ${DIR}/../reqs.txt ${DIR}/app.ini ${DIR}/../dist/

docker build ${DIR}/../dist/ \
    --file ${DIR}/Dockerfile \
    --build-arg VERSION=${VERSION} \
    --tag megadloader:${VERSION}
