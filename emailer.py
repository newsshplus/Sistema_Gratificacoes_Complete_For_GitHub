
import smtplib, ssl
from email.message import EmailMessage

def send_email(smtp_host, smtp_port, smtp_user, smtp_pass, sender, recipients, subject, body, attachment_path=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(recipients if isinstance(recipients, (list,tuple)) else [recipients])
    msg.set_content(body)
    if attachment_path:
        with open(attachment_path,'rb') as f:
            data = f.read()
        msg.add_attachment(data, maintype='application', subtype='pdf', filename=attachment_path.split('/')[-1])
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
        server.starttls(context=context)
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
    return True
