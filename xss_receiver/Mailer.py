import smtplib
from email.mime.text import MIMEText
from email.header import Header
from threading import Thread
from xss_receiver import Config, cached_config


class Mailer:
    threads = []

    @staticmethod
    def _send_mail(path, content):
        if Config.SEND_MAIL_SMTP_SSL:
            smtp = smtplib.SMTP_SSL(Config.SEND_MAIL_SMTP_HOST, Config.SEND_MAIL_SMTP_PORT)
        else:
            smtp = smtplib.SMTP(Config.SEND_MAIL_SMTP_HOST, Config.SEND_MAIL_SMTP_PORT)

        message = MIMEText(content, 'plain', 'utf-8')
        message['From'] = Header(Config.SEND_MAIL_ADDR, 'utf-8')
        message['To'] = Header(cached_config.RECV_MAIL_ADDR, 'utf-8')

        subject = f'[XSS Notice] [{path}]'
        message['Subject'] = Header(subject, 'utf-8')

        smtp.login(Config.SEND_MAIL_ADDR, Config.SEND_MAIL_PASSWD)
        smtp.sendmail(Config.SEND_MAIL_ADDR, [cached_config.RECV_MAIL_ADDR], message.as_string())

    @staticmethod
    def send_mail(path, content):
        if cached_config.RECV_MAIL_ADDR.strip() != '':
            thread = Thread(target=Mailer._send_mail, args=(path, content,))
            thread.start()
