import numpy as np
import sys
import os

def readALTEDR(lbl):
    """Wrapper function for reading ADF or RDF files

    :param lbl: PDS label file for ADF or RDF file
    :type lbl: string

    :return: Tuple with dict containing header information and structured array containing ADF or RDF file data
    :rtype: (dict, np.ndarray)
    """