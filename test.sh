#!/bin/bash

set -x
set -e
docker build \
    --label openindoor/geojson-to-osm \
    -t openindoor/geojson-to-osm \
    geojson-to-osm

docker run \
    -v $(pwd)/../private_data/PLANS:/data \
    -v $(pwd)/geojson-to-osm/geojson-to-osm.py:/geojson-to-osm/geojson-to-osm \
    -it openindoor/geojson-to-osm