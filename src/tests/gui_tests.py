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
from inbox import constants
from inbox.models import CleanUserProcess
import secret_keys
import fixtures


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
        fixtures.add_example_clean_process_users(amount=45)
        self.default_login('/admin/process')
        self.assert_element_visible(
            By.ID,'processes-list','Process list title does not appears')

        td_list1 = [td.text for td in driver.find_elements_by_xpath(
            '//*[@id="process-list"]/tbody/tr/td[1]')]
        self.assertEquals(constants.PAGE_SIZE, len(td_list1),'list len does '
                                                            'not match')
        self.assert_element_invisible(By.ID,'prev-id','button appears')
        self.assert_element_visible(By.ID,'home-id','button does not appear')
        self.assert_element_visible(By.ID,'next-id','button does not '
                                                    'appear').click()

        td_list2 = [td.text for td in driver.find_elements_by_xpath(
            '//*[@id="process-list"]/tbody/tr/td[1]')]
        self.assertEquals(constants.PAGE_SIZE, len(td_list2),'list len does '
                                                            'not match')
        self.assert_element_visible(By.ID,'prev-id','button appears')
        self.assert_element_visible(By.ID,'home-id','button does not appear')
        self.assert_element_visible(By.ID,'next-id','button does not '
                                                    'appear').click()
        self.assertNotEqual(set(td_list1),set(td_list2))

        td_list3 = [td.text for td in driver.find_elements_by_xpath(
            '//*[@id="process-list"]/tbody/tr/td[1]')]
        self.assertLess(len(td_list3),constants.PAGE_SIZE)

        self.assert_element_invisible(By.ID,'next-id','button does not appear')
        self.assert_element_visible(By.ID,'home-id','button does not appear')
        self.assert_element_visible(By.ID,'prev-id','button appears').click()
        self.assertNotEqual(set(td_list2),set(td_list3))

        td_list4 = [td.text for td in driver.find_elements_by_xpath(
            '//*[@id="process-list"]/tbody/tr/td[1]')]
        self.assertEquals(constants.PAGE_SIZE, len(td_list4),'list len does '
                                                            'not match')
        self.assertEquals(set(td_list2),set(td_list4))

    def test_create(self):
        driver = self.driver
        self.default_login('/admin/process')
        driver.find_element_by_id('process_name').send_keys('process1')
        driver.find_element_by_id('source_email').send_keys('test')
        driver.find_element_by_id('source_password').send_keys(
            secret_keys.ADMIN_PASSWORD)
        driver.find_element_by_id('search_criteria').send_keys('search_criteria')
        driver.find_element_by_id('add-process-button').click()
        self.assert_element_invisible(By.CLASS_NAME, 'alert-success','object '
                                                                     'appears')

        driver.find_element_by_id('source_email').clear()
        driver.find_element_by_id('source_email').send_keys(
            secret_keys.ADMIN_USERNAME)
        driver.find_element_by_id('add-process-button').click()
        time.sleep(2)
        self.assert_element_visible(By.CLASS_NAME, 'alert-success','Object '
                                                                   'does not '
                                                                   'appears')
        td_list1 = [td.text for td in driver.find_elements_by_xpath(
            '//*[@id="process-list"]/tbody/tr/td[1]')]
        self.assertEquals(1, len(td_list1),'list len does not match')

if __name__ == '__main__':
    unittest.main()
