
from logging import Logger
from logging import getLogger

from os import getenv
from os import sep as osSep

from sys import platform

from configparser import ConfigParser

from travisci.Singleton import Singleton

from travisci.exceptions.PreferencesLocationNotSet import PreferencesLocationNotSet


class Preferences(Singleton):

    THE_GREAT_MAC_PLATFORM: str = 'darwin'
    PREFERENCES_FILE_NAME:  str = '.travisci-cli.ini'

    TRAVIS_CI_SECTION:      str = 'TRAVISCI'

    TRAVISCI_API_TOKEN_KEY:  str = 'travisci_api_token'

    preferencesFileLocationAndName: str = None

    def init(self):

        self.logger:  Logger = getLogger(__name__)

        self._config: ConfigParser = ConfigParser()
        self._loadConfiguration()

    @staticmethod
    def determinePreferencesLocation():
        """
        This method MUST (I repeat MUST) be called before
        attempting to instantiate the preferences Singleton
        """
        if platform == "linux2" or platform == "linux" or platform == Preferences.THE_GREAT_MAC_PLATFORM:
            Preferences.preferencesFileLocationAndName = getenv("HOME") + osSep + Preferences.PREFERENCES_FILE_NAME
        else:
            Preferences.preferencesFileLocationAndName = Preferences.PREFERENCES_FILE_NAME

    @staticmethod
    def getPreferencesLocation():
        if Preferences.preferencesFileLocationAndName is None:
            raise PreferencesLocationNotSet()
        else:
            return Preferences.preferencesFileLocationAndName

    @property
    def travisciApiToken(self) -> str:
        return self._config.get(Preferences.TRAVIS_CI_SECTION, Preferences.TRAVISCI_API_TOKEN_KEY)

    @travisciApiToken.setter
    def travisciApiToken(self, newValue: str):
        self._config.set(Preferences.TRAVIS_CI_SECTION, Preferences.TRAVISCI_API_TOKEN_KEY, newValue)
        self.__saveConfig()

    def _loadConfiguration(self):
        """
        Load preferences from configuration file
        """
        self.__ensureConfigurationFileExists()
        self._config.read(Preferences.getPreferencesLocation())

        self.__createSectionIfNecessary(Preferences.TRAVIS_CI_SECTION)

        self.__createNeededConfigurationKeys()

        self.__saveConfig()

    def __ensureConfigurationFileExists(self):

        # Make sure that the configuration file exists
        # noinspection PyUnusedLocal
        try:
            f = open(Preferences.getPreferencesLocation(), "r")
            f.close()
        except (ValueError, Exception) as e:
            try:
                f = open(Preferences.getPreferencesLocation(), "w")
                f.write("")
                f.close()
                self.logger.warning(f'Preferences file re-created')
            except (ValueError, Exception) as e:
                self.logger.error(f"Error: {e}")
                return

    def __createSectionIfNecessary(self, sectionName: str):

        hasSection: bool = self._config.has_section(sectionName)
        self.logger.debug(f'hasSection: {hasSection} - {sectionName}')
        if hasSection is False:
            self._config.add_section(sectionName)

    def __createNeededConfigurationKeys(self):

        if self._config.has_option(Preferences.TRAVIS_CI_SECTION, Preferences.TRAVISCI_API_TOKEN_KEY) is False:
            self._config.set(Preferences.TRAVIS_CI_SECTION, Preferences.TRAVISCI_API_TOKEN_KEY, 'PutYourTravisCIKeyHere')

    def __saveConfig(self):
        """
        Save configuration data to the configuration file
        """
        f = open(Preferences.getPreferencesLocation(), "w")
        self._config.write(f)
        f.close()
