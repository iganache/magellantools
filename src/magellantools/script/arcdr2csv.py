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


def getFiles(filepath, suffix = "adf"):
    file = glob.glob(filepath + "/**/" + suffix + "*.lbl", recursive = True)
    return files

def cli():
    parser = argparse.ArgumentParser(description="Input arcdr file names")
    parser.add_argument('--file', dest = 'file', type=str, default="", nargs ='?', help = 'arcdr file name referred to by orbit')
    return parser.parse_args()

def arcdr2csv(filepath, outpath, suffix = "adf"):
    
    files = glob.glob(filepath + "/**/" + suffix + "*.lbl", recursive = True)
    
    for file in files:
    
        fname = file.split("/")[-1].split(".")[0]
        orbitnum = ''.join([i for i in fname if i.isdigit()])

        hdr, data = readARCDR(file)
        npoint = range(len(data))
        subset = data

        rows = []
        for sub in range(len(data)):
            data_row = data[sub]

            if suffix == "rdf":

                flag_val = data_row["RAD_FLAG_GROUP"]
                flags = np.zeros(32) # hold which flags in b are set
                for i in range(32):
                    mask = 2**i # mask
                    flags[i] = (flag_val & mask) >> i

                row_dict = {"orbit": [orbitnum], 
                            "footprint": data_row["RAD_NUMBER"], 
                            "flag": data_row["RAD_FLAG_GROUP"],
                            "xsize": data_row["RAD_ALONG_TRACK_FOOTPRINT_SIZE"],
                            "ysize": data_row["RAD_CROSS_TRACK_FOOTPRINT_SIZE"],
                            "sar_lsize": data_row["SAR_FOOTPRINT_SIZE"][0],
                            "sar_rsize": data_row["SAR_FOOTPRINT_SIZE"][1],
                            "lat": data_row["RAD_FOOTPRINT_LATITUDE"], 
                            "lon": data_row["RAD_FOOTPRINT_LONGITUDE"],
                            "sar_lbsc": data_row["SAR_AVERAGE_BACKSCATTER"][0],
                            "sar_rbsc": data_row["SAR_AVERAGE_BACKSCATTER"][1],
                            "thetai": data_row["INCIDENCE_ANGLE"],
                            "pradius": data_row["AVERAGE_PLANETARY_RADIUS"],
                            "Tb": data_row["BRIGHTNESS_TEMPERATURE"],
                            "Te": data_row["SURFACE_EMISSION_TEMPERATURE"],
                            "Ts": data_row["SURFACE_TEMPERATURE"],
                            "emis": data_row["SURFACE_EMISSIVITY"],
                            "flag_geoc": flags[0],
                            "flag_rdac": flags[1],
                            "flag_nosar1": flags[2],
                            "flag_nosar2": flags[3],
                            "flag_bad": flags[4],
                            "flag_cal": flags[5],
                            "flag_nrad": flags[6],
                            "flag_nrad2": flags[15]} 



            elif suffix == "adf":

                ## search for all the flags set in the flag field #########
                flag_val = data_row["ALT_FLAG_GROUP"]
                flags = np.zeros(32) # hold which flags in b are set
                for i in range(32):
                    mask = 2**i # mask
                    flags[i] = (flag_val & mask) >> i
                    
                    
                    
                ####### compute echo contrast ############################
                mean_ep = np.mean(data_row["NON_RANGE_SHARP_ECHO_PROF"])
                std_ep = np.std(data_row["NON_RANGE_SHARP_ECHO_PROF"])
                try:
                    Ce = std_ep/mean_ep
                except:
                    Ce = np.nan
                mean_rs_ep = np.mean(data_row["RANGE_SHARP_ECHO_PROFILE"])
                std_rs_ep = np.std(data_row["RANGE_SHARP_ECHO_PROFILE"])
                try:
                    Ce_rs = std_rs_ep/mean_rs_ep
                except:
                    Ce_rs = np.nan
                ############################################################
                

                row_dict = {"orbit": orbitnum, 
                            "footprint": data_row["FOOTPRINT_NUMBER"], 
                            "flag": data_row["ALT_FLAG_GROUP"],
                            "xsize": data_row["ALT_ALONG_TRACK_FOOTPRINT_SIZE"],
                            "ysize": data_row["ALT_CROSS_TRACK_FOOTPRINT_SIZE"],
                            "lat": data_row["ALT_FOOTPRINT_LATITUDE"], 
                            "lon": data_row["ALT_FOOTPRINT_LONGITUDE"], 
                            "pradius": data_row["DERIVED_PLANETARY_RADIUS"],
                            "rms_slope": data_row["RADAR_DERIVED_SURF_ROUGHNESS"],
                            "ref": data_row["DERIVED_FRESNEL_REFLECTIVITY"],
                            "ref_corr": data_row["DERIVED_FRESNEL_REFLECT_CORR"],
                            "multi_peak_corr": data_row["MULT_PEAK_FRESNEL_REFLECT_CORR"],
                            "mean_echo_profile": mean_ep,
                            "std_echo_profile": std_ep,
                            "Ce": Ce,
                            "mean_rs_echo_profile": mean_rs_ep,
                            "std_rs_echo_profile": std_rs_ep,
                            "Ce_rs": Ce_rs,
                            "flag_fit": flags[0],
                            "flag_ephc": flags[1],
                            "flag_rhoc": flags[2],
                            "flag_rs2": flags[3],
                            "flag_nrs2": flags[4],
                            "flag_bad": flags[5],
                            "flag_rbad": flags[6],
                            "flag_cbad": flags[7],
                            "flag_tmark": flags[8],
                            "flag_cmark": flags[9],
                            "flag_fmark": flags[10],
                            "flag_hagfors": flags[11],
                            "flag_badalta": flags[12],
                            "flag_slopebad": flags[13],
                            "flag_rhobad": flags[14],
                            "flag_rad2": flags[15],
                            "flag_rad2bad": flags[16],
                            "flag_ambig": flags[17],
                            "flag_ambig2": flags[18]}


            rows.append(row_dict)

        df = pd.DataFrame(rows)
        df.to_csv(outpath+"/"+fname+".csv", index=False)
        
        
def main (): 
    # args = cli()
    # file = args.file
    # arcdrpath =  "/center1/PLANETDAT/iganesh/mgn-v-rdrs-5-cdr-alt-rad-v1"
    # arcdrpath = "./"
    
    filepath = "/home/iganesh/mgn-v-rdrs-5-cdr-alt-rad-v1"
    outpath = "/home/iganesh/mgn-v-rdrs-5-cdr-alt-rad-v1/altimetry_csv_echoprof"
    arcdr2csv(filepath, outpath, "adf")

    
if __name__ == '__main__':
    main()   
