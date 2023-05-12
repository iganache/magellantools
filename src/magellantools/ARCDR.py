import numpy as np
import sys
import os


def readARCDR(lbl):
    """Wrapper function for reading ADF or RDF files

    :param lbl: PDS label file for ADF or RDF file
    :type lbl: string

    :return: Tuple with dict containing header information and structured array containing ADF or RDF file data
    :rtype: (dict, np.ndarray)
    """
    file, hdr = getFileHdr(lbl)

    if hdr == -1:
        sys.exit("No ^TABLE pointer found in label file %s" % lbl)

    lblname = os.path.basename(file)

    if lblname[0:3].lower() == "rdf":
        # print("parsing rdf")
        return parseRDF(file, hdr)
    if lblname[0:3].lower() == "adf":
        # print("parsing adf")
        return parseADF(file, hdr)
    else:
        sys.exit("No parser match found")


def getFileHdr(lbl):
    """Determine length of header and path to ADF or RDF file

    :param lbl: PDS label file for ADF or RDF file
    :type lbl: string

    :return: Tuple containing path to ADF or RDF file and length of file header
    :rtype: (string, int)
    """
    hdr = -1
    with open(lbl) as fd:
        for line in fd:
            if "^TABLE" in line:
                hdr = line.split("=")[1].split(",")[1]
                hdr = filter(str.isdigit, hdr)
                hdr = "".join(hdr)
                hdr = int(hdr)
                file = line.split("=")[1].split(",")[0]
                file = file.strip(' ("')
                break

    return os.path.dirname(lbl) + "/" + file.lower(), hdr


