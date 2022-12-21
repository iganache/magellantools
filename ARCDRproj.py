# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19, 2022
Projects ARCDR data into equirectangular Venus projection
Currently only deals with a csv file of ARCDR data.
Need to add this into a functionality while reading in
ARCDR stuff in the PDS format.

@author: Indujaa
"""

import glob
import argparse
import numpy as np
import pandas as pd
from ARCDR import readARCDR
from pyproj import CRS
from pyproj import Transformer


def project(in_csv, out_csv):
    
    df = pd.read_csv(in_csv)
    lon = df["lon"].to_numpy()
    lat = df["lat"].to_numpy()
    
    geo_crs = CRS.from_proj4("+proj=longlat +a=6051800 +b=6051800 +no_defs ")
    proj_crs = CRS.from_proj4("+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +a=6051800 +b=6051800 +units=m +no_defs")
    proj = Transformer.from_crs(geo_crs, proj_crs)
    
    arr = np.zeros((len(lat), 2)).astype(np.float32)
    
    for i in range(len(lat)):
        arr[i, :] = proj.transform(lon[i], lat[i])
        
    df["Xval"] = arr[:,0] 
    df["Yval"] = arr[:,1] 
    
    df.to_csv(out_csv, index=False)
    
    
def main (): 
#     args = cli()
#     file = args.file
    #arcdrpath =  "/center1/PLANETDAT/iganesh/mgn-v-rdrs-5-cdr-alt-rad-v1"
    project("/home/iganesh/magellantools/ARCDR_alt_tess_rhocorr_int_cyc1_DN.csv", "/home/iganesh/magellantools/ARCDR_alt_tess_rhocorr_int_cyc1_DN_proj.csv")


    
if __name__ == '__main__':
    main()   
