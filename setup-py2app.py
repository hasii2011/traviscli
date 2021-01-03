"""
This is a setup-py2app.py script generated by py2applet

Usage:
    python setup-py2app.py py2app
"""

from setuptools import setup

APP = ['travisci/TravisCmd.py']
DATA_FILES = [('travisci/resources', ['travisci/resources/loggingConfiguration.json']),
              ('travisci/resources', ['travisci/resources/version.txt']),
              ]
OPTIONS = {}

setup(
    app=APP,
    data_files=DATA_FILES,
    packages=['travisci',
              'travisci/exceptions'
              ],
    include_package_data=True,
    zip_safe=False,

    url='https://github.com/hasii2011/travisci-cli',
    author='Humberto A. Sanchez II',
    author_email='Humberto.A.Sanchez.II@gmail.com',
    description='A build help tool',
    options={},
    setup_requires=['py2app'],
    install_requires=['click',
                      'PyTravisCI',
                      ]
)
