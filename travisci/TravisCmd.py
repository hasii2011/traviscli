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
from PyTravisCI.resource_types.user import User

import click


from travisci.Preferences import Preferences


class TravisCmd:

    JSON_LOGGING_CONFIG_FILENAME: str = "loggingConfiguration.json"

    MADE_UP_PRETTY_MAIN_NAME:     str = "TravisCmd"

    RESOURCES_PACKAGE_NAME: str = 'travisci.resources'
    RESOURCES_PATH:         str = f'travisci{osSep}resources'

    RESOURCE_ENV_VAR:       str = 'RESOURCEPATH'

    def __init__(self):

        self._setupSystemLogging()
        self.logger: Logger = getLogger(TravisCmd.MADE_UP_PRETTY_MAIN_NAME)

        Preferences.determinePreferencesLocation()
        self._preferences: Preferences = Preferences()

        self._buildCount:   int = 1
        self._repoSlugName: str = ''

    def runCommand(self):

        travisciApiToken: str = self._preferences.travisciApiToken
        self.logger.debug(f'Running Command with token: {travisciApiToken}')

        travisCI: TravisCI = TravisCI(access_token=travisciApiToken, access_point=defaults.access_points.PRIVATE)

        # We get our very own account information.
        me: User = travisCI.get_user()

        self.logger.info(f'Running as {me.name=} {me.login=}')

        params = {'limit': self._buildCount}

        repository: Repository = travisCI.get_repository(self._repoSlugName)
        repoBuilds: Builds     = repository.get_builds(params=params)

        self.logger.debug(f"{'Build ID':<10} {'Number':<10} {'State':<10} {'Slug':<100}")

        self._highestBuildNumber: int = 0
        for build in repoBuilds:
            self.logger.debug(f"{build.id:<10} {build.number:<10} {build.state:<10} {build.repository.slug:<100}")
            if int(build.number) > self._highestBuildNumber:
                self._highestBuildNumber = int(build.number)
        self.logger.info(f'{self._highestBuildNumber=}')

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
    def versionText(self) -> str:
        return self._versionTxt

    @versionText.setter
    def versionText(self, newValue: str):
        self._versionTxt = newValue

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

        configFilePath: str = self._retrieveResourcePath(TravisCmd.JSON_LOGGING_CONFIG_FILENAME)

        with open(configFilePath, 'r') as loggingConfigurationFile:
            configurationDictionary = jsonLoad(loggingConfigurationFile)

        config.dictConfig(configurationDictionary)
        logging.logProcesses = False
        logging.logThreads   = False

    def _retrieveResourcePath(self, bareFileName: str) -> str:

        # Use this method in Python 3.9
        # from importlib_resources import files
        # configFilePath: str  = files('travisci.resources').joinpath(TravisCmd.JSON_LOGGING_CONFIG_FILENAME)

        try:
            fqFileName: str = resource_filename(TravisCmd.RESOURCES_PACKAGE_NAME, bareFileName)
        except (ValueError, Exception):
            #
            # Maybe we are in an app
            #
            from os import environ
            pathToResources: str = environ.get(f'{TravisCmd.RESOURCE_ENV_VAR}')
            fqFileName:      str = f'{pathToResources}{osSep}{TravisCmd.RESOURCES_PATH}{osSep}{bareFileName}'

        return fqFileName


@click.command()
@click.option('-c', '--count',     default=1,      help='Number builds to return.')
@click.option('-r', '--repo-slug', required=True,  help='something thing like hasii2011/PyUt.')
@click.option('-f', '--file',      default='travisci/resources/version.txt', type=click.File('r'),  help='Relative location of version text file')
def main(count: int, repo_slug: str, file: TextIO):

    print(f'{count=} {repo_slug=}')
    travisCmd: TravisCmd = TravisCmd()

    travisCmd.buildCount   = count
    travisCmd.repoSlugName = repo_slug
    travisCmd.versionText  = file.read()

    # Launch travisCmd
    travisCmd.runCommand()


if __name__ == "__main__":

    print(f"Starting {TravisCmd.MADE_UP_PRETTY_MAIN_NAME}")
    main()
