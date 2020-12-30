#!/usr/bin/python3

import numpy
import pyproj
from geographiclib.geodesic import Geodesic
import geopy.distance
import pathlib
import geopandas
import pandas
import geojson
from shapely.geometry import Point
import json
import uuid
from turfpy.measurement import bbox_polygon, bbox, distance, bearing
from turfpy.transformation import transform_translate, transform_rotate, transform_scale

import shapely
from shapely.geometry import asShape
from shapely.geometry import shape
from shapely.geometry import mapping
from pprint import pprint
import re

# move autocad plan to GPS position (AutoCAD rotation, GPS translation)
def gpsize(geojson_fn, bounds_geojson_fn, result_fn, layer_filter=[]):
    print('********************* gpsize *********************')

    print('Load files...')
    bounds_gps = geopandas.read_file(bounds_geojson_fn, crs = 'EPSG:4326')
    autocad_gdf = geopandas.read_file(geojson_fn, crs = 'EPSG:27561')

    # FILTER
    print('Filter on layers...')
    autocad_filtered_gdf = autocad_gdf[autocad_gdf['Layer'].map(lambda layer: layer in layer_filter)]

    print('Rotation...')
    # ROTATE
    # Anticipate angle after epsg transformation
    point0 = Point((autocad_filtered_gdf.total_bounds[0], autocad_filtered_gdf.total_bounds[1]))
    point1 = Point((autocad_filtered_gdf.total_bounds[0], autocad_filtered_gdf.total_bounds[3]))
    side = geopandas.GeoDataFrame({'geometry': [point0, point1]}, crs = 'EPSG:27561')
    side_gps = side.to_crs('EPSG:4326')
    init_angle = Geodesic.WGS84.Inverse(
        side_gps.iloc[0].geometry.coords[0][1], side_gps.iloc[0].geometry.coords[0][0],
        side_gps.iloc[1].geometry.coords[0][1], side_gps.iloc[1].geometry.coords[0][0]
    )
    # Process bounds angle
    inverse = Geodesic.WGS84.Inverse(
        bounds_gps.iloc[0].geometry.coords[0][1], bounds_gps.iloc[0].geometry.coords[0][0],
        bounds_gps.iloc[0].geometry.coords[3][1], bounds_gps.iloc[0].geometry.coords[3][0]
    )
    # Apply rotation
    autocad_rotated_gdf = autocad_filtered_gdf.set_geometry(
        autocad_filtered_gdf.rotate(
            -inverse['azi1'] + init_angle['azi1'],
            origin = Point((0, 0))
        )
    )
    # Move from AutoCAD to GPS coordinates
    rotated_gdf = autocad_rotated_gdf.set_crs('EPSG:27561', allow_override=True).to_crs('EPSG:4326')

    # Translation
    print('Translation...')
    translated_gdf = rotated_gdf.set_geometry(
        rotated_gdf.translate(
            xoff = bounds_gps.total_bounds[0] - rotated_gdf.total_bounds[0],
            yoff = bounds_gps.total_bounds[1] - rotated_gdf.total_bounds[1]
        )
    )

    print('Save result...')
    translated_gdf.to_file(result_fn, driver='GeoJSON')

def osmize(
    gpsized_geojson_fn,
    oid_geojson_fn,
    area_layers=[],
    label_layers=[],
    level = None
    ):
    print('********************* osmize *********************')
    print('Load file...')
    gpsized_gdf = geopandas.read_file(gpsized_geojson_fn, crs = 'EPSG:4326')

    print('Split layers...')
    indoor_gdf = gpsized_gdf[gpsized_gdf['Layer'].map(lambda layer: layer in area_layers)][['geometry', 'Text']]

    print('Merge data...')
    for label_layer in label_layers:
        print('Merge with layer: ' + label_layer)
        label_gdf = gpsized_gdf[gpsized_gdf['Layer'].map(lambda layer: layer == label_layer)][['geometry', 'Text']]
        indoor_gdf = indoor_gdf[['geometry', 'Text']]
        indoor_gdf = geopandas.sjoin(
            indoor_gdf,
            label_gdf,
            how='left',
            op='contains',
            lsuffix='indoor',
            rsuffix='label'
        )
        print('Beautify result...')
        indoor_gdf['Text'] = numpy.where(
            pandas.isnull(indoor_gdf['Text_indoor']),
            indoor_gdf['Text_label'],
            indoor_gdf['Text_indoor']
        )

    indoor_gdf = indoor_gdf[['geometry', 'Text']]
    indoor_gdf['indoor'] = 'room'
    if level:
        indoor_gdf['level'] = level
    print('Save result...')
    indoor_gdf.to_file(oid_geojson_fn, driver='GeoJSON')

# for each plan in geojson format file, apply 3 actions:
# - Place plan in GPS location 
# - Create OpenIndoor Geojson
for rtx_geojson_fn in pathlib.Path('/data/').glob('**/*_rtx.geojson'):
    print('rtx_geojson_fn: ' + str(rtx_geojson_fn))
    bounds_geojson_fn = str(rtx_geojson_fn).replace('_rtx.geojson', '_bounds.geojson')
    oid_geojson_fn = str(rtx_geojson_fn).replace('_rtx.geojson', '_openindoor.geojson')
    gpsized_geojson_fn = str(rtx_geojson_fn).replace('_rtx.geojson', '_gpsized.geojson')
    oid_geojson_fn = str(rtx_geojson_fn).replace('_rtx.geojson', '_oid.geojson')

    level_search = re.search('.*/floor_([0-9])+/.*_rtx.geojson', str(rtx_geojson_fn))
    level = level_search.group(1)
    print('level: ' + level)

    gpsize(
        str(rtx_geojson_fn),
        bounds_geojson_fn,
        gpsized_geojson_fn,
        layer_filter=[
            '50 VIGNETTE',
            '41 N° POSTE DE TRAVAIL',
            '42 N° SALLES ET PORTES',
            'INFO CHSCT',
            '58 CADRE ETAGE'
        ]
    )

    osmize(
        gpsized_geojson_fn,
        oid_geojson_fn,
        area_layers=[
            'INFO CHSCT'
        ],
        label_layers=[
            '42 N° SALLES ET PORTES',
            '50 VIGNETTE',
            '41 N° POSTE DE TRAVAIL',
            'INFO CHSCT'
        ],
        level = level
    )
