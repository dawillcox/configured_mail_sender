from typing import Tuple

from configured_mail_sender import MailSender, MailSenderException
from getpass import getpass
from smtplib import SMTP_SSL, SMTPException, SMTP
from email.mime.base import MIMEBase
from enum import Enum

"""
This is a MailSender version for sending to a generic SMTP server. It assumes
SSL is needed.

This needs:
    server, port:
        The server and port to connect to. These could be passed in as parameters,
        or could come from the caller, or could be taken from the domain configuration
        file. We assume that server and port will be the same for any application.
    
    sender:
        The email sender, who's sending the email. (User and domain.) This is an
        explicit parameter from the mail_sender() caller.
    
    password:
        This comes from the user's readonly credentials file file. If the file
        doesn't exist with the password, SMTPSender prompts the user to enter a
        password and saves the password for later use.
    
SMTP supports three encryption protocols, and by convention those correspond
to standard ports:
    port 25 implies no encryption. Connections to that port are vulnerable to
        sniffing data, including your password. Its use is generally not supported
        and is discouraged, but there may be some servers that still use it.
    Port 465 is SSL encrypted, so much more secure, but there are vulnerabilities.
        But this is the most common implementation.
    Port 587 is encrypted but uses STARTTLS, which avoids the SSL vulnerability.
        But it isn't always supported.
    
When creating a connection, if only port or security is specified in the domain
configuration, the other parameter will be inferred from the first. If neither
is given, SSL on port 465 is used.
"""


class SecurityProtocol(Enum):
    NONE = 25  # Is this really supported
    SSL = 465
    STARTTLS = 587


# Map from standard port to default protocol.
_PORT_SECURITY = {p.value: p for p in SecurityProtocol}


def _get_port_security(domain_spec: dict,
                       **kwargs: dict) -> Tuple[int, SecurityProtocol]:
    """Return the port security enum from the configuration
    :param domain_spec: Configuration for this email domain
    :param **port_spec: Override port in domain_spec
    :param **security: Override security in domain_spec
    :return: Port number and security
    """

    port = kwargs.get('port', domain_spec.get('port'))
    security_name = kwargs.get('security', domain_spec.get('security'))
    if security_name:
        try:
            security = SecurityProtocol[security_name.upper()]
            if not port:
                # Port not specified, so use default for the protocol
                port = security.value
        except KeyError as e:
            raise MailSenderException(e,
                                      f'{security_name} is not one of '
                                      f'{",".join(p.name for p in SecurityProtocol)}')
    else:
        port = port if port else SecurityProtocol.SSL.value
        security = _PORT_SECURITY.get(port, SecurityProtocol.SSL)

    return port, security


class SMTPSender(MailSender):
    def __init__(self, sender: str,
                 domain_spec: dict,
                 **kwargs: dict):
        """
        Class to facilitate sending gmail
        :param sender: Sending email address
        :param **server: Server name
        :param **password: Password for connection if explicitly provided
        """
        MailSender.__init__(self, sender, domain_spec=domain_spec, **kwargs)

        server = self.domain_spec.get('server')
        (self.port, self.security) = _get_port_security(self.domain_spec, **kwargs)

        # Not recommended, but if password came in from creation, save it
        self.password = kwargs.get('password')
        if self.password:
            self.user_credentials['password'] = self.password

        self.smtp = None
        self.server = server
        self.userid = None

    def open(self):
        """Initialize, including setting up connection to the server.
        :returns: self
        """
        MailSender.open(self)
        # Now that we know who to connect to, get the user's password.
        update_needed = self._complete_credentials()
        self.smtp = self._create_server(host=self.server, timeout=50, port=self.port)

        self.userid = self.kwargs.get('userid',
                                      self.user_credentials.get('userid', self.sender))
        try:
            self.smtp.login(self.userid, self.password)
        except SMTPException as e:
            raise MailSenderException(e, f'Login to {self.userid} failed.')

        # Successfully logged in. Update credential file if needed
        if update_needed:
            self._update_creds()
        return self

    def _create_server(self, **kwargs) -> SMTP:
        """Open an SMTP connection. (This is a method to facilitate unit tests.)
        :param kwargs: Other parameters including host and port.
        :return: SMTP Server
        """
        if self.security is SecurityProtocol.SSL:
            return SMTP_SSL(**kwargs)
        else:
            sender = SMTP(**kwargs)
            if self.security is SecurityProtocol.STARTTLS:
                sender.starttls()
            return sender

    def _complete_credentials(self) -> bool:
        """
        Initialize credentials from credentials file.
        Extending class may need to add more than password?
        :return: True if credentials file needs to be re-written.
        """

        if self.password:
            # We already have a password
            return False

        self.password = self.user_credentials.get('password', None)
        if self.password:
            return False
        else:
            # Need to get password and save it if valid.
            self.password = self.user_credentials['password'] = self._get_password()
            return True

    def _get_password(self) -> str:
        """
        Ask the user to enter a password.
        :return: password(str)

        Note: This is a non-static method to facilitate unit tests.
        """

        # Not recommended, mostly for unit tests, but use password from instantiation if specified.
        pwd = self.kwargs.get("password")
        if pwd is None:
            pwd = getpass(f'Enter password for user "{self.sender}:')
        return pwd

    def send_message(self, message: MIMEBase) -> None:
        """
        Send a MIME email message. Recipients are encoded in the message.
        :param message: message to send
        """
        r_list = [message.get(r) for r in ['To', 'Cc', 'Bcc']]
        r_list = [r for r in r_list if r]
        receivers = ','.join(r_list)
        sender_name = self.user_credentials.get('name')
        message['From'] = f'{sender_name} <{self.sender}>' if sender_name else self.sender
        self._send_message(self.sender, receivers, message.as_string())

    def _send_message(self, sender: str, receivers: str, msg_str: str) -> None:
        """
        Do the actual send. (This is a class method to facilitate unit tests.)
        :param sender: Sending address
        :param receivers: Comma-separated list of receivers
        :param msg_str: Message as encoded string
        """
        self.smtp.sendmail(sender, receivers, msg_str)

    def get_service_name(self) -> str:
        return 'smtp'
