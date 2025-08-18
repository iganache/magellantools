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
    # Enforce that input file is lbl
    if(lbl.split(".")[-1].casefold() != "lbl"):
        sys.exit("Invalid input file %s\nInput file must be lbl" % lbl)

    file, hdr = getEDRFileHdr(lbl)

    if hdr == -1:
        sys.exit("No ^TABLE pointer found in label file %s" % lbl)

    lblname = os.path.basename(file)

    if lblname[0:3].casefold() == "alt":
        return parseALT(file, hdr)
    if lblname[0:3].casefold() == "sab":
        return parseSAB(file, hdr)
    else:
        sys.exit("No parser match found for file %s" % lbl)


def getEDRFileHdr(lbl):
    """Determine length of header and path to the ALT-EDR file

    :param lbl: ALT.LBL PDS label file 
    :type lbl: string

    :return: Tuple containing path to ALT.DAT file and length of file header
    :rtype: (string, int)
    """
    hdr = -1
    with open(lbl) as fd:
        for line in fd:
            if "^TABLE " in line:
                hdr = line.split("=")[1].split(",")[1]
                hdr = filter(str.isdigit, hdr)
                hdr = "".join(hdr)
                hdr = int(hdr)
                file = line.split("=")[1].split(",")[0]
                file = file.strip(' (\'')
                break

    return os.path.dirname(lbl) + "/" + file.upper(), hdr



def parseALT(file, hdr):
    """Parse ALT.DAT file.

    :param file: Path to ALT data file
    :type file: string

    :param hdr: Length of ALT data file header in bytes
    :type hdr: int

    :return: Tuple with dict containing header information, nodata mask, and structured array containing ALT file data
    :rtype: (dict, np.ndarray, np.ndarray)
    """


    # file, hdr = getEDRFileHdr(lbl)
    fd = open(file, "rb")
    edrhd = fd.read(hdr - 1)
    edrhd = edrhd.split(b"\r\n")
    header = {}
    for item in edrhd:
        if len(item) > 0:
            item = item.split(b"=")
            header[item[0].decode()] = item[1].decode()


    # Data types to read from file
    sct = np.dtype(
        [
            ("SC_RIM", ">u1", 3),
            ("SC_MOD91", "u1"),
            ("SC_MOD10", "u1"),
            ("SC_MOD8", "u1")
        ]
    )

    sclk = np.dtype(
        [
            ("DAYS", ">u2"),
            ("MILLISEC", "u2", 2)
        ]
    )
    
    
    recOrig_t = np.dtype(
            [
                ("DATA_ID_LABEL", "<S12"),
                ("DATA_LENGTH", "<S8"),
                ("SUBHDR_AGG_CHDO", ">i2", 2),
                ("T1_CHDO", ">i2", 2),
                ("T1_MAJOR", ">u1"),
                ("T1_MINOR", ">u1"),
                ("T1_MISSION_ID", ">u1"),
                ("T1_FORMAT", ">u1"),
                ("T2_CHDO", ">i2", 2),
                ("T2_ORGN", ">u1"),
                ("T2_LAST_MDFR", ">u1"),
                ("T2_SCFT_ID", ">u1"),
                ("T2_DATA_SRC", ">u1"),
                ("T2_MODE", ">u2"),
                ("T2_ERT", sct),
                ("T2_SPARE1", ">i1"),
                ("T2_EXTRCT_LVL", ">u1"),
                ("T2_DSN_REC_SEQ", ">u2", 2),
                ("T2_BET", ">u1"),
                ("T2_FLY", ">u1"),
                ("T2_REED_SLMN", ">u1"),
                ("T2_GOLAY", ">u1"),
                ("T2_FLAG", ">u1"),
                ("T2_PIN_ERR", ">u1"),
                ("T2_PARNT_FRAME", ">u1", 4),
                ("T2_SPARE2", ">u1"),
                ("T2_FREQ_BAND", ">u1"),
                ("T2_BIT_RATE", ">u2", 2),
                ("T2_DEST", ">u1"),
                ("T2_GDD", ">u1"),
                ("T2_SNT", ">u1", 4),
                ("T2_SSNR", ">u1", 4),
                ("T2_SIG_LVL", ">u1", 4),
                ("T2_ANT", ">u1"),
                ("T2_RX", ">u1"),
                ("T2_MASTER_ANT", ">u1"),
                ("T2_MASTER_RX", ">u1"),
                ("T2_DTM_GRP", ">u1"),
                ("T2_TLM_CHNL", ">u1"),
                ("T2_T2_LOCK", ">u2"),
                ("T2_VERSION", ">u1"),
                ("T2_BUILD", ">u1"),
                ("T2_ORG_SRC", ">u1"),
                ("T2_CURR_SRC", ">u1"),
                ("T2_RCT", sct),
                ("T2_ANOM", ">u2"),
                ("T2_LOCK_COUNT", ">i2"),
                ("T2_LRN", ">i2"),
                ("T2_PUB", ">i1", 6),
                ("T2_SPARE3", ">i1", 2),
                ("T3_CHDO", ">i2", 2),
                ("T3_CORR", ">u2"),
                ("T3_FID", ">u1"),
                ("T3_EXTR_LVL", ">u1"),
                ("T3_ID", ">u2"),
                ("T3_SCLK", sclk),
                ("T3_SCT", sct),
                ("T3_ORBIT_NUM", ">i2"),
                ("CHDO2",  ">i2", 2),
                ("AL_VECTOR_SIZE", ">i2"),
                ("AL_FILLER_BYTES", ">u1", 4),
                ("AL_EXTRACT_COUNT", ">i2"),
                ("AL_GOLAY_ERROR_COUNT", ">i2"),
                ("AL_RCD_COUNT", ">u1"),
                ("AL_RCD_MISSING", ">u1"),
                ("AL_SAB_BET", ">u1"),
                ("AL_SAB_PN_ERROR", ">u1"),
                ("AL_LAST_SRC", ">u1"),
                ("AL_FLAGS", ">u1"),
                ("DATA_CHDO", ">i2", 2),
                ("SB_SYNC",  ">u2", 2),
                ("SB_THRESH",  ">u2", 12),
                ("SB_SPARE1", ">u2"),
                ("SB_RAD",  ">u2"),
                ("SB_RCLK",  ">u2", 4),
                ("SB_SPARE2", ">u2"),
                ("SB_SAB_B",  ">u2", 5),
                ("SB_BMC_FLAG",  ">u2"),
                ("ALT_FRAME", "<u1", 2266),
            ])
    data = np.fromfile(fd, dtype=recOrig_t)
    fd.close()

    mask = None
    return header, mask, data



def parseSAB(file, hdr):
    """Parse SAB.DAT file.

    :param file: Path to SAB data file
    :type file: string

    :param hdr: Length of SAB data file header in bytes
    :type hdr: int

    :return: Tuple with dict containing header information, nodata mask, and structured array containing SAB file data
    :rtype: (dict, np.ndarray, np.ndarray)
    """


    # file, hdr = getEDRFileHdr(lbl)
    fd = open(file, "rb")
    edrhd = fd.read(hdr - 1)
    edrhd = edrhd.split(b"\r\n")
    header = {}
    for item in edrhd:
        if len(item) > 0:
            item = item.split(b"=")
            header[item[0].decode()] = item[1].decode()


    # Data types to read from file
    sct = np.dtype(
        [
            ("SC_RIM", ">u1", 3),
            ("SC_MOD91", "u1"),
            ("SC_MOD10", "u1"),
            ("SC_MOD8", "u1")
        ]
    )

    sclk = np.dtype(
        [
            ("DAYS", ">u2"),
            ("MILLISEC", "u2", 2)
        ]
    )
    
    
    recOrig_t = np.dtype(
            [
                ("DATA_ID_LABEL", "<S12"),
                ("DATA_LENGTH", "<S8"),
                ("SUBHDR_AGG_CHDO", ">i2", 2),
                ("T1_CHDO", ">i2", 2),
                ("T1_MAJOR", ">u1"),
                ("T1_MINOR", ">u1"),
                ("T1_MISSION_ID", ">u1"),
                ("T1_FORMAT", ">u1"),
                ("T2_CHDO", ">i2", 2),
                ("T2_ORGN", ">u1"),
                ("T2_LAST_MDFR", ">u1"),
                ("T2_SCFT_ID", ">u1"),
                ("T2_DATA_SRC", ">u1"),
                ("T2_MODE", ">u2"),
                ("T2_ERT", sct),
                ("T2_SPARE1", ">i1"),
                ("T2_EXTRCT_LVL", ">u1"),
                ("T2_DSN_REC_SEQ", ">u2", 2),
                ("T2_BET", ">u1"),
                ("T2_FLY", ">u1"),
                ("T2_REED_SLMN", ">u1"),
                ("T2_GOLAY", ">u1"),
                ("T2_FLAG", ">u1"),
                ("T2_PIN_ERR", ">u1"),
                ("T2_PARNT_FRAME", ">u1", 4),
                ("T2_SPARE2", ">u1"),
                ("T2_FREQ_BAND", ">u1"),
                ("T2_BIT_RATE", ">u2", 2),
                ("T2_DEST", ">u1"),
                ("T2_GDD", ">u1"),
                ("T2_SNT", ">u1", 4),
                ("T2_SSNR", ">u1", 4),
                ("T2_SIG_LVL", ">u1", 4),
                ("T2_ANT", ">u1"),
                ("T2_RX", ">u1"),
                ("T2_MASTER_ANT", ">u1"),
                ("T2_MASTER_RX", ">u1"),
                ("T2_DTM_GRP", ">u1"),
                ("T2_TLM_CHNL", ">u1"),
                ("T2_T2_LOCK", ">u2"),
                ("T2_VERSION", ">u1"),
                ("T2_BUILD", ">u1"),
                ("T2_ORG_SRC", ">u1"),
                ("T2_CURR_SRC", ">u1"),
                ("T2_RCT", sct),
                ("T2_ANOM", ">u2"),
                ("T2_LOCK_COUNT", ">i2"),
                ("T2_LRN", ">i2"),
                ("T2_PUB", ">i1", 6),
                ("T2_SPARE3", ">i1", 2),
                ("T3_CHDO", ">i2", 2),
                ("T3_CORR", ">u2"),
                ("T3_FID", ">u1"),
                ("T3_EXTR_LVL", ">u1"),
                ("T3_ID", ">u2"),
                ("T3_SCLK", sclk),
                ("T3_SCT", sct),
                ("T3_ORBIT_NUM", ">i2"),
                ("CHDO2",  ">i2", 2),
                ("SA_VECTOR_SIZE", ">i2"),
                ("SA_FILLER_BYTES", ">u1", 117),
                ("SA_SPARE", ">u1"),
                ("SA_SAB_LENGTH", ">u2", 2),
                ("SA_EXTRACT_COUNT", ">i2"),
                ("SA_GOLAY_ERROR_COUNT", ">i2"),
                ("SA_RCD_COUNT", ">u1"),
                ("SA_RCD_MISSING", ">u1"),
                ("SA_SAB_BET", ">u1"),
                ("SA_SAB_PN_ERROR", ">u1"),
                ("SA_LAST_SOURCE", ">u1"),
                ("SA_FLAGS", ">u1"),
                ("SA_TOTAL_PARTS", ">u1"),
                ("SA_PART_NUMBER", ">u1"),
                ("SA_CHDO", ">i2", 2),
                ("SB_SYNC",  ">u2", 2),
                ("SB_THRESH",  ">u2", 12),
                ("SB_SPARE1", ">u2"),
                ("SB_RAD",  ">u2"),
                ("SB_RCLK",  ">u2", 4),
                ("SB_SPARE2", ">u2"),
                ("SB_SAB_B",  ">u2", 5),
                ("SB_BMC_FLAG",  ">u2")
            ])
    data = np.fromfile(fd, dtype=recOrig_t)
    fd.close()

    mask = None
    return header, mask, data