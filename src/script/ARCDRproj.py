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
from osgeo import gdal
import rasterio
import rasterio.mask


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
    print(len(arr[:,0] ), len(arr[:,0] ))
    
    diff_arr = np.gradient(arr, axis = 0)
    theta = np.arctan(diff_arr[:,1]/diff_arr[:,0])
    print(len(theta))
    df["orbit_inc"] = np.rad2deg(theta)
    
    df.to_csv(out_csv, index=False)
    return df

def crop_footprints(df):
    df["DN_mean"] = np.zeros((len(df))).astype(np.float32)
    df["DN_npix"] = np.zeros((len(df)))
    for i in range(len(df)):
        rec = df.iloc[i]
        x0 = rec["Xval"]
        y0 = rec["Yval"]
        a = rec["ysize"]*1000/2
        b = rec["xsize"]*1000/2
        
        ymin = y0 - 2*a
        ymax = y0 +2*a
        xmin = x0 - 2*a
        xmax = x0 + 2*a
                
        A = np.deg2rad(90.0+rec["orbit_inc"])
        infile = "/home/iganesh/Venus_Magellan_LeftLook_mosaic_global_225m.tif"
        inds = rasterio.open(infile)
        img = inds.read(1, window=rasterio.windows.from_bounds(xmin, ymin, xmax, ymax, inds.transform)).astype(np.float32)
        img[img>255] = np.nan
        img[img<0] = np.nan
        
        height = img.shape[0]
        width = img.shape[1]
        cols, rows = np.meshgrid(np.arange(width), np.arange(height))
        xs, ys = rasterio.transform.xy(inds.transform, rows, cols)
        
        ellipse = (((xs-x0)*np.cos(A) + (ys-y0)*np.sin(A))**2 / a**2) + (((xs-x0)*np.sin(A) - (ys-y0)*np.cos(A))**2 / b**2)
        in_ellipse = img[ellipse<=1.0]
        mean = np.nanmean(in_ellipse)
        num_pix = np.count_nonzero(~np.isnan(img))
        print(np.count_nonzero(ellipse<=1.0))
        rec["DN_mean"] = mean
        rec["DN_npix"] = num_pix
        
    df.to_csv("/home/iganesh/Arecibo/ARCDR_alt_tess_int_rhocorr_cyc1_DN_test.csv", index=False)   
    
    
def main (): 
#     args = cli()
#     file = args.file
    #arcdrpath =  "/center1/PLANETDAT/iganesh/mgn-v-rdrs-5-cdr-alt-rad-v1"
    # proj_df = project("/home/iganesh/Arecibo/ARCDR_alt.csv", "/home/iganesh/Arecibo/ARCDR_alt_equirect.csv")
    
    proj_df = pd.read_csv("/home/iganesh/Arecibo/ARCDR_alt_tess_int_rhocorr.csv")
    crop_footprints(proj_df)

    
if __name__ == '__main__':
    main()   
