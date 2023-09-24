from configured_mail_sender.mail_sender import mail_sender
from email.mime.text import MIMEText
import logging

fromemail = 'daw30410@yahoo.com'
# fromemail = 'dwillcox@urbanatroop104.org'
# fromemail = 'dwillcoxster@gmail.com'
# fromemail = "financial-secretary@community-ucc.org"
logging.basicConfig(level=logging.DEBUG)
sender = mail_sender(fromemail)

msg = MIMEText("This is a test message", 'plain')
msg['Subject'] = 'Success!'
msg['To'] = 'dwillcoxster@gmail.com'
msg['Cc'] = 'daw30410@yahoo.com'

sender.send_message(msg)

# print(sender)
