# Magellan PDS Tools
[![Documentation Status](https://readthedocs.org/projects/magellantools/badge/?version=latest)](https://magellantools.readthedocs.io/en/latest/?badge=latest)

<p align="center">
  <img src="docs/source/img/logo.png" />
</p>

magellantools is a small Python library and set of command line tools to read, manipulate, and export (to more convenient formats) radar and radiometry data acquired by NASA's Magellan mission to Venus that is archived on the [Planetary Data System](https://pds-geosciences.wustl.edu/missions/magellan/index.htm).

We do not currently support all of the data types on the PDS (see list below). Requests to add support for a specific data type are welcome, but contributing to the code to add support for that data type is even more welcome.

Supported data types:  
- [] ARCDR  
	- [x] ADF  
	- [x] RDF  