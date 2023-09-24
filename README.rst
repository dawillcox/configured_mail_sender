======================
Configured Mail Sender
======================

Overview
--------------
There are multitudinous Python packages for sending emails with widely
varying interfaces. Some concentrate on constructing the email message,
others concentrate on the delivery. But virtually all require the caller to
have explicit knowledge of *how* the email will be delivered. Typically the
caller needs to know at least:

* The address and port for the SMTP server. (The fact that servers
  may have different connection encryption schems is generally ignored.)
* The sending email address.
* Login name for the smtp server, if different from the sender's address.
* Login credentials, typically password.

All the above vary by sending email address of course. This of course
puts the onus on the email package user to maintain the above for each
potential sender. And for password (or other protocol-specific authentication
values), they need to be protected in some way, at least readable only by
the user.

And, of course, they don't support more secure authentication systems like
Google's OAuth2.

With ``configured_email_sender``, the application only needs to know the sending email address.
``configured_email_sender.mail_sender`` uses
`combine-settings <https://pypi.org/project/combine-settings/>`_
to find all it needs to deliver the mail. Public settings, e.g, SMTP
address and port can be public for the whole site. Private information
(passwords) should be readable only by the user.

How It Works
-------------
``configured_mail_sender`` makes it easy for a Python script to send emails on behalf of a user
without dealing with the details of interaction with the sending email provider.
Your script needs to know only the sending email address. ``mail_sender`` uses configuration
files (system-wide or user-specific) to figure out how to communicate with the sender's
email domain.

The sending Python script creates a ``MailSender`` object for the sending email address.
It can then construct emails in the form of ``Mime`` objects and use the ``MailSender`` object
to send them.

Here's a simple example:

.. code-block::

    from configured_mail_sender import mail_sender
    from email.mime.text import MIMEText

    sender = mail_sender('sending-email@somedomain.com')
    msg = MIMEText("This is a test message", 'plain')
    msg['Subject'] = 'Success!'
    msg['To'] = 'receiver@gmail.com'
    msg['Cc'] = ['ccer1@somewhere.org', 'ccer2@elswhere.com']
    msg['Bcc'] = 'private@somedomain.com'

    sender.send_message(msg)


See the `DOCUMENTATION <https://github.com/dawillcox/configured_mail_sender/blob/main/DOCUMENTATION.rst>`_ for details on how to
configure ``configured_mail_sender``.
