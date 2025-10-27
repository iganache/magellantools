import argparse
import glob
import os
import textwrap

import geopandas as gpd
import numpy as np
import pandas as pd
from tqdm import tqdm
import pds4_tools

from magellantools import ARCDR

# Command line utility to convert ADF and RDF files to CSV or GPKG

# TODO: Rewrite file output to a more streaming-type style. No real need to make big
# geodataframe before writing out I think.


def cli():
    desc = """
    arcdr2table translates data from ADF and RDF files in the Magellan ARCDR
    dataset to comma separated value (CSV) or geopackage (GPKG) format.
    """

    epi = """
    Not all fields are currently translated, the output files will be missing
    the following fields:
    adf -
            FORMAL_ERRORS_GROUP
            FORMAL_CORRELATIONS_GROUP
            ALT_PARTIALS_GROUP
            NON_RANGE_SHARP_ECHO_PROF (mean and std dev are output)
            BEST_NON_RANGE_SHARP_MODEL_TPT
            RANGE_SHARP_ECHO_PROFILE
            BEST_RANGE_SHARP_MODEL_TMPLT
    rdf -
            RAD_PARTIALS_GROUP
            RAW_RAD_LOAD_POWER
            ALT_SKIP_FACTOR
            ALT_GAIN_FACTOR

    ARCDR landing page:
    https://pds-geosciences.wustl.edu/missions/magellan/arcdr/index.htm
    """
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(desc),
        epilog=textwrap.dedent(epi),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", help="Verbose output", action="store_true")
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        help="Output file type",
        choices=["csv", "gpkg"],
        default="csv",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file name (default = mgn.[csv,gpkg])",
        default="mgn",
    )
    parser.add_argument(
        "-l",
        "--layer-name",
        type=str,
        help="Output layer name, for GPKG only (default = mgn)",
        default="mgn",
    )
    parser.add_argument(
        "files",
        type=str,
        nargs="+",
        help="Label file(s) of ADF/RDF file(s) to convert. Must be in same directory as ADF/RDF file.",
    )
    return parser.parse_args()


def arcdr2gdf_pds4(file, args):
    structures = pds4_tools.read(file, quiet=(not args.v))
    tabledict = {"adf": "Altimetry_File", "rdf": "Radiometry_File"}
    fname = os.path.basename(file)
    orbitnum = "".join([i for i in fname.split("_")[0] if i.isdigit()])

    type = None
    for k in tabledict.keys():
        if k in file.lower():
            type = k
            break

    if type is None:
        print("Unknown file type")
        return 1

    table = structures[tabledict[type]]
    df = pd.DataFrame()

    if type == "adf":
        delFields = [
            "GROUP_0, Spacecraft_Position_Vector",
            "GROUP_1, Spacecraft_Velocity_Vector",
            "GROUP_2, Formal_Errors",  # not split yet
            "GROUP_3, Formal_Correlations",  # not split yet
            "GROUP_4, Partials_Group",  # not split yet
            "GROUP_5, Non_Range_Sharp_Echo_Prof",  # not split yet but have taken mean and stdev
            "GROUP_6, Best_Non_Range_Sharp_Model_TPT",  # not split yet
            "GROUP_7, Range_Sharp_Echo_Profile",  # not split yet
            "GROUP_8, Best_Range_Sharp_Model_Tmplt",  # not split yet
            "GROUP_9, Spare",  # not split yet
        ]

        df["Non_Range_Sharp_Echo_Prof_Mean"] = np.mean(
            table["GROUP_5, Non_Range_Sharp_Echo_Prof"]
        )
        df["Non_Range_Sharp_Echo_Pro_Stdev"] = np.std(
            table["GROUP_5, Non_Range_Sharp_Echo_Prof"]
        )

        lon = table["Footprint_Longitude"]
        lat = table["Footprint_Latitude"]

    elif type == "rdf":
        # where did "SP_POSITION_VECTOR" go?
        delFields = [
            "GROUP_0, Spacecraft_Position_Vector",
            "GROUP_1, Spacecraft_Velocity_Vector",
            "GROUP_2, SAR_Footprint_Size",
            "GROUP_3, SAR_Average_Backscatter",
            "GROUP_4, Partials",
            "Raw_Rad_Load_Power",
            "GROUP_5, Alt_Skip_Factor",
            "GROUP_6, Alt_Gain_Factor",
            "GROUP_7, Spare",
        ]
        lon = table["Footprint_Longitude"]
        lat = table["Footprint_Latitude"]

    # Copy over to dataframe
    for field in table.data.dtype.names:
        if field not in delFields:
            df[field] = table[field]

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


def arcdr2gdf_pds3(file):
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

    # Add extension to output filename if it is not present
    _, ext = os.path.splitext(args.output)
    ext = ext[1:]  # strip .

    if ext != args.type:
        args.output = args.output + "." + args.type

    _, ext = os.path.splitext(args.files[0])
    if ext.lower() == ".xml":
        pdsmode = 4
    elif ext.lower() == ".lbl":
        pdsmode = 3
    else:
        print("Unknown label file type")
        return 1

    if pdsmode == 3:
        for file in tqdm(args.files, desc="Loading data files", disable=(not args.v)):
            gdfs.append(arcdr2gdf_pds3(file))
    elif pdsmode == 4:
        for file in tqdm(args.files, desc="Loading data files", disable=(not args.v)):
            gdfs.append(arcdr2gdf_pds4(file, args))

    if args.v:
        print("Concatenating GeoDataFrames.")

    gdf = pd.concat(gdfs)

    gdf.set_crs(
        'GEOGCS["GCS_Venus_2000",DATUM["D_Venus_2000",SPHEROID["Venus_2000_IAU_IAG",6051800,0,AUTHORITY["ESRI","107902"]],AUTHORITY["ESRI","106902"]],PRIMEM["Reference_Meridian",0,AUTHORITY["ESRI","108900"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["ESRI","104902"]]'
    )

    # Writing geopackage
    if args.type == "gpkg":
        if args.v:
            print("Writing gpkg.")
        gdf.to_file(
            args.output, layer=args.layer_name, driver=args.type.upper(), mode="w"
        )
    elif args.type == "csv":
        if args.v:
            print("Writing csv.")
        df = pd.DataFrame(gdf).drop(columns="geometry")
        df.to_csv(args.output, index=False)
    else:
        print("unhandled output type")


if __name__ == "__main__":
    main()
