#!/usr/bin/env bash

set -e

VERSION=${1:-$VERSION}
if [[ -z ${VERSION} ]]; then
    echo "usage: $0 VERSION"
    exit 0
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

# build frontend assets
cd ${DIR}/../ && yarn run build:release

# build backend assets
cd ${DIR}/.. && VERSION=${VERSION} python3.6 setup.py bdist_wheel

# copy backend reqs
cp ${DIR}/../reqs.txt ${DIR}/app.ini ${DIR}/../dist/

docker build ${DIR}/../dist/ \
    --file ${DIR}/Dockerfile \
    --build-arg VERSION=${VERSION} \
    --tag djeebus/megadloader:${VERSION} \
    --tag djeebus/megadloader:latest

echo "now run \"docker push djeebus/megadloader:${VERSION}\""
