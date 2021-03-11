from pathlib import Path
from typing import TextIO
from typing import cast

import logging

from logging import Logger
from logging import getLogger
from logging import config

from pkg_resources import resource_filename

from json import load as jsonLoad

from os import sep as osSep

from PyTravisCI import TravisCI
from PyTravisCI import defaults

from click import Context
from click import command
from click import option
from click import version_option
from click import get_current_context
from click import secho
from click import open_file
from click import style
from click import INT
from click import Path as clickPath
from click import clear as clickClear
from click import echo as clickEcho

from PyTravisCI.resource_types.builds import Builds
from PyTravisCI.resource_types.repository import Repository

from travisci.Preferences import Preferences
from travisci.SemanticVersion import SemanticVersion
from travisci.exceptions.UnsupportedOperation import UnsupportedOperation


class TravisCli:

    JSON_LOGGING_CONFIG_FILENAME: str = "loggingConfiguration.json"
    MADE_UP_PRETTY_MAIN_NAME:     str = "TravisCli"

    RESOURCES_PACKAGE_NAME: str = 'travisci.resources'
    RESOURCES_PATH:         str = f'travisci{osSep}resources'
    RESOURCE_ENV_VAR:       str = 'RESOURCEPATH'

    def __init__(self):

        self._setupSystemLogging()
        self.logger: Logger = getLogger(TravisCli.MADE_UP_PRETTY_MAIN_NAME)

        Preferences.determinePreferencesLocation()
        self._preferences: Preferences = Preferences()

        self._buildCount:   int    = 1
        self._repoSlugName: str    = ''
        self._versionFile:  Path = cast(Path, None)
        self._majorVersion = ''
        self._minorVersion = ''
        self._patchVersion = ''

    def runCommand(self):

        repoBuilds:      Builds          = self._getTravisBuilds()
        semanticVersion: SemanticVersion = self.__getCurrentVersion()

        semanticVersion = self._updateVersionNumber(semanticVersion=semanticVersion)

        self._updateBuildNumber(semanticVersion=semanticVersion, repoBuilds=repoBuilds)

    @property
    def buildCount(self) -> int:
        raise UnsupportedOperation('CLI properties are write-only')

    @buildCount.setter
    def buildCount(self, newValue: int):
        self._buildCount = newValue

    @property
    def repoSlugName(self) -> str:
        raise UnsupportedOperation('CLI properties are write-only')

    @repoSlugName.setter
    def repoSlugName(self, newValue: str):
        self._repoSlugName = newValue

    @property
    def versionFile(self) -> Path:
        raise UnsupportedOperation('CLI properties are write-only')

    @versionFile.setter
    def versionFile(self, file: Path):
        self._versionFile = file

    @property
    def majorVersion(self) -> str:
        raise UnsupportedOperation('CLI properties are write-only')

    @majorVersion.setter
    def majorVersion(self, newVersion: str):
        self._majorVersion = newVersion

    @property
    def minorVersion(self) -> str:
        raise UnsupportedOperation('CLI properties are write-only')

    @minorVersion.setter
    def minorVersion(self, newVersion: str):
        self._minorVersion = newVersion

    @property
    def patchVersion(self) -> str:
        raise UnsupportedOperation('CLI properties are write-only')

    @patchVersion.setter
    def patchVersion(self, newVersion: str):
        self._patchVersion = newVersion

    def _getTravisBuilds(self) -> Builds:
        """
        Get a set of builds from Travis CI for the selected repository

        Returns:  The Travis builds
        """
        travisciApiToken: str = self._preferences.travisciApiToken
        self.logger.debug(f'Running Command with token: {travisciApiToken}')

        travisCI: TravisCI = TravisCI(access_token=travisciApiToken, access_point=defaults.access_points.PRIVATE)

        params = {'limit': self._buildCount}
        repository: Repository = travisCI.get_repository(self._repoSlugName)
        travisBuilds: Builds = repository.get_builds(params=params)

        return travisBuilds

    def _updateVersionNumber(self, semanticVersion: SemanticVersion) -> SemanticVersion:
        """
        Only one of the 3 numbers is not None
        If the minor version is updated then patch version goes to zero
        if the major version is updated then both the minor and patch version go to zero

        Args:
            semanticVersion:  The version the update

        Returns:

        """

        if self._patchVersion is not None:
            semanticVersion.patch = self._patchVersion
        elif self._minorVersion is not None:
            semanticVersion.minor = self._minorVersion
            semanticVersion.patch = 0
        elif self._majorVersion is not None:
            semanticVersion.major = self._majorVersion
            semanticVersion.minor = 0
            semanticVersion.patch = 0

        return semanticVersion

    def _updateBuildNumber(self, semanticVersion: SemanticVersion, repoBuilds: Builds):

        highestBuildNumber: str = self.__getHighestBuildNumber(repoBuilds)

        highestBuildNumber = f'+.{highestBuildNumber}'      # Normalize it

        semanticVersion = self.__updateVersionFile(highestBuildNumber, semanticVersion)

        return semanticVersion

    def _setupSystemLogging(self):

        configFilePath: str = self._retrieveResourcePath(TravisCli.JSON_LOGGING_CONFIG_FILENAME)

        with open(configFilePath, 'r') as loggingConfigurationFile:
            configurationDictionary = jsonLoad(loggingConfigurationFile)

        config.dictConfig(configurationDictionary)
        logging.logProcesses = False
        logging.logThreads   = False

    def _retrieveResourcePath(self, bareFileName: str) -> str:

        # Use this method in Python 3.9
        # from importlib_resources import files
        # configFilePath: str  = files('travisci.resources').joinpath(TravisCli.JSON_LOGGING_CONFIG_FILENAME)

        try:
            fqFileName: str = resource_filename(TravisCli.RESOURCES_PACKAGE_NAME, bareFileName)
        except (ValueError, Exception):
            #
            # Maybe we are in an app
            #
            from os import environ
            pathToResources: str = environ.get(f'{TravisCli.RESOURCE_ENV_VAR}')
            fqFileName:      str = f'{pathToResources}{osSep}{TravisCli.RESOURCES_PATH}{osSep}{bareFileName}'

        return fqFileName

    def __getHighestBuildNumber(self, repoBuilds: Builds) -> str:
        """
        Searches the input list of repository builds and determines the largest build number

        Args:
            repoBuilds: The Travis CI repository builds

        Returns:  The string version of the build number
        """
        highestBuildNumber: str = '0'

        for build in repoBuilds:

            if int(build.number) > int(highestBuildNumber):
                highestBuildNumber = build.number

        self.logger.info(f'{highestBuildNumber=}')

        return highestBuildNumber

    def __getCurrentVersion(self) -> SemanticVersion:
        """
        Reads the version text file that is in semantic version format

        Returns:  The semantic version object that represents the current version stored in the text file
        """
        readDescriptor:  TextIO          = open_file(self._versionFile, mode='r')
        semanticVersion: SemanticVersion = SemanticVersion(readDescriptor.read())
        readDescriptor.close()

        secho(f'Old Version: {semanticVersion}')

        return semanticVersion

    def __updateVersionFile(self, normalizedBuildNumber: str, semanticVersion: SemanticVersion) -> SemanticVersion:
        """
        Updates the version text file

        Args:
            normalizedBuildNumber:  String set up as 'proper' build number
            semanticVersion:        The semantic version from the old text file
        """
        semanticBuildNbr      = semanticVersion.toBuildNumber(normalizedBuildNumber)
        semanticVersion.build = semanticBuildNbr
        secho(f'New Version: {semanticVersion}')

        writeDescriptor: TextIO = open_file(self._versionFile, mode='w')
        writeDescriptor.write(semanticVersion.__str__())
        writeDescriptor.close()

        return semanticVersion


