import sys
import os
import unittest
import dev_appserver
import logging
import time
from google.appengine.tools.devappserver2 import devappserver2
from google.appengine.tools.devappserver2 import python_runtime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from google.appengine.ext.remote_api import remote_api_stub
import secret_keys


class LocalSeleniumTestCase(unittest.TestCase):

    def setUp(self):
        #Start a new App Engine server
        self.SERVER_NAME = 'localhost'
        self.SERVER_PORT = '8123'
        python_runtime._RUNTIME_ARGS = [
            sys.executable,
            os.path.join(os.path.dirname(dev_appserver.__file__),
                         '_python_runtime.py')
        ]
        options = devappserver2.PARSER.parse_args([
            '--admin_port', '0',
            '--port', self.SERVER_PORT,
            '--datastore_path', ':memory:',
            '--logs_path', ':memory:',
            '--skip_sdk_update_check',
            '--',
        ] + [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__name__))))])
        server = devappserver2.DevelopmentServer()
        server.start(options)
        self.server = server
        self.base_url = "http://%s:%s" % (self.SERVER_NAME, self.SERVER_PORT)
        #Initialize Selenium
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(5)

        self.verificationErrors = []
        self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.server.stop()
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

    def initialize_default_datastore(self):
        time.sleep(3)

        def auth_func():
            return (secret_keys.ADMIN_USERNAME, secret_keys.ADMIN_PASSWORD)

        remote_api_stub.ConfigureRemoteApi(
            None,
            '/_ah/remote_api',
            auth_func,
            '%s:%s' % (self.SERVER_NAME, self.SERVER_PORT)
        )

    #----------------------------assert section -------------------------------

    def assert_element_visible(self, how, what, message):
        try:
            return WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((how, what)))
        except:
            logging.exception('')
            self.fail(message)

    def assert_element_invisible(self, how, what, message):
        try:
            return WebDriverWait(self.driver, 3).until(EC
            .invisibility_of_element_located((how, what)))
        except:
            self.fail(message)


    #------------------------bussines logic section ---------------------------
    def test_list(self):
        driver = self.driver
        #self.initialize_default_datastore()


        self.default_login('/process')
        self.assert_element_visible(By.ID,'processes-list','Process list '
                                                           'title does not '
                                                           'appears')

if __name__ == '__main__':
    unittest.main()