def parseADF(file, hdr):
    """Parse ADF data file.

    :param file: Path to ADF data file
    :type file: string

    :param hdr: Length of ADF data file header in bytes
    :type hdr: int

    :return: Tuple with dict containing header information and structured array containing ADF file data
    :rtype: (dict, np.ndarray)
    """
    fd = open(file, "rb")
    adfhd = fd.read(hdr - 1)
    adfhd = adfhd.split(b"\r\n")
    header = {}
    for item in adfhd:
        if len(item) > 0:
            item = item.split(b"=")
            header[item[0].decode()] = item[1].decode()

    recOrig_t = np.dtype(
        [
            ("SFDU_LABEL_AND_LENGTH", "<S20"),
            ("FOOTPRINT_NUMBER", "<i4"),
            ("ALT_FLAG_GROUP", "<u4"),
            ("ALT_FLAG2_GROUP", "<u4"),
            ("ALTIMETRY_FOOTPRINT_TDB_TIME", "<f8"),
            ("ALT_SPACECRAFT_POSITION_VECTOR", "<f8", 3),
            ("ALT_SPACECRAFT_VELOCITY_VECTOR", "<f8", 3),
            ("ALT_FOOTPRINT_LONGITUDE", "<f4"),
            ("ALT_FOOTPRINT_LATITUDE", "<f4"),
            ("ALT_ALONG_TRACK_FOOTPRINT_SIZE", "<f4"),
            ("ALT_CROSS_TRACK_FOOTPRINT_SIZE", "<f4"),
            ("RECEIVER_NOISE_CALIBRATION", "<f4"),
            ("UNCORRECTED_DISTANCE_TO_NADIR", "<f4"),
            ("ATMOS_CORRECTION_TO_DISTANCE", "<f4"),
            ("DERIVED_PLANETARY_RADIUS", "<f4"),
            ("RADAR_DERIVED_SURF_ROUGHNESS", "<f4"),
            ("DERIVED_FRESNEL_REFLECTIVITY", "<f4"),
            ("DERIVED_FRESNEL_REFLECT_CORR", "<f4"),
            ("FORMAL_ERRORS_GROUP", "<f4", 3),
            ("FORMAL_CORRELATIONS_GROUP", "<f4", 6),
            ("EPHEMERIS_RADIUS_CORRECTION", "<f4"),
            ("EPHEMERIS_LONGITUDE_CORRECTION", "<f4"),
            ("EPHEMERIS_LATITUDE_CORRECTION", "<f4"),
            ("ALT_PARTIALS_GROUP", "<f4", 18),
            ("NON_RANGE_SHARP_FIT", "<f4"),
            ("SCALING_FACTOR", "<f4"),
            ("NON_RANGE_SHARP_LOOKS", "<u4"),
            ("NON_RANGE_PROF_CORRS_INDEX", "<u4"),
            ("NON_RANGE_SHARP_ECHO_PROF", ">u1", 302),  # # UNSIGNED_INTEGER
            ("BEST_NON_RANGE_SHARP_MODEL_TPT", ">u1", 50),  # # UNSIGNED_INTEGER
            ("RANGE_SHARP_FIT", "<f4"),
            ("RANGE_SHARP_SCALING_FACTOR", "<f4"),
            ("RANGE_SHARP_LOOKS", "<u4"),
            ("RANGE_SHARP_PROF_CORRS_INDEX", "<u4"),
            ("RANGE_SHARP_ECHO_PROFILE", ">u1", 302),  # # UNSIGNED_INTEGER
            ("BEST_RANGE_SHARP_MODEL_TMPLT", ">u1", 50),  # # UNSIGNED_INTEGER
            ("MULT_PEAK_FRESNEL_REFLECT_CORR", "<f4"),
            ("DERIVED_PLANETARY_THRESH_RADI", "<f4"),
            ("SIGNAL_QUALITY_INDICATOR", "<f4"),  # # IEEE real
            ("DERIVED_THRESH_DETECTOR_INDEX", "<u4"),
            ("SPARE", "V28"),
        ]
    )
    adf = np.fromfile(fd, dtype=recOrig_t)
    fd.close()

    # Convert vax format numbers to float
    adf["ALTIMETRY_FOOTPRINT_TDB_TIME"] = vax2ieee(adf["ALTIMETRY_FOOTPRINT_TDB_TIME"])
    adf["ALT_SPACECRAFT_POSITION_VECTOR"] = vax2ieee(
        adf["ALT_SPACECRAFT_POSITION_VECTOR"]
    )
    adf["ALT_SPACECRAFT_VELOCITY_VECTOR"] = vax2ieee(
        adf["ALT_SPACECRAFT_VELOCITY_VECTOR"]
    )
    adf["ALT_FOOTPRINT_LONGITUDE"] = vax2ieee(adf["ALT_FOOTPRINT_LONGITUDE"])
    adf["ALT_FOOTPRINT_LATITUDE"] = vax2ieee(adf["ALT_FOOTPRINT_LATITUDE"])
    adf["ALT_ALONG_TRACK_FOOTPRINT_SIZE"] = vax2ieee(
        adf["ALT_ALONG_TRACK_FOOTPRINT_SIZE"]
    )
    adf["ALT_CROSS_TRACK_FOOTPRINT_SIZE"] = vax2ieee(
        adf["ALT_CROSS_TRACK_FOOTPRINT_SIZE"]
    )
    adf["RECEIVER_NOISE_CALIBRATION"] = vax2ieee(adf["RECEIVER_NOISE_CALIBRATION"])
    adf["UNCORRECTED_DISTANCE_TO_NADIR"] = vax2ieee(
        adf["UNCORRECTED_DISTANCE_TO_NADIR"]
    )
    adf["ATMOS_CORRECTION_TO_DISTANCE"] = vax2ieee(adf["ATMOS_CORRECTION_TO_DISTANCE"])
    adf["DERIVED_PLANETARY_RADIUS"] = vax2ieee(adf["DERIVED_PLANETARY_RADIUS"])
    adf["RADAR_DERIVED_SURF_ROUGHNESS"] = vax2ieee(adf["RADAR_DERIVED_SURF_ROUGHNESS"])
    adf["DERIVED_FRESNEL_REFLECTIVITY"] = vax2ieee(adf["DERIVED_FRESNEL_REFLECTIVITY"])
    adf["DERIVED_FRESNEL_REFLECT_CORR"] = vax2ieee(adf["DERIVED_FRESNEL_REFLECT_CORR"])
    adf["FORMAL_ERRORS_GROUP"] = vax2ieee(adf["FORMAL_ERRORS_GROUP"])
    adf["FORMAL_CORRELATIONS_GROUP"] = vax2ieee(adf["FORMAL_CORRELATIONS_GROUP"])
    adf["EPHEMERIS_RADIUS_CORRECTION"] = vax2ieee(adf["EPHEMERIS_RADIUS_CORRECTION"])
    adf["EPHEMERIS_LONGITUDE_CORRECTION"] = vax2ieee(
        adf["EPHEMERIS_LONGITUDE_CORRECTION"]
    )
    adf["EPHEMERIS_LATITUDE_CORRECTION"] = vax2ieee(
        adf["EPHEMERIS_LATITUDE_CORRECTION"]
    )
    adf["ALT_PARTIALS_GROUP"] = vax2ieee(adf["ALT_PARTIALS_GROUP"])
    adf["NON_RANGE_SHARP_FIT"] = vax2ieee(adf["NON_RANGE_SHARP_FIT"])
    adf["SCALING_FACTOR"] = vax2ieee(adf["SCALING_FACTOR"])
    adf["RANGE_SHARP_FIT"] = vax2ieee(adf["RANGE_SHARP_FIT"])
    adf["RANGE_SHARP_SCALING_FACTOR"] = vax2ieee(adf["RANGE_SHARP_SCALING_FACTOR"])
    adf["MULT_PEAK_FRESNEL_REFLECT_CORR"] = vax2ieee(
        adf["MULT_PEAK_FRESNEL_REFLECT_CORR"]
    )
    adf["DERIVED_PLANETARY_THRESH_RADI"] = vax2ieee(
        adf["DERIVED_PLANETARY_THRESH_RADI"]
    )

    return header, adf


