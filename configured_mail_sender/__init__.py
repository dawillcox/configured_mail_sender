from .mail_sender import create_sender, MailSenderException, MailSender

# The following is a total hack. If anyone has a better solution, please share.
#
# The import above lets a user do:
#   import configured_mail_sender
#   sender = configured_mail_sender.creat_sender(....)
# without the intervening reference to mail_sender. But without the following
# or something like it, ruff complains that those imports aren't referenced
# and "fail" the commit in github.
# Fortunately ruff isn't smart enough to recognize that the code isn't reachable.
if 0:
    try:
        create_sender("foo")
        MailSender('x')
    except MailSenderException:
        pass


