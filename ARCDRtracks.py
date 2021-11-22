import sys
import os
import glob
from pathlib import Path
import numpy as np
from RDF import readRDF
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

def main():
    makeTracks("../mgn-v-rdrs-5-cdr-alt-rad-v1/", "mgn-v-rdrs-5-cdr-alt-rad-v1.gpkg")
    
def makeTracks(inpath,outfile):
    
    col_list = ["fpath", "orbit"]
    crs = "+proj=longlat +a=6051800 +b=6051800 +no_defs"
    #gdf = makegeoDF(col_list, crs = crs)
    
    geom_list = []
    
    files = glob.glob(inpath + '/**/*.lbl', recursive=True)
    i = 0
    recs = []
    for lblfile in files:
        hdr, rdf = readRDF(lblfile)

        gdf = gpd.GeoDataFrame(
        geometry=[],
        columns=col_list
        )
        rec = {}
        rec[col_list[0]] = os.path.basename(lblfile)
        rec[col_list[1]] = float(hdr["ORBIT_NUMBER"])

        geom_arr = np.transpose(np.stack((rdf["RAD_FOOTPRINT_LONGITUDE"], rdf["RAD_FOOTPRINT_LATITUDE"], rdf["AVERAGE_PLANETARY_RADIUS"])))
        # get rid of no data rows
        geom_arr = geom_arr[np.abs(geom_arr[:,0]) < 1e4 ,:]
        
        # Separate lines that cross -180/180
        geom_1 = geom_arr[geom_arr[:,0] < 180, :]
        geom_2 = geom_arr[geom_arr[:,0] > 180, :]
        geom_2[:, 0] = geom_2[:, 0]-360 # Make -180 to 180

        for geom in [geom_1, geom_2]:
            if(len(geom) > 20):
                geom = [(lon, lat, z) for (lon, lat, z) in geom]
                geom = geom[::10] # Downsample points by 10x
                rec["geometry"] = LineString(geom)
                recs.append(pd.DataFrame([rec]))

    df = pd.concat(recs)
    gdf = gpd.GeoDataFrame(df, columns=col_list, geometry=df.geometry)
    gdf.crs = crs
    gdf.to_file(outfile, driver="GPKG")    
        

def makegeoDF(col_list, crs = None):
    gdf = gpd.GeoDataFrame(
        geometry=[],
        columns=col_list
    )
    
    gdf.crs = crs
    
    return gdf

main()