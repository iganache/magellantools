import sys
import os
import glob
from pathlib import Path
import numpy as np
from RDF import readRDF

import geopandas as gpd
from shapely.geometry import LineString



def makeTracks(inpath,outfile):
    
    col_list = ["fpath", "orbit"]
    crs = "+proj=longlat +a=6051800 +b=6051800 +no_defs"
    gdf = makegeoDF(col_list, crs = crs)
    
    geom_list = []
    
    files = glob.glob(inpath + '/**/*.lbl', recursive=True)
    for lblfile in files:
        hdr, rdf = readRDF(lblfile)
        
        rec = {}
        rec[col_list[0]] = str(lblfile)
        rec[col_list[1]] = float(hdr["ORBIT_NUMBER"])
        
        geom_arr = np.transpose(np.array[rdf["RAD_FOOTPRINT_LONGITUDE"], rdf["RAD_FOOTPRINT_LATITUDE"], rdf["AVERAGE_PLANETARY_RADIUS"]])
        geom = [(lon, lat, z) for (lat, lon, z) in geom_arr]
        rec["geometry"] = LineString(geom)
        
        gdf = gdf.append(rec, ignore_index=True)

        gdf.to_file(outfile, driver="GPKG")    
        

def makegeoDF(col_list, crs = None):
    gdf = gpd.GeoDataFrame(
        geometry=[],
        columns=col_list
    )
    
    gdf.crs = crs
    
    return gdf