#-------------------------------------------------------------------------------
# Name: email_shapefile
# Purpose: Email a zip file containing a shapefile
#
# Author: Jason Piwarski
#
# Created:     28/01/2015
# Copyright:   (c) Jason Piwarski 2015
#-------------------------------------------------------------------------------

import os, sys, smtplib, zipfile, string
from email import Encoders
from email.mime.text import MIMEText
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formatdate

shapefile = "C:\Users\Admin\Desktop\Crowd Hydrology\data"
zip_output = "C:\Users\Admin\Desktop\Crowd Hydrology\zipped\gauges"

def zip(src, dst):
    zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            zf.write(absname, arcname)
    zf.close()

def send_email_with_attachment(subject, host, from_addr, body_text, emails, file_to_attach):

    #Name the attachment here
    header = 'Content-Disposition', 'attachment; filename=gauges.zip'

    # create the message
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    if body_text:
        msg.attach( MIMEText(body_text) )

    msg["To"] = ', '.join(emails)

    attachment = MIMEBase('application', "octet-stream")
    try:
        with open(file_to_attach, "rb") as fh:
            data = fh.read()
        attachment.set_payload( data )
        Encoders.encode_base64(attachment)
        attachment.add_header(*header)
        msg.attach(attachment)
    except IOError:
        msg = "Error opening attachment file %s" % file_to_attach
        print msg
        sys.exit(1)

    server = smtplib.SMTP(host)
    server.ehlo()
    server.starttls()
    server.login("mmhiatoolkit", "MMHIA2014")
    server.sendmail(from_addr, emails, msg.as_string())
    server.quit()

if __name__ == '__main__':
    zip(shapefile,zip_output)
    host = "smtp.gmail.com:587"
    from_addr = "mmhiatoolkit@gmail.com" #we'll need an "official" crowd hydrology address
    emails = ["jasonpiwarsk1@gmail.com"]
    subject = "Test email with attachment from Python"
    body_text = "This email contains an attachment!"
    file_to_attach = "C:\Users\Admin\Desktop\Crowd Hydrology\zipped\gauges.zip"
    send_email_with_attachment(subject, host, from_addr, body_text, emails, file_to_attach)
    print 'done'

