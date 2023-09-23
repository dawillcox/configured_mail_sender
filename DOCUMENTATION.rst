=============
Configured Mail Sender Documentation
=============

``configured_mail_sender`` makes it easy for a Python script to send emails on behalf of a user
without dealing with the details of interaction with the sending email provider.
Your script needs to know only the sending email address. ``mail_sender`` uses configuration
files (system-wide or user-specific) to figure out how to communicate with the sender's
email domain.

Your Python script creates a ``MailSender`` object for the sending email address.
It can then construct emails as ``Mime`` objects and use the ``MailSender`` object
to send them.

Here's a simple example:

.. code-block:: python

    from configured_mail_sender import mail_sender
    from email.mime.text import MIMEText

    sender = mail_sender('sending-email@somedomain.com')
    msg = MIMEText("This is a test message", 'plain')
    msg['Subject'] = 'Success!'
    msg['To'] = 'receiver@gmail.com'
    msg['Cc'] = ['ccer1@somewhere.org', 'ccer2@elswhere.com']
    msg['Bcc'] = 'private@somedomain.com'

    sender.send_message(msg)

Much more complex emails are possible, including attachments and HTML formatting,
but that's standard ``Mime`` stuff. ``MailSender`` doesn't need to know
the internals of the email.
See the `email.mime <https://docs.python.org/3/library/email.mime.html>`_
documentation for details.

Everything needed to communicate with the sender's email service comes
from system and/or user configuration files. Your application doesn't need to deal with that.

Configuring to send emails
---------------
``configured_mail_sender`` uses two sets of configuration files to
set up communication with the sending email address.

``mailsender_domains.yml`` files tell it how to interact with the servers
that handle outgoing emails for a given email domain (the part after the '@'
in the sending email address).

A ``mailsender_creds.yml`` file has whatever is needed to convince the server that you're
allowed to send emails from that email address.

Outgoing Email Domains
~~~~~~~~

``mail_sender`` uses
`combine-settings <https://pypi.org/project/combine-settings/>`_
to build outgoing email domain cofigurations from one or more
``mailsender_domains.yml`` files.
See the documentation for ``combine-settings`` for just how this works,
but in short it looks for ``mailsender_domains.yml`` files from:

* built-in defaults from ``configured_mail_sender``
* global installation-specific settings
* settings from the Python virtual environment
* user-specific settings
* specific settings from parameters in the ``combine-settings`` call.

``configured_mail_sender.mail_sender()`` passes any relevant
parameters through to ``combine-settings``.

The assembled domain configuration has a configuration for each
potential outgoing domain, something like this:

.. code-block:: yaml

    yahoo.com:
      protocol: smtp      # smtp is assumed
      server: smtp.mail.yahoo.com
      port: 587
      security: STARTTLS


protocol
    specifies the connection and authentication protocol used
    by the sending email domain. ``configured_mail_sender`` out of the box
    supports only SMTP, the most used protocol, but it can be configured
    for others. The default for this setting is ``smtp``, but if you have
    a custom extension of the abstract base ``MailSender`` class you
    can put the class path of that class here as ``protocol``. (The
    ``configured_mail_sender`` unit tests use this feature if you want to
    seen how that works.) The remaining settings here apply only to the
    SMTP protocol.

server
    is the domain name of the SMTP server to connect to.

port
    is the port to connect to.

security
    is the connection security used.

About port and security... There are several standard ports used by
SMTP servers, corresponding to different schemes used to set up
connection encryption. Here are the standard ports and corresponding
encryption:

+-----+---------------------+-------------------------------------+
| Port| Encryption Scheme   | Comment                             |
+-----+---------------------+-------------------------------------+
|   25|  None               | Insecure and strongly discouraged   |
|     |                     | even if allowed.                    |
+-----+---------------------+-------------------------------------+
|  485|  SSL                | Encrypted, but older with security  |
|     |                     | vulnerabilities. But probably most  |
|     |                     | widely available.                   |
+-----+---------------------+-------------------------------------+
|  587|  STARTTLS           | Newer, more secure.                 |
|     |                     | Supported by the major servers.     |
|     |                     | Recommended.                        |
+-----+---------------------+-------------------------------------+

Port and security will be used as follows:

* If both port and security are given, they will be used as given.
* If only security is given, the associated port will be used.
* If only port is given, the associated security will be used, or SSL if port is not one of the standard ports.
* If neither port nor security is given, SSL on port 485 will be used.

``configured_mail_sender`` has built-in defaults for some common email
domains, including:

* yahoo.com
* aol.com
* gmail.com
* outlook.com
* hotmail.com
* live.com
* comcast.net

Others can be easily added in your site or user ``mailsender_domains.yml`` file.


User Credentials
~~~~~~~~
The credentials a user needs to send emails
are stored in the user's ``mailsender_creds.yml`` file.
Unlike ``mailsender_domains.yml``, each user has their own, private
``mailsender_creds.yml`` file. It contains whatever tokens are needed to
tell the outgoing email server that your application is allowed to send
from that email address.

The credentials come from the first of:

* A file given in the ``creds_file`` parameter to the ``mailsender()`` call.
* A file named in the ``MAILSENDER_CREDS`` environment variable.
* A file in the os-appropriate user directory as determined by
  `platformdirs <https://pypi.org/project/platformdirs/>`_ as follows:

.. code-block:: python

    import platformdirs
    dir = platformdirs.user_config_path('MailSender')

Please consult `platformdirs <https://pypi.org/project/platformdirs/>`_
to see how that works for your environment.
Because it contains sensitive information the ``mailsender_creds.yml`` file
should be readable only by the user, but should be writable by the user
because in some situations it may need to be updated. The directory itself
must be writable by the user.

The ``mailsender_creds.yml`` has one entry for each outgoing email address
with whatever is needed to authenticate with the email server. Each entry
should be something like this:

.. code_block:: yaml

itsreallyme@comcast.net:
    password: password123456 # A really bad example
    userid: itssortofme

userid
    By default the sending email address is assumed to be the userid to
    log in to the SMTP server. If that's not correct use this setting
    to override the default.
password
    This is the password to connect to the SMTP server for this sender.
    If the SMTP server doesn't require a password, you probably shouldn't
    be using it. If no password is provided, ``mail_sender`` will prompt
    the user for one, and if the connection succeeds it will update the
    ``mailsender_creds.yml`` to include it.

Creating a MailSender
=====================
Once you've set up all of the configuration files you're all set to
start sending emails. See the code example at the beginning of this
document But there are a few other parameters to
``mail_sender()`` that power-users might want to use:

base_config
    This will override the builtin ``configured_mail_sender`` defaults
    for the domain configuration. This can be either a file name
    or a Python dict with settings.

overrides
    This is another set of settings that override anything that
    ``combine_settings`` finds in its domain files.

creds_file
    As mentioned above, this gives an alternate location for the user's
    credentials file.

password, userid
    Not recommended, but the user's userid and/or password can be
    given as explicit parameters.

