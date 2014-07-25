import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='ghs-hazard-calculator',
    version='0.1',
    packages=['hazard_calculator'],
    package_dir = {"": "src"},
    include_package_data=True,
    license='BSD License',  # example license
    description='A Django app that calculates hazards of products.',
    long_description=README,
    url='http://www.example.com/',
    zip_safe=False, #this installs the egg as a directory; allows django egg loader to find staticfiles
    install_requires = ['django-autocomplete-light>=1.4.14'],
    author='Matt Araneta',
    author_email='maraneta@foo.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
