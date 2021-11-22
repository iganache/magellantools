import numpy as np
import sys
import os


def readRDF(lbl):
    file, hdr = getFileHdr(lbl)
    if(hdr == -1):
        sys.exit("No ^TABLE pointer found in label file %s" % lbl)
    return parseRDF(file, hdr)


def getFileHdr(lbl):
    # Get filename and header length
    hdr = -1
    with open(lbl) as fd:
        for line in fd:
            if "^TABLE" in line:
                hdr = line.split('=')[1].split(',')[1]
                hdr = filter(str.isdigit, hdr)
                hdr = "".join(hdr)
                hdr = int(hdr)
                file = line.split('=')[1].split(',')[0]
                file = file.strip(" (\"")
                break
    return os.path.dirname(lbl) + '/' + file.lower(), hdr


def parseRDF(file, hdr):
    fd = open(file, 'rb')
    rdfhd = fd.read(hdr-1)
    rdfhd = rdfhd.split(b"\r\n")
    header = {}
    for item in rdfhd:
        if(len(item) > 0):
            item = item.split(b'=')
            header[item[0].decode()] = item[1].decode()
    
    # Data types to read from file
    recOrig_t = np.dtype(
        [
            ("SFDU_LABEL_AND_LENGTH", "<S20"),
            ("RAD_NUMBER", "<i4"),
            ("RAD_FLAG_GROUP", "<u4"),
            ("RAD_FLAG2_GROUP", "<u4"),
            ("RAD_SPACECRAFT_EPOCH_TDB_TIME", "<f8"),
            ("RAD_SPACECRAFT_POSITION_VECTOR", "<f8", 3),
            ("RAD_SPACECRAFT_VELOCITY_VECTOR", "<f8", 3),
            ("RAD_FOOTPRINT_LONGITUDE", "<f4"),
            ("RAD_FOOTPRINT_LATITUDE", "<f4"),
            ("RAD_ALONG_TRACK_FOOTPRINT_SIZE", "<f4"),
            ("RAD_CROSS_TRACK_FOOTPRINT_SIZE", "<f4"),
            ("SAR_FOOTPRINT_SIZE", "<f4", 2),
            ("SAR_AVERAGE_BACKSCATTER", "<f4", 2),
            ("INCIDENCE_ANGLE", "<f4"),
            ("BRIGHTNESS_TEMPERATURE", "<f4"),
            ("AVERAGE_PLANETARY_RADIUS", "<f4"),
            ("PLANET_READING_SYSTEM_TEMP", "<f4"),
            ("ASSUMED_WARM_SKY_TEMPERATURE", "<f4"),
            ("RAD_RECEIVER_SYSTEM_TEMP", "<f4"),
            ("SURFACE_EMISSION_TEMPERATURE", "<f4"),
            ("SURFACE_EMISSIVITY", "<f4"),
            ("RAD_PARTIALS_GROUP", "<f4", 18),
            ("RAD_EMISSIVITY_PARTIAL", "<f4"),
            ("SURFACE_TEMPERATURE", "<f4"),
            ("RAW_RAD_ANTENNA_POWER", "<f4"),
            ("RAW_RAD_LOAD_POWER", "<f4"),
            ("ALT_SKIP_FACTOR", "<u1", 2),
            ("ALT_GAIN_FACTOR", "<u1", 2),
            ("ALT_COARSE_RESOLUTION", "<i4"),
            ("SPARE", "V16"),
        ]
    )

    rdf = np.fromfile(fd, dtype=recOrig_t)
    fd.close()

    # Convert vax format numbers to float
    rdf["RAD_SPACECRAFT_EPOCH_TDB_TIME"] = vax2ieee(rdf["RAD_SPACECRAFT_EPOCH_TDB_TIME"])
    rdf["RAD_SPACECRAFT_POSITION_VECTOR"] = vax2ieee(rdf["RAD_SPACECRAFT_POSITION_VECTOR"])
    rdf["RAD_SPACECRAFT_VELOCITY_VECTOR"] = vax2ieee(rdf["RAD_SPACECRAFT_VELOCITY_VECTOR"])
    rdf["RAD_FOOTPRINT_LONGITUDE"] = vax2ieee(rdf["RAD_FOOTPRINT_LONGITUDE"])
    rdf["RAD_FOOTPRINT_LATITUDE"] = vax2ieee(rdf["RAD_FOOTPRINT_LATITUDE"])
    rdf["RAD_ALONG_TRACK_FOOTPRINT_SIZE"] = vax2ieee(rdf["RAD_ALONG_TRACK_FOOTPRINT_SIZE"])
    rdf["RAD_CROSS_TRACK_FOOTPRINT_SIZE"] = vax2ieee(rdf["RAD_CROSS_TRACK_FOOTPRINT_SIZE"])
    rdf["SAR_FOOTPRINT_SIZE"] = vax2ieee(rdf["SAR_FOOTPRINT_SIZE"])
    rdf["SAR_AVERAGE_BACKSCATTER"] = vax2ieee(rdf["SAR_AVERAGE_BACKSCATTER"])
    rdf["INCIDENCE_ANGLE"] = vax2ieee(rdf["INCIDENCE_ANGLE"])
    rdf["BRIGHTNESS_TEMPERATURE"] = vax2ieee(rdf["BRIGHTNESS_TEMPERATURE"])
    rdf["AVERAGE_PLANETARY_RADIUS"] = vax2ieee(rdf["AVERAGE_PLANETARY_RADIUS"])
    rdf["PLANET_READING_SYSTEM_TEMP"] = vax2ieee(rdf["PLANET_READING_SYSTEM_TEMP"])
    rdf["ASSUMED_WARM_SKY_TEMPERATURE"] = vax2ieee(rdf["ASSUMED_WARM_SKY_TEMPERATURE"])
    rdf["RAD_RECEIVER_SYSTEM_TEMP"] = vax2ieee(rdf["RAD_RECEIVER_SYSTEM_TEMP"])
    rdf["SURFACE_EMISSION_TEMPERATURE"] = vax2ieee(rdf["SURFACE_EMISSION_TEMPERATURE"])
    rdf["SURFACE_EMISSIVITY"] = vax2ieee(rdf["SURFACE_EMISSIVITY"])
    rdf["RAD_PARTIALS_GROUP"] = vax2ieee(rdf["RAD_PARTIALS_GROUP"])
    rdf["RAD_EMISSIVITY_PARTIAL"] = vax2ieee(rdf["RAD_EMISSIVITY_PARTIAL"])
    rdf["SURFACE_TEMPERATURE"] = vax2ieee(rdf["SURFACE_TEMPERATURE"])
    rdf["RAW_RAD_ANTENNA_POWER"] = vax2ieee(rdf["RAW_RAD_ANTENNA_POWER"])
    rdf["RAW_RAD_LOAD_POWER"] = vax2ieee(rdf["RAW_RAD_LOAD_POWER"])

    return header, rdf


