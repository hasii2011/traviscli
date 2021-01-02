from logging import Logger
from logging import getLogger

from tests.TestBase import TestBase

from travisci.Preferences import Preferences


class TestPreferences(TestBase):
    """
    This class only tests the basic dynamic creation portions of the
    Preferences class
    """
    clsLogger: Logger = None

    @classmethod
    def setUpClass(cls):
        TestBase.setUpLogging()
        TestPreferences.clsLogger = getLogger(__name__)

    def setUp(self):
        self.logger:   Logger       = TestPreferences.clsLogger

    def tearDown(self):
        pass

    def testBasicSectionCreation(self):

        preferences: Preferences = Preferences()
