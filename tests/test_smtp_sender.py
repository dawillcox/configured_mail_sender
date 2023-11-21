import unittest
import os
import yaml
from configured_mail_sender.mail_sender import create_sender, MailSenderException
from configured_mail_sender.smtp_sender import (SMTPSender,
                                                SecurityProtocol,
                                                _get_port_security)
from unittest import TestCase
from smtplib import SMTP_SSL
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

CONF_BASE = os.path.join(os.path.split(__file__)[0], 'test_configs')
SERVICE_NAME = "smtp_test"
SERVICE_DOMAIN = "smtp.test"
SENDER = f"smtp_sender@{SERVICE_DOMAIN}"
SENDER_PASSWORD = "test?pwd9"
PREVIOUS_SENDER = f'prev_sender@{SERVICE_DOMAIN}'
PREVIOUS_PASSWORD = 'test?pwd9'
DOMAIN_FILE = os.path.join(CONF_BASE, "mailsender_domains.yml")


class TestSender(SMTPSender):
    def __init__(self, sender, domain_spec, **kwargs):
        SMTPSender.__init__(self, sender, domain_spec, **kwargs)

    def open(self):
        return SMTPSender.open(self)

    def get_service_name(self) -> str:
        return SERVICE_NAME

    def _create_server(self, **kwargs) -> SMTP_SSL:
        return MockSMTPSSL(**kwargs)

    def _get_password(self):
        # Don't want to have to type a password for tests
        if 'password' in self.kwargs.keys():
            return self.kwargs.get('password')

        return SENDER_PASSWORD


class MockSMTPSSL(SMTP_SSL):
    def __init__(self, **kwargs):
        self.port = kwargs.get('port')
        # self.userid = userid
        self.server = kwargs.get("host")
        self.sender = None
        self.password = None
        self.sent_sender = None
        self.receivers = None
        self.message = None

    def login(self, user, password, *, initial_response_ok=True):
        # verify that user and password are as expected
        self.sender = user
        self.password = password
        return None

    def sendmail(self, from_addr, to_addrs, msg, mail_options=(),
                 rcpt_options=()):
        self.sent_sender = from_addr
        self.receivers = to_addrs
        self.message = msg


class TestInvokeSMTP(TestCase):
    def test_create(self) -> None:
        self.assertRaises(MailSenderException,
                          lambda: create_sender("nobody@yahoo.com",
                                                password="badpwd"))


class TestBasic(TestCase):
    def setUp(self) -> None:
        self.sender = create_sender(SENDER,
                                    overrides=DOMAIN_FILE,
                                    password=SENDER_PASSWORD)
        with open(DOMAIN_FILE, 'r') as f:
            self.service_params = yaml.safe_load(f).get(SERVICE_DOMAIN)

    def test_create(self) -> None:
        """Basic test of mailer creation with password already known"""
        sender = self.sender
        self.assertEqual(SENDER_PASSWORD, sender.password)
        smtp = sender.smtp
        self.assertEqual(SENDER, smtp.sender)
        self.assertEqual(SENDER_PASSWORD, smtp.password)
        self.assertEqual(self.service_params['server'], smtp.server)
        self.assertEqual(self.service_params['port'], smtp.port)

    def test_send(self) -> None:
        """Create a message with To and Bcc and make sure things work as designed."""
        msg = MIMEMultipart()
        msg['Subject'] = 'This is a test'
        test_to = "test_to@example.com"
        test_bcc = "test_bcc@example.com,test_bcc2@example.com"
        test_cc = "test_cc@example.com,test_cc2@example.com"
        msg['To'] = test_to
        msg['Bcc'] = test_bcc
        msg['Cc'] = test_cc

        msg['From'] = SENDER
        msg.attach(MIMEText("Here's your report.", 'plain'))
        self.sender.send_message(msg)

        smtp = self.sender.smtp
        self.assertEqual(smtp.sender, SENDER)
        self.assertEqual(smtp.message, msg.as_string())
        receivers = set(smtp.receivers)
        for rs in [test_to, test_bcc, test_cc]:
            rs = rs.split(',')
            for r in rs:
                self.assertTrue(r in receivers, f'{r} missing in receivers')
                receivers.remove(r)
        self.assertTrue(len(receivers) == 0, f'Extra receivers in {receivers}')


