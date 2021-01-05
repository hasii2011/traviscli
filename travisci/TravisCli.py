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

from PyTravisCI.resource_types.builds import Builds

from PyTravisCI.resource_types.repositories import Repositories
from PyTravisCI.resource_types.repository import Repository

import click

from travisci.Preferences import Preferences
from travisci.SemanticVersion import SemanticVersion


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

    def runCommand(self):

        travisciApiToken: str = self._preferences.travisciApiToken
        self.logger.debug(f'Running Command with token: {travisciApiToken}')

        travisCI: TravisCI = TravisCI(access_token=travisciApiToken, access_point=defaults.access_points.PRIVATE)

        params = {'limit': self._buildCount}

        repository: Repository = travisCI.get_repository(self._repoSlugName)
        repoBuilds: Builds     = repository.get_builds(params=params)

        self._updateBuildNumber(repoBuilds)

    @property
    def buildCount(self) -> int:
        return self._buildCount

    @buildCount.setter
    def buildCount(self, newValue: int):
        self._buildCount = newValue

    @property
    def repoSlugName(self) -> str:
        return self._repoSlugName

    @repoSlugName.setter
    def repoSlugName(self, newValue: str):
        self._repoSlugName = newValue

    @property
    def versionFile(self) -> Path:
        return self._versionFile

    @versionFile.setter
    def versionFile(self, file: Path):
        self._versionFile = file

    def _updateBuildNumber(self, repoBuilds: Builds):

        highestBuildNumber: str             = self.__getHighestBuildNumber(repoBuilds)
        semanticVersion:    SemanticVersion = self.__getCurrentVersion()

        highestBuildNumber = f'+.{highestBuildNumber}'      # Normalize it

        self.__updateVersionFile(highestBuildNumber, semanticVersion)

    def _listRepositories(self, travisCI):
        repositories: Repositories = travisCI.get_repositories()
        # Loop until there are no more pages to navigate.
        while True:
            for repository in repositories:
                repository: Repository = cast(Repository, repository)
                self.logger.info(f'{repository.name=} {repository.slug=}')

            if repositories.has_next_page():
                repositories = repositories.next_page()
                continue
            break

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
        readDescriptor:  TextIO          = click.open_file(self._versionFile, mode='r')
        semanticVersion: SemanticVersion = SemanticVersion(readDescriptor.read())
        readDescriptor.close()

        click.secho(f'Old Version: {semanticVersion}')

        return semanticVersion

    def __updateVersionFile(self, normalizedBuildNumber: str, semanticVersion: SemanticVersion):
        """
        Updates the version text file

        Args:
            normalizedBuildNumber:  String set up as 'proper' build number
            semanticVersion:        The semantic version from the old text file
        """
        semanticBuildNbr      = semanticVersion.toBuildNumber(normalizedBuildNumber)
        semanticVersion.build = semanticBuildNbr
        click.secho(f'New Version: {semanticVersion}')

        writeDescriptor: TextIO = click.open_file(self._versionFile, mode='w')
        writeDescriptor.write(semanticVersion.__str__())
        writeDescriptor.close()


@click.command()
@click.option('-c', '--count',     default=5,      type=click.INT, help='Number builds to check.')
@click.option('-r', '--repo-slug', required=True,  help='something thing like hasii2011/PyUt.')
@click.option('-f', '--file',      default='travisci/resources/version.txt', type=click.Path(exists=True),  help='Relative location of version text file')
@click.option('--major',    required=False, type=click.INT, help='Change the major number to the specified one')
@click.option('--minor',    required=False, type=click.INT, help='Change the minor number to the specified one')
@click.option('--patch',    required=False, type=click.INT, help='Change the patch number to the specified one')
@click.version_option(version='0.1', message='%(version)s')
def commandHandler(count: int, repo_slug: str, file: TextIO, major: int, minor: int, patch: int):

    click.clear()
    click.echo(click.style(f"Starting {TravisCli.MADE_UP_PRETTY_MAIN_NAME}", reverse=True))

    travisCmd: TravisCli = TravisCli()

    travisCmd.buildCount   = count
    travisCmd.repoSlugName = repo_slug
    travisCmd.versionFile  = file

    ctx = click.get_current_context()
    if (major and minor) or (major and patch) or (minor and patch):
        click.echo('You can only specify one of --major, --minor, or --patch')
        ctx.exit(1)

    # Launch travisCmd
    travisCmd.runCommand()


if __name__ == "__main__":

    commandHandler()