def parseRDF(file, hdr):
    """Parse RDF data file.

    :param file: Path to RDF data file
    :type file: string

    :param hdr: Length of RDF data file header in bytes
    :type hdr: int

    :return: Tuple with dict containing header information and structured array containing RDF file data
    :rtype: (dict, np.ndarray)
    """
    fd = open(file, "rb")
    rdfhd = fd.read(hdr - 1)
    rdfhd = rdfhd.split(b"\r\n")
    header = {}
    for item in rdfhd:
        if len(item) > 0:
            item = item.split(b"=")
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
    rdf["RAD_SPACECRAFT_EPOCH_TDB_TIME"] = vax2ieee(
        rdf["RAD_SPACECRAFT_EPOCH_TDB_TIME"]
    )
    rdf["RAD_SPACECRAFT_POSITION_VECTOR"] = vax2ieee(
        rdf["RAD_SPACECRAFT_POSITION_VECTOR"]
    )
    rdf["RAD_SPACECRAFT_VELOCITY_VECTOR"] = vax2ieee(
        rdf["RAD_SPACECRAFT_VELOCITY_VECTOR"]
    )
    rdf["RAD_FOOTPRINT_LONGITUDE"] = vax2ieee(rdf["RAD_FOOTPRINT_LONGITUDE"])
    rdf["RAD_FOOTPRINT_LATITUDE"] = vax2ieee(rdf["RAD_FOOTPRINT_LATITUDE"])
    rdf["RAD_ALONG_TRACK_FOOTPRINT_SIZE"] = vax2ieee(
        rdf["RAD_ALONG_TRACK_FOOTPRINT_SIZE"]
    )
    rdf["RAD_CROSS_TRACK_FOOTPRINT_SIZE"] = vax2ieee(
        rdf["RAD_CROSS_TRACK_FOOTPRINT_SIZE"]
    )
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
    """Convert VAX floating point numbers to IEEE 754.

    :param vax: Array of VAX floats to convert
    :type vax: np.ndarray

    :return: Array of IEEE 754 floats corresponding to input VAX floats
    :rtype: np.ndarray
    """
    # VAX format specified here:
    # https://nssdc.gsfc.nasa.gov/nssdc/formats/VAXFloatingPoint.htm

    # Need to be clever with the bytes here to operate on a whole np.ndarray in one go
    # The data is read in as floats to have the right type in the
    # data array (otherwise the output of this function gets truncated)
    # But to do all the bit fiddling the data needs to be unsigned ints
    # So a using tobytes and frombuffer to acheive that
    dtype = vax.dtype
    shape = vax.shape
    buf = vax.tobytes(order="C")

    if dtype == np.float32:
        vax = np.frombuffer(buf, dtype=np.uint32)
    elif dtype == np.float64:
        vax = np.frombuffer(buf, dtype=np.uint64)

    vax = vax.reshape(shape)

    if vax.dtype == np.uint32:  # VAX F
        sgn = (vax & 0x00008000) >> 15  # Get the sign bit
        sgn = sgn.astype(np.int8)

        exp = (vax & 0x00007F80) >> 7  # exponent
        exp = exp.astype(np.int16)
        exp -= 128  # exponent bias

        msa = ((vax & 0x0000007F) << 16) | ((vax & 0xFFFF0000) >> 16)
        msa = msa.astype(np.float32)
        msa /= 2 ** 24
        msa += 0.5  # vax has 0.1m hidden bit vs ieee 1.m hidden bit

        return ((-1.0) ** sgn) * (msa) * ((2.0) ** exp)

    elif vax.dtype == np.uint64:  # VAX D
        sgn = (vax & 0x0000000000008000) >> 15  # Get the sign bit
        sgn = sgn.astype(np.int8)

        exp = (vax & 0x0000000000007F80) >> 7  # exponent
        exp = exp.astype(np.int16)
        exp -= 128  # exponent bias

        msa = (
            ((vax & 0x000000000000007F) << 48)
            | ((vax & 0x00000000FFFF0000) << 16)
            | ((vax & 0x0000FFFF00000000) >> 32)
            | ((vax & 0xFFFF000000000000) >> 32)
        )
        msa = msa.astype(np.float64)
        msa /= 2 ** 56
        msa += 0.5  # vax has 0.1m hidden bit vs ieee 1.m hidden bit
        return ((-1.0) ** sgn) * (msa) * ((2.0) ** exp)
