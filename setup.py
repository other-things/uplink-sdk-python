# -*- coding: utf-8 -*-
from distutils.core import setup

setup(name='Uplink SDK py',
      version='0.5',
      description='Python bindings for Adjoint project uplink',
      url='http://github.com/adjoint-io/uplink-sdk-py',
      author='Adjoint Inc.',
      author_email='info@adjoint.io',
      license='All Rights Reserved',
      packages=["uplink"],
      install_requires=[
          "requests == 2.11.1",
          "cryptography >= 1.7.1",
          "ecdsa == 0.13",
          "pytest >= 2.6.4",
          "pysha3 >= 1.0.2",
          "base58 >= 0.2.4",
          'typing'
      ]
      )
