__author__ = 'chris'

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

files = []

setup(name='pySpikeGL',
      version='0.1dev',
      description="Interactive graphing interface for spikeGL.",
      author='Rinberg Lab',
      packages=['pySpikeGL'], requires=['PyQt4', 'scipy', 'numpy', 'galry']
      )
