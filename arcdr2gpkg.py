# -*- coding: utf-8 -*-
"""
Created on Mon Nov 14, 2022
Script for reading in arcdr files and writing 
all the info into a csv in parallel. 

Command for creating a file with all the lbl
files needed:
[find $PWD -type f -name "adf*.lbl" >> filelist]
[find $PWD -type f -name "rdf*.lbl" >> filelist]

@author: Indujaa
"""

import glob
import argparse
import numpy as np
import pandas as pd
from ARCDR import readARCDR
import geopandas as gpd
import pandas as pd
import os
from tqdm import tqdm


def cli():
    parser = argparse.ArgumentParser(description="Generate geopackage from Magellan ARCDR files")
    parser.add_argument(
        "dir", type=str, help="Magellan data directory",
    )
    parser.add_argument(
        "type", type=str, help="File type", choices=["adf", "rdf"],
    )
    return parser.parse_args()


def arcdr2gpkg(file, ftype):
    fname = file.split("/")[-1].split(".")[0]
    orbitnum = "".join([i for i in fname if i.isdigit()])

    hdr, data = readARCDR(file)

    # Delete multi-element data
    # TODO: figure out how to add these. Some can be split up to X, Y, Z etc.
    if(ftype == "adf"):
        delFields = [
            "ALT_SPACECRAFT_POSITION_VECTOR",
            "ALT_SPACECRAFT_VELOCITY_VECTOR",
            "FORMAL_ERRORS_GROUP",
            "FORMAL_CORRELATIONS_GROUP",
            "ALT_PARTIALS_GROUP",
            "NON_RANGE_SHARP_ECHO_PROF",
            "BEST_NON_RANGE_SHARP_MODEL_TPT",
            "RANGE_SHARP_ECHO_PROFILE",
            "BEST_RANGE_SHARP_MODEL_TMPLT",
            "SPARE",
        ]
    elif(ftype == "rdf"):
        delFields = [
            "RAD_SPACECRAFT_POSITION_VECTOR",
            "RAD_SPACECRAFT_VELOCITY_VECTOR",
            "SAR_FOOTPRINT_SIZE",
            "SAR_AVERAGE_BACKSCATTER",
            "RAD_PARTIALS_GROUP",
            "RAW_RAD_LOAD_POWER",
            "ALT_SKIP_FACTOR",
            "ALT_GAIN_FACTOR",
            "SPARE"
        ]

    fields = list(data.dtype.names)
    for delField in delFields:
        fields.remove(delField)
    data = data[fields]

    df = pd.DataFrame()
    for name in data.dtype.names:
        df[name] = data[name]

    if(ftype == "adf"):
        # Filter out bad data
        df = df[df.ALT_FOOTPRINT_LONGITUDE <= 360]
        # Convert lons from 0-360 to -180 to 180
        df.ALT_FOOTPRINT_LONGITUDE = (df.ALT_FOOTPRINT_LONGITUDE + 180) % 360 - 180

        # Make geodataframe
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(
                df.ALT_FOOTPRINT_LONGITUDE, df.ALT_FOOTPRINT_LATITUDE
            ),
        )
    elif(ftype == "rdf"):
        # Filter out bad data
        df = df[df.RAD_FOOTPRINT_LONGITUDE <= 360]
        # Convert lons from 0-360 to -180 to 180
        df.RAD_FOOTPRINT_LONGITUDE = (df.RAD_FOOTPRINT_LONGITUDE + 180) % 360 - 180

        # Make geodataframe
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(
                df.RAD_FOOTPRINT_LONGITUDE, df.RAD_FOOTPRINT_LATITUDE
            ),
        )



    gdf["ORBIT"] = os.path.basename(file).replace(".lbl", "").replace(ftype, "")

    return gdf


def main():
    args = cli()
    files = glob.glob(args.dir + "/**/" + args.type + "*.lbl", recursive=True)
    gdfs = []

    for file in tqdm(files):
        gdfs.append(arcdr2gpkg(file, args.type))

    gdf = pd.concat(gdfs)

    gdf.set_crs(
        'GEOGCS["GCS_Venus_2000",DATUM["D_Venus_2000",SPHEROID["Venus_2000_IAU_IAG",6051800,0,AUTHORITY["ESRI","107902"]],AUTHORITY["ESRI","106902"]],PRIMEM["Reference_Meridian",0,AUTHORITY["ESRI","108900"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["ESRI","104902"]]'
    )

    gdf.to_file("arcdr.gpkg", layer=args.type, driver="GPKG", mode="w")


if __name__ == "__main__":
    main()