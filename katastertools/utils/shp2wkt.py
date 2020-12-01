#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert data from ESRI Shapefile to text format containing object ID and WKT.

USAGE: shp2wkt.py <input-file>

    input-file		absolute path to input ESRI Shapefile
"""
import os
import sys

from osgeo import ogr


def main():
    try:
        infile = sys.argv[1]
    except IndexError:
        print(__doc__)
        sys.exit(0)

    sdriver = ogr.GetDriverByName('ESRI Shapefile')

    sds = sdriver.Open(infile, 0)
    if sds is None:
        print('Could not open file')
        sys.exit(1)

    outfile = f'{os.path.splitext(infile)[0]}.txt'
    print(f"Processing file {infile} to {outfile} ...")

    slayer = sds.GetLayer()
    sfeature = slayer.GetNextFeature()

    count_features = 0
    with open(outfile, 'w') as f:
        while sfeature:
            count_features += 1
            print(f'Feature #{sfeature.GetFID()}\r', end=' ')

            geom = sfeature.GetGeometryRef()
            line = f'{sfeature.GetField("o_id")};{geom.ExportToWkt()}\n'
            f.write(line)

            # destroy
            sfeature.Destroy()
            sfeature = slayer.GetNextFeature()

    print()
    print('Done. Total Features: {0}'.format(count_features))

    sds.Destroy()


if __name__ == '__main__':
    main()
