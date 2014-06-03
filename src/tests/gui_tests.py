import sys
import os
import unittest
import dev_appserver
from google.appengine.tools.devappserver2 import devappserver2
from google.appengine.tools.devappserver2 import python_runtime
from selenium import webdriver


class LocalSeleniumTestCase(unittest.TestCase):

    def setUp(self):
        #Start a new App Engine server
        SERVER_NAME = 'localhost'
        SERVER_PORT = '8123'
        python_runtime._RUNTIME_ARGS = [
            sys.executable,
            os.path.join(os.path.dirname(dev_appserver.__file__),
                         '_python_runtime.py')
        ]
        options = devappserver2.PARSER.parse_args([
            '--admin_port', '0',
            '--port', SERVER_PORT,
            '--datastore_path', ':memory:',
            '--logs_path', ':memory:',
            '--skip_sdk_update_check',
            '--',
        ] + [os.path.join(os.path.dirname(os.path.abspath(__name__)))])
        server = devappserver2.DevelopmentServer()
        server.start(options)
        self.server = server
        self.base_url = "http://%s:%s" % (SERVER_NAME, SERVER_PORT)
        #Initialize Selenium
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(5)

        self.verificationErrors = []
        self.accept_next_alert = True

    def tearDown(self):
        self.server.stop()
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

    def default_login(self, url, user_email=None):
        #Login and load home page
        self.driver.get(self.base_url + '/admin/')
        if user_email:
            self.driver.find_element_by_id("email").clear()
            self.driver.find_element_by_id("email").send_keys(user_email)
        self.driver.find_element_by_id('admin').click()
        self.driver.find_element_by_id('submit-login').click()
        self.driver.get(self.base_url + url)

    def test_birthday_list(self):
        driver = self.driver
        self.driver.get(self.base_url + '/admin/birthdays/upload')

if __name__ == '__main__':
    unittest.main()
