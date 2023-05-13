import argparse
import glob
import os

import geopandas as gpd
import numpy as np
import pandas as pd
from tqdm import tqdm

from magellantools import ARCDR


def cli():
    parser = argparse.ArgumentParser(
        description="Generate geopackage from Magellan ARCDR files"
    )
    parser.add_argument(
        "out_type",
        type=str,
        help="Output file type",
        choices=["csv", "gpkg"],
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file name (default = mgn.[csv,gpkg])",
        default="mgn"
    )
    parser.add_argument(
        "-l",
        "--layer-name",
        type=str,
        help="Output layer name, for GPKG only (default = mgn)",
        default="mgn"
    )
    parser.add_argument(
        "files",
        type=str,
        nargs="+",
        help="File(s)",
    )
    return parser.parse_args()


def arcdr2gdf(file):
    fname = os.path.basename(file)
    orbitnum = "".join([i for i in fname if i.isdigit()])

    hdr, mask, data = ARCDR.readARCDR(file)

    data = data[mask]

    df = pd.DataFrame()

    # Split up some multi element fields, name the rest (to toss)
    if "adf" in fname:
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

    elif "rdf" in fname:
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

    # Convert lons from 0-360 to -180 to 180
    lon = (lon + 180) % 360 - 180

    # Make geodataframe
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(lon, lat),
    )

    # Add in orbit number
    gdf["ORBIT"] = orbitnum

    return gdf


def main():
    args = cli()
    gdfs = []

    # Add extension to filename if it is not present
    out, ext = os.path.splitext(args.output)

    if(ext is not args.out_type):
        args.output = args.output + "." + args.out_type

    for file in tqdm(args.files):
        gdfs.append(arcdr2gdf(file))

    print("Concatenating GeoDataFrames")
    gdf = pd.concat(gdfs)

    gdf.set_crs(
        'GEOGCS["GCS_Venus_2000",DATUM["D_Venus_2000",SPHEROID["Venus_2000_IAU_IAG",6051800,0,AUTHORITY["ESRI","107902"]],AUTHORITY["ESRI","106902"]],PRIMEM["Reference_Meridian",0,AUTHORITY["ESRI","108900"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["ESRI","104902"]]'
    )

    # Writing geopackage
    if(args.out_type == "gpkg"):
        gdf.to_file(args.output, layer=args.layer_name, driver=args.out_type.upper(), mode="w")
    elif(args.out_type == "csv"):
        df = pd.DataFrame(gdf).drop(columns="geometry")
        df.to_csv(args.output, index=False)
    else:
        print("unhandled output type")

if __name__ == "__main__":
    main()
