Convert RDF/ADF to CSV/GPKG
===========================

magellantools includes command line tools to convert ADF and RDF files to different (more convenient) file formats - particularly CSV and Geopackage.

.. warning::
    Most multi-value fields in the ADF and RDF files are excluded from the CSV/GPKG files produced by these tools, such as the echo profiles in the ADF files. To access these fields please use the Python API.

First - download example ADF and RDF files:

.. code:: bash

	wget -nc https://pds-geosciences.wustl.edu/mgn/mgn-v-rdrs-5-cdr-alt-rad-v1/mg_2008/17611780/rdf01761.lbl
	wget -nc https://pds-geosciences.wustl.edu/mgn/mgn-v-rdrs-5-cdr-alt-rad-v1/mg_2008/17611780/rdf01761.1
	wget -nc https://pds-geosciences.wustl.edu/mgn/mgn-v-rdrs-5-cdr-alt-rad-v1/mg_2008/17611780/adf01761.lbl
	wget -nc https://pds-geosciences.wustl.edu/mgn/mgn-v-rdrs-5-cdr-alt-rad-v1/mg_2008/17611780/adf01761.1

Then use the command line tools to convert them. The command line tools take a directory as an argument and convert all files of the specified type in the given directory. The example below converts all ADF files in the current directory to a single Geopackage named :code:`adf.gpkg`:

.. code:: bash

	arcdr2gpkg . adf adf.gpkg