import pathlib
from setuptools import setup
from setuptools import find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name="traviscli",
    version="0.1.0",
    author_email='Humberto.A.Sanchez.II@gmail.com',
    description='A build help tool',
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/hasii2011/travisci-cli",
    packages=find_packages(),
    include_package_data=False,
    package_data={'travisci.resources': ['*.json', 'travisci/resources/*.json']},
    install_requires=['click', 'PyTravisCI']
)