@command()
@option('-b', '--build-count',     default=5,      type=INT, help='Number builds to check.')
@option('-r', '--repo-slug',   required=True,  help='something thing like hasii2011/PyUt.')
@option('-f', '--file',        default='travisci/resources/version.txt', type=clickPath(exists=True),  help='Relative location of version text file')
@option('--major-version',     required=False, type=INT, help='Change the major number to the specified one')
@option('--minor-version',     required=False, type=INT, help='Change the minor number to the specified one')
@option('--patch-version',     required=False, type=INT, help='Change the patch number to the specified one')
@version_option(version='0.3.0', message='%(version)s')
def commandHandler(build_count: int, repo_slug: str, file: TextIO, major_version: int, minor_version: int, patch_version: int):
    """
    Use this command to get the Travis CI build number of your project.  Assumes you are using Semantic Versioning
    """
    clickClear()
    clickEcho(style(f"Starting {TravisCli.MADE_UP_PRETTY_MAIN_NAME}", reverse=True))

    travisCmd: TravisCli = TravisCli()

    travisCmd.buildCount   = build_count
    travisCmd.repoSlugName = repo_slug
    travisCmd.versionFile  = file

    ctx: Context = get_current_context()
    if (major_version and minor_version) or (major_version and patch_version) or (minor_version and patch_version):
        clickEcho('You can only specify one of --major-version, --minor-version, or --patch-version')
        ctx.exit(1)

    travisCmd.majorVersion = major_version
    travisCmd.minorVersion = minor_version
    travisCmd.patchVersion = patch_version

    # Launch travisCmd
    travisCmd.runCommand()


if __name__ == "__main__":

    commandHandler()
