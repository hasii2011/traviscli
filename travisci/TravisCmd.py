

import logging

from logging import Logger
from logging import getLogger
from logging import config

from json import load as jsonLoad

from PyTravisCI import TravisCI
from pkg_resources import resource_filename

from os import sep as osSep

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

    def runCommand(self):

        travisciApiToken: str = self._preferences.travisciApiToken
        self.logger.info(f'Running Command with token: {travisciApiToken}')

        travisCI: TravisCI = TravisCI(access_token=travisciApiToken)

        # We get our very own account information.
        me = travisCI.get_user()
        self.logger.info(f'Running as {me=}')

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


if __name__ == "__main__":

    print(f"Starting {TravisCmd.MADE_UP_PRETTY_MAIN_NAME}")

    travisCmd: TravisCmd = TravisCmd()

    # Launch travisCmd
    travisCmd.runCommand()
