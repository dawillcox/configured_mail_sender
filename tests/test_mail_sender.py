from os import path
# from unittest import TestCase
import unittest
from email.mime.base import MIMEBase
import platformdirs

import configured_mail_sender
from configured_mail_sender.mail_sender import MailSender,\
    create_sender, MailSenderException
from unittest import TestCase

TEST_CONFIG_DIR = path.join(path.split(__file__)[0], 'test_configs')

CONF_BASE = TEST_CONFIG_DIR
CONF_FILE = path.join(CONF_BASE, 'mailsender_domains.yml')
# APPLICATION = 'testapp'
SENDER = 'foo@base.com'
APPLICATION_PARAM = "test_setting"
APPLICATION_SETTING_VALUE = "setting_value"
SERVICE_NAME = "test_service"


class TestBase(MailSender):
    def __init__(self, sender, **kwargs):
        MailSender.__init__(self, sender, **kwargs)
        self.message = None

    def get_service_name(self):
        return SERVICE_NAME

    def send_message(self, message: MIMEBase) -> None:
        self.message = message


class Test(TestCase):
    def test_creation(self):
        """Instantiate basic class and verify some generic settings"""
        mailer = create_sender(SENDER, overrides=CONF_FILE)

        self.assertEqual(mailer.sender, SENDER)
        self.assertEqual(SERVICE_NAME, mailer.get_service_name())

    def test_no_gmail(self):
        """Make sure attempt to use gmail protocol fails as expected"""
        self.assertRaises(MailSenderException,
                          lambda: create_sender("foo@gmail.none.test",
                                               overrides=CONF_FILE))

    def test_bad_module(self):
        self.assertRaises(MailSenderException,
                          lambda: create_sender('foo@bad.server',
                                                overrides=CONF_FILE))

    def test_bad_domain(self):
        self.assertRaises(MailSenderException,
                          lambda: create_sender("foo@nosuchdomain"))

    def test_no_sender(self):
        self.assertRaises(MailSenderException,
                          lambda: create_sender(None))

    def test_domain_list(self):
        domains = configured_mail_sender.mail_sender.known_domains()
        self.assertEqual('smtp.mail.yahoo.com', domains.get('yahoo.com'))
        self.assertEqual(7, len(domains))

    def test_file_list(self):
        config_files = configured_mail_sender.config_file_list()
        self.assertEqual(path.join(platformdirs.user_config_path('MailSender'),
                                   'mailsender_creds.yml'),
                         config_files[-1])
        self.assertEqual(path.join(platformdirs.site_config_path('MailSender'),
                                   'mailsender_domains.yml'),
                         config_files[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
