# -*- coding: utf-8 -*-
"""
Created on Mon Nov 14, 2022
Script for reading in arcdr files and writing 
all the info into a csv in parallel. 

Command for creating a file with all the lbl
files needed:
[find $PWD -type f -name "adf*.lbl" >> filelist]
[find $PWD -type f -name "rdf*.lbl" >> filelist]

@author: Indujaa, Michael
"""

import argparse
import glob
import os

import geopandas as gpd
import numpy as np
import pandas as pd
from tqdm import tqdm

from ARCDR import readARCDR


def cli():
    parser = argparse.ArgumentParser(
        description="Generate geopackage from Magellan ARCDR files"
    )
    parser.add_argument(
        "dir",
        type=str,
        help="Magellan data directory",
    )
    parser.add_argument(
        "type",
        type=str,
        help="File type",
        choices=["adf", "rdf"],
    )
    return parser.parse_args()


def arcdr2gpkg(file, ftype):
    fname = file.split("/")[-1].split(".")[0]
    orbitnum = "".join([i for i in fname if i.isdigit()])

    hdr, data = readARCDR(file)

    df = pd.DataFrame()

    # Split up some multi element fields, name the rest (to toss)
    if ftype == "adf":
        df["ALT_SPACECRAFT_POSITION_VECTOR_X"] = data["ALT_SPACECRAFT_POSITION_VECTOR"][
            :, 0
        ]
        df["ALT_SPACECRAFT_POSITION_VECTOR_Y"] = data["ALT_SPACECRAFT_POSITION_VECTOR"][
            :, 1
        ]
        df["ALT_SPACECRAFT_POSITION_VECTOR_Z"] = data["ALT_SPACECRAFT_POSITION_VECTOR"][
            :, 2
        ]

        df["ALT_SPACECRAFT_VELOCITY_VECTOR_X"] = data["ALT_SPACECRAFT_VELOCITY_VECTOR"][
            :, 0
        ]
        df["ALT_SPACECRAFT_VELOCITY_VECTOR_Y"] = data["ALT_SPACECRAFT_VELOCITY_VECTOR"][
            :, 1
        ]
        df["ALT_SPACECRAFT_VELOCITY_VECTOR_Z"] = data["ALT_SPACECRAFT_VELOCITY_VECTOR"][
            :, 2
        ]

        df["NON_RANGE_SHARP_ECHO_PROF_MEAN"] = np.mean(
            data["NON_RANGE_SHARP_ECHO_PROF"]
        )
        df["NON_RANGE_SHARP_ECHO_PROF_STDEV"] = np.std(
            data["NON_RANGE_SHARP_ECHO_PROF"]
        )

        delFields = [
            "ALT_SPACECRAFT_POSITION_VECTOR",
            "ALT_SPACECRAFT_VELOCITY_VECTOR",
            "FORMAL_ERRORS_GROUP",  # not split yet
            "FORMAL_CORRELATIONS_GROUP",  # not split yet
            "ALT_PARTIALS_GROUP",  # not split yet
            "NON_RANGE_SHARP_ECHO_PROF",  # not split yet but have taken mean and stdev
            "BEST_NON_RANGE_SHARP_MODEL_TPT",  # not split yet
            "RANGE_SHARP_ECHO_PROFILE",  # not split yet
            "BEST_RANGE_SHARP_MODEL_TMPLT",  # not split yet
            "SPARE",  # not split yet
        ]
        lon = data["ALT_FOOTPRINT_LONGITUDE"]
        lat = data["ALT_FOOTPRINT_LATITUDE"]

    elif ftype == "rdf":
        df["RAD_SPACECRAFT_POSITION_VECTOR_X"] = data["RAD_SPACECRAFT_POSITION_VECTOR"][
            :, 0
        ]
        df["RAD_SPACECRAFT_POSITION_VECTOR_Y"] = data["RAD_SPACECRAFT_POSITION_VECTOR"][
            :, 1
        ]
        df["RAD_SPACECRAFT_POSITION_VECTOR_Z"] = data["RAD_SPACECRAFT_POSITION_VECTOR"][
            :, 2
        ]

        df["RAD_SPACECRAFT_VELOCITY_VECTOR_X"] = data["RAD_SPACECRAFT_VELOCITY_VECTOR"][
            :, 0
        ]
        df["RAD_SPACECRAFT_VELOCITY_VECTOR_Y"] = data["RAD_SPACECRAFT_VELOCITY_VECTOR"][
            :, 1
        ]
        df["RAD_SPACECRAFT_VELOCITY_VECTOR_Z"] = data["RAD_SPACECRAFT_VELOCITY_VECTOR"][
            :, 2
        ]

        df["SAR_AVERAGE_BACKSCATTER_WEST"] = data["SAR_AVERAGE_BACKSCATTER"][:, 0]
        df["SAR_AVERAGE_BACKSCATTER_EAST"] = data["SAR_AVERAGE_BACKSCATTER"][:, 1]

        df["SAR_FOOTPRINT_SIZE_WEST"] = data["SAR_FOOTPRINT_SIZE"][:, 0]
        df["SAR_FOOTPRINT_SIZE_EAST"] = data["SAR_FOOTPRINT_SIZE"][:, 1]

        delFields = [
            "RAD_SPACECRAFT_POSITION_VECTOR",
            "RAD_SPACECRAFT_VELOCITY_VECTOR",
            "SAR_FOOTPRINT_SIZE",
            "SAR_AVERAGE_BACKSCATTER",
            "RAD_PARTIALS_GROUP",  # not split yet
            "RAW_RAD_LOAD_POWER",  # not split yet
            "ALT_SKIP_FACTOR",  # not split yet
            "ALT_GAIN_FACTOR",  # not split yet
            "SPARE",  # not split yet
        ]
        lon = data["RAD_FOOTPRINT_LONGITUDE"]
        lat = data["RAD_FOOTPRINT_LATITUDE"]

    # Copy over everything else to dataframe
    for field in data.dtype.names:
        if field not in delFields:
            df[field] = data[field]

    # Filter out bad data (nasty lons)
    mask = lon <= 360
    df = df[mask]
    lon = lon[mask]
    lat = lat[mask]

    # Convert lons from 0-360 to -180 to 180
    lon = (lon + 180) % 360 - 180

    # Make geodataframe
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(lon, lat),
    )

    # Add in orbit number
    gdf["ORBIT"] = os.path.basename(file).replace(".lbl", "").replace(ftype, "")

    return gdf


def main():
    args = cli()
    files = glob.glob(args.dir + "/**/" + args.type + "*.lbl", recursive=True)
    gdfs = []

    print("Reading %s files" % args.type)
    for file in tqdm(files):
        gdfs.append(arcdr2gpkg(file, args.type))

    print("Concatenating GeoDataFrames")
    gdf = pd.concat(gdfs)

    gdf.set_crs(
        'GEOGCS["GCS_Venus_2000",DATUM["D_Venus_2000",SPHEROID["Venus_2000_IAU_IAG",6051800,0,AUTHORITY["ESRI","107902"]],AUTHORITY["ESRI","106902"]],PRIMEM["Reference_Meridian",0,AUTHORITY["ESRI","108900"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["ESRI","104902"]]'
    )

    # Writing geopackage
    print("Writing geopackage")
    gdf.to_file("arcdr.gpkg", layer=args.type, driver="GPKG", mode="w")


if __name__ == "__main__":
    main()
