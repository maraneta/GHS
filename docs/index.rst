.. GHS Hazard Calculator documentation master file, created by
   sphinx-quickstart on Fri Jul 18 10:29:20 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

GHS Hazard Calculator
=====================

The GHS Hazard Calculator application provides a way to easily determine the hazards of a product, specified by 
the Globally Harmonized System of Classification and Labelling of Chemicals (GHS).  

.. Contents:

.. toctree::
   :maxdepth: 2
  

.. Indices and tables
   ==================

   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`


Configuration
=============

1. Download the GHS django project.
2. cd to the root directory and run the following command to install ghs-hazard-calculator: ::
	
	python setup.py install
	
3. Add ``hazard_calculator`` to ``INSTALLED_APPS``.
4. Change the ``ghs.settings`` file and ensure that the database configuration is correct (use the same database as your main application).



Usage
=====

A user can find the hazards of a flavor in a few steps:

1. Import the GHS label document (contains cas numbers and hazards for raw materials).
2. Find the CAS numbers and weights of all ingredients in the product's formula.
3. Input that data into ``calculate_flavor_hazards`` to get the product's calculated hazards.

