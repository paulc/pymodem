#!/usr/bin/env python

try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import Command,setup

import pymodem
long_description = pymodem.description
version = pymodem.version

class GenerateReadme(Command):
    description = "Generates README file from long_description"
    user_options = []
    def initialize_options(self): pass
    def finalize_options(self): pass
    def run(self):
        open("README","w").write(long_description)

setup(name='pymodem',
      version = version,
      description = 'Simple Python interface to generic terminal and (specifically) GSM modem devices. Includes general serial connection/chat, AT command, SMS (including GSM.03.38) support.',
      long_description = long_description,
      author = 'Paul Chakravarti',
      author_email = 'paul.chakravarti@gmail.com',
      url = 'https://github.com/paulchakravarti/pymodem',
      cmdclass = { 'readme' : GenerateReadme },
      packages = ['pymodem'],
      license = 'BSD',
      classifiers = [ "Topic :: Terminals :: Serial" ]
     )
