#!/usr/bin/env python3
import os
import sys
import mysql.connector
import mailparser
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

###
###        change fwd.best in this file to your domain
###


dbhost = os.getenv("DBHOST")
dbuser = os.getenv("DBUSER")
dbpass = os.getenv("DBPASS")
dbname = os.getenv("DBNAME")
tabname = os.getenv("TABNAME")

port = os.getenv("PORT")
smtp_server = os.getenv("SMTP_SERVER")
sender_email = os.getenv("SENDER_EMAIL")

password = os.getenv("PASSWORD")

dt_obj = datetime.utcnow()
a=dt_obj.timestamp()*100
fname = str("%.f" % a)+'.log'

v=""
for line in sys.stdin:
    v=v+line

file = open('parser/files/'+fname, 'w')
file.write(v)
file.close()



def check_aliaz(alias):
    db = mysql.connector.connect(host=dbhost, user=dbuser, password=dbpass,database=dbname)

    cursor = db.cursor()

    query = "SELECT destination FROM "+tabname+" where alias='"+alias+"'"
    cursor.execute(query)

    rows=cursor.fetchone()
    db.close()
    if rows:
        return rows[0]
    else:
        return None

def add_alias(alias,destination):
    db = mysql.connector.connect(host=dbhost, user=dbuser, password=dbpass,database=dbname)
    cursor = db.cursor()
 
    query = "INSERT into  "+tabname+"  (alias, destination) VALUES ('"+alias+"', '"+destination+"')"

    cursor.execute(query)
    db.commit()
    db.close()

mail = mailparser.parse_from_string(v)

mail_from = mail.from_[0][1]
mail_to = mail.to[0][1]
mail_subject = mail.subject
html_body = mail.text_html[0]
#mail_text=mail.text_plain[0]
mail_text = mail.text_plain[0] if len(mail.text_plain)>0 else ''


if mail_to=="install@fwd.best" and mail_subject=="install":
    add_alias(mail_from.split("@")[0],mail_from)
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "forwarder registered"
    message["From"] = sender_email
    message["To"] = mail_from
    alias = mail_from.split("@")[0]
    mail_text = "Now yo can use address "+alias+".XXX@fwd.best  where XXX can be any character or digit, any amount. But dot is important!"

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(mail_text, "plain")
     
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
     

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, mail_from, message.as_string()
        )  

else:
    alias = mail_to.split("@")[0]
    destination = check_aliaz(alias.rsplit(".",1)[0])
    if destination:
            
        message = MIMEMultipart("alternative")
        message["Subject"] = "["+mail_to+"] "+mail_subject
        message["From"] = sender_email
        message["To"] = destination

        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(mail_text, "plain")
        part2 = MIMEText(html_body, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, destination, message.as_string()
            )