class TestNewPassword(TestCase):

    def setUp(self) -> None:
        # Some setup, and make sure there isn't a leftover password file
        self.other_sender = f'anotherSender@{SERVICE_DOMAIN}'
        self.user_password_file = os.path.join(CONF_BASE,
                                               f'user_{self.other_sender}.yml')
        self.test_cred_file = os.path.join(CONF_BASE, "test_creds.yml")
        if os.path.exists(self.user_password_file):
            os.remove(self.user_password_file)

    def tearDown(self) -> None:
        torm = [f'{f}.lock' for f in [self.test_cred_file,  self.user_password_file]]
        torm += [self.user_password_file]
        # if os.path.exists(self.user_password_file):
        #     os.remove(self.user_password_file)
        for f in torm:
            if os.path.exists(f):
                os.remove(f)

    # If no password is available, a credentials file should be created
    def test_new_password(self):
        """ Verify credentials file update when prompted for a new password. """
        sender = create_sender(self.other_sender,
                               overrides=DOMAIN_FILE,
                               creds_file=self.user_password_file)
        self.assertIsNotNone(sender)
        self.assertTrue(os.path.exists(self.user_password_file),
                        'creds file should be created')
        with open(self.user_password_file, 'r') as f:
            new_certs = yaml.safe_load(f)
        cert_section = new_certs.get(self.other_sender)
        self.assertNotEqual(cert_section, None)
        self.assertEqual(cert_section.get('password'), SENDER_PASSWORD)

    def test_prev_password(self):
        """ Verifying that password in the cred file is correctly retrieved."""
        sender = create_sender(PREVIOUS_SENDER,
                               overrides=DOMAIN_FILE,
                               creds_file=self.test_cred_file)
        self.assertEqual(sender.password, PREVIOUS_PASSWORD)

    def test_explicit_password(self):
        """ Verify that explicit password overrides configuration file """
        test_pwd = "plover"
        sender = create_sender(PREVIOUS_SENDER,
                               overrides=DOMAIN_FILE,
                               password=test_pwd,
                               creds_file=self.test_cred_file)
        self.assertEqual(sender.password, test_pwd)


class TestPortSecurity(TestCase):
    """
    Testing that port or protocol can be set from the other
    """

    def test_bad_security(self):
        """Invalid security parameter should throw an exception"""
        conf = {'security': "unk"}
        self.assertRaises(MailSenderException,
                          lambda: _get_port_security(conf))

    def test_implied_port(self):
        """Port correctly deduced from specified security"""
        for test_security in SecurityProtocol:
            (port, security) = _get_port_security({'security': test_security.name})
            self.assertEqual(test_security.value, port)

    def test_implied_security(self):
        """Security protocol correctly deduced from specified port"""
        for test_security in SecurityProtocol:
            (port, security) = _get_port_security({'port': test_security.value})
            self.assertEqual(test_security.name, security.name)

    def test_both_set(self):
        """If both port and security protocol given, believe the user"""
        (port, security) = _get_port_security({'port': 33,
                                               'security': SecurityProtocol.SSL.name})
        self.assertEqual(33, port)
        self.assertEqual(SecurityProtocol.SSL.name, security.name)

    def test_default_security(self):
        """Assume SSL if using nonstandard port"""
        (port, security) = _get_port_security({'port': 99})
        self.assertEqual(SecurityProtocol.SSL.name, security.name)

    def test_explicit_override(self):
        """Port and security explicitly overwritten by caller"""
        kwargs = {'port': 999, 'security': SecurityProtocol.SSL.name}
        port_sec = {'port': 25, 'security': SecurityProtocol.NONE.name}
        (port, security) = _get_port_security(port_sec, **kwargs)
        self.assertEqual(port, 999)
        self.assertEqual(SecurityProtocol.SSL.name, security.name)


if __name__ == '__main__':
    unittest.main(verbosity=2)