def vax2ieee(vax):
    # Need to be clever with the bytes here
    # The data is read in as floats to have the right type in the
    # data array (otherwise the output of this function gets truncated)
    # But to do all the bit fiddling the data needs to be unsigned ints
    # So a using tobytes and frombuffer to acheive that
    dtype = vax.dtype
    shape = vax.shape
    buf = vax.tobytes(order='C')

    if(dtype == np.float32):
        vax = np.frombuffer(buf, dtype=np.uint32)
    elif(dtype == np.float64):
        vax = np.frombuffer(buf, dtype=np.uint64)

    vax = vax.reshape(shape)

    if(vax.dtype == np.uint32):  # VAX F
        sgn = (vax & 0x00008000) >> 15  # Get the sign bit
        sgn = sgn.astype(np.int8)

        exp = (vax & 0x00007F80) >> 7  # exponent
        exp = exp.astype(np.int16)
        exp -= 128  # exponent bias

        msa = ((vax & 0x0000007F) << 16) | ((vax & 0xFFFF0000) >> 16)
        msa = msa.astype(np.float32)
        msa /= 2**24
        msa += 0.5  # vax has 0.1m hidden bit vs ieee 1.m hidden bit

        return ((-1.0)**sgn) * (msa) * ((2.0)**exp)

    elif(vax.dtype == np.uint64):  # VAX D
        sgn = (vax & 0x0000000000008000) >> 15  # Get the sign bit
        sgn = sgn.astype(np.int8)

        exp = (vax & 0x0000000000007F80) >> 7  # exponent
        exp = exp.astype(np.int16)
        exp -= 128  # exponent bias

        msa = ((vax & 0x000000000000007F) << 48) | ((vax & 0x00000000FFFF0000) << 16) | \
              ((vax & 0x0000FFFF00000000) >> 32) | ((vax & 0xFFFF000000000000) >> 32)
        msa = msa.astype(np.float64)
        msa /= 2**56
        msa += 0.5  # vax has 0.1m hidden bit vs ieee 1.m hidden bit
        return ((-1.0)**sgn) * (msa) * ((2.0)**exp)