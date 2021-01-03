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

        highestBuildNumber: str = '0'
        for build in repoBuilds:

            if int(build.number) > int(highestBuildNumber):
                highestBuildNumber = build.number

        self.logger.info(f'{highestBuildNumber=}')

        readFD:          TextIO          = open(self._versionFile, "r")
        semanticVersion: SemanticVersion = SemanticVersion(readFD.read())
        readFD.close()

        print(f'Old Version: {semanticVersion}')

        highestBuildNumber = f'+.{highestBuildNumber}'
        semanticBuildNbr = semanticVersion.toBuildNumber(highestBuildNumber)
        semanticVersion.build = semanticBuildNbr

        print(f'New Version: {semanticVersion}')

        writeFD: TextIO = open(self._versionFile, "w")

        writeFD.write(semanticVersion.__str__())
        writeFD.close()

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


@click.command()
@click.option('-c', '--count',     default=1,      help='Number builds to return.')
@click.option('-r', '--repo-slug', required=True,  help='something thing like hasii2011/PyUt.')
@click.option('-f', '--file',      default='travisci/resources/version.txt', type=click.Path(exists=True),  help='Relative location of version text file')
def main(count: int, repo_slug: str, file: TextIO):

    print(f'{count=} {repo_slug=}')
    travisCmd: TravisCli = TravisCli()

    travisCmd.buildCount   = count
    travisCmd.repoSlugName = repo_slug
    travisCmd.versionFile  = file

    # Launch travisCmd
    travisCmd.runCommand()


if __name__ == "__main__":

    print(f"Starting {TravisCli.MADE_UP_PRETTY_MAIN_NAME}")
    main()
