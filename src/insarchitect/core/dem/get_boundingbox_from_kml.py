###############################################
# Program is used for preparing DEM data      #
# Author: Lv Xiaoran                          #
# Created: October 2021                       #
###############################################

import argparse
import numpy as np
import xml.etree.ElementTree as ET

EXAMPLE = """Example:
   get_boundingbox_from_kml.py *_20211019042049.kml —-delta_lat 0.5 —-delta_lon 1.2
"""

def create_parser():
    parser = argparse.ArgumentParser(description='Get bounding box coordinates from kml file',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)

    parser.add_argument('file', nargs=1, type=str, help='kml file\n')
    parser.add_argument('--delta_lat', type=float, nargs=1, help='Delta latitude to subtract/add from minimum/maximimum latitude', default=[0.0])
    parser.add_argument('--delta_lon', nargs=1, type=float, help='Delta longitude to subtract/add from minimum/maximimum longitude', default=[0.0])

    return parser

def cmd_line_parse(iargs=None):
    parser = create_parser()
    inps = parser.parse_args(args=iargs)
    return inps

def process_kml(kml_file, delta_lat, delta_lon):
    """
    Main code to extract bounding box from KML file.
    
    Args:
        kml_file: Path to KML file (str or Path)
        delta_lat: Delta latitude to subtract/add from min/max latitude
        delta_lon: Delta longitude to subtract/add from min/max longitude
    
    Returns:
        Tuple of (lat_min, lat_max, lon_min, lon_max)
    """
    tree = ET.parse(kml_file)
    #root = tree.getroot()

    # read lon/lat coordinate into latlon_store matrix
    lineStrings = tree.findall('.//{http://earth.google.com/kml/2.1}LineString')
    if not lineStrings:
        lineStrings = tree.findall('.//{http://www.opengis.net/kml/2.2}LinearRing')
        latlon_store = np.empty(shape=[0,2], dtype=float)
        for attributes in lineStrings:
            for sub in attributes:
                if sub.tag == '{http://www.opengis.net/kml/2.2}coordinates':
                    corners = sub.text.split()
                    for corner in corners[0:-1]:
                        lon, lat, _ = corner.split(',')
                        latlon_store = np.append(latlon_store,np.array([[float(lon), float(lat)]]),axis=0)
    else:
        latlon_store = np.empty(shape=[0,2],dtype=float)
        for attributes in lineStrings:
            for subAttribute in attributes:
                if subAttribute.tag == '{http://earth.google.com/kml/2.1}coordinates':
                    corners = subAttribute.text.split(' ')
                    for corner in corners[0:-1]:
                        lon, lat, _ = corner.split(',')
                        latlon_store = np.append(latlon_store,np.array([[float(lon), float(lat)]]),axis=0)
    # select the max/min lat and lon
    lat_max = np.max(latlon_store[:,1])
    lat_min = np.min(latlon_store[:,1])

    lon_max = np.max(latlon_store[:,0])
    lon_min = np.min(latlon_store[:,0])

    # add the delta_lat/delta_lon
    lat_max2 = np.around((lat_max + delta_lat), 1)
    lat_min2 = np.around((lat_min - delta_lat), 1)

    lon_max2 = np.around((lon_max + delta_lon), 1)
    lon_min2 = np.around((lon_min - delta_lon), 1)

    return lat_min2, lat_max2, lon_min2, lon_max2

def main(iargs=None):
    inps = cmd_line_parse(iargs)

    kml_file = inps.file[0]

    delta_lat = inps.delta_lat[0]
    delta_lon = inps.delta_lon[0]

    lat_min2, lat_max2, lon_min2, lon_max2 = process_kml(kml_file=kml_file, delta_lat=delta_lat, delta_lon=delta_lon)

    lat_lon_str = f'SNWE: {lat_min2} {lat_max2} {lon_min2} {lon_max2}'
    
    return lat_lon_str

if __name__ == '__main__':
    main()