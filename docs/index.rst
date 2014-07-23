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
	
3. In your project settings file, add ``hazard_calculator`` to ``INSTALLED_APPS``.
4. In your project settings file, under ``TEMPLATE_LOADERS``, uncomment or add the following line. ::

	'django.template.loaders.eggs.load_template_source'
	
   This allows your project to use templates from the GHS Hazard Calculator python egg that 
   was installed via the ``setup.py`` command above.

5. The ``hazard_calculator`` app should now be properly installed and configured.  Try visiting 
   the url ``/ghs_app/hazard_calculator``.



Usage
=====

A user can find the hazards of a flavor in a few steps:

1. Import the GHS label document (contains cas numbers and hazards for raw materials).
2. Find the CAS numbers and weights of all ingredients in the product's formula.
3. Input that data into ``calculate_flavor_hazards`` to get the product's calculated hazards.


Main Functions
==============

.. automodule:: hazard_calculator.tasks


.. autofunction:: import_GHS_ingredients_from_document   
.. autofunction:: calculate_flavor_hazards  