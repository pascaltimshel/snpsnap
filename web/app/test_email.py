#!/usr/bin/env python

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# fromaddr == my email address
# toaddr == recipient's email address
fromaddr = "snpsnap@broadinstitute.org"
toaddr = "pascal.timshel@gmail.com"

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = "PYTON TEST MAIL"
msg['From'] = fromaddr
msg['To'] = toaddr

# Create the body of the message (a plain-text and an HTML version).
text = "Hi!\nHow are you?\nHere is the link you wanted:\nhttp://www.python.org"
html = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
       How are you?<br>
       Here is the <a href="http://www.python.org">link</a> you wanted.
    </p>
  </body>
</html>
"""

# Record the MIME types of both parts - text/plain and text/html.
part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)
msg.attach(part2)

# From email June 5th 2014 from BITs
# ...You should either be using "localhost" if you are on a Linux VM, 
# or "smtp.broadinstitute.org" if "localhost" doesn't work. 
# Connecting to either of these email systems will use port 25 with no authentication.
### This works on the Broad server
server = smtplib.SMTP('localhost')
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()

#### This actually also works on the Broad server
# server = smtplib.SMTP('smtp.gmail.com', 587)
# server.ehlo()
# #The starttls() function starts Transport Layer Security mode, which is required by Gmail
# server.starttls() #If there has been no previous EHLO or HELO command this session, this method tries ESMTP EHLO first.
# server.ehlo()
# server.login("ptimshel@broadinstitute.org", "HIDDEN")
# text = msg.as_string()
# server.sendmail(fromaddr, toaddr, text)


# Email Client Settings
# Broad Gmail
# Incoming (IMAP)
# Server:	imap.gmail.com
# Username	Your Full Broad Email Address
# Port:	993
# Use SSL:	Yes
# Outgoing (SMTP)
# Server:	smtp.gmail.com
# Username	username@broadinstitute.org
# Port:	465 or 587
# Use STARTTLS:	Yes (or SSL)
# Webmail:
# http://mail.broadinstitute.org/

