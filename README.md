# geojson-to-osm

## Build

```
docker build \
    --label openindoor/geojson-to-osm \
    -t openindoor/geojson-to-osm \
    geojson-to-osm
```

## Deploy

```
docker tag openindoor/geojson-to-osm openindoor/geojson-to-osm:1.0.0
docker push  openindoor/geojson-to-osm:1.0.0
```

## Usage

```
docker run \
    -v $(pwd)/../private_data/PLANS:/data \
    -it \
    openindoor/geojson-to-osm
```