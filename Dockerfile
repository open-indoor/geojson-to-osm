FROM debian:testing

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y update \
    && apt-get -y upgrade \
    && apt-get -y install \
      --no-install-recommends \
      bash \
      cron \
      curl \
      fcgiwrap \
      file \
      gettext \
      git \
      grep \
      htop \
      jq \
      less \
      net-tools \
      procps \
      unzip \
      util-linux \
      uuid-runtime \
      vim \
      wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y update \
    && apt-get -y install \
      --no-install-recommends \
      python3-setuptools \
      python3-shapely \
      python3-geopandas \
      python3-geojson \
      python3-pycurl \
      python3-pip \
      python3-wheel \
      python3-rtree \
      python3-pyproj \
      python3-geopy \
      python3-geographiclib \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /geojson-to-osm
WORKDIR /geojson-to-osm
COPY ./requirements.txt /geojson-to-osm/
RUN pip3 install -v -r /geojson-to-osm/requirements.txt

COPY ./geojson-to-osm.py /geojson-to-osm/geojson-to-osm
RUN chmod +x /geojson-to-osm/geojson-to-osm

CMD /geojson-to-osm/geojson-to-osm



