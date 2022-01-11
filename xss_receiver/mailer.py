import asyncio
from email.header import Header
from email.mime.text import MIMEText

import aiosmtplib

from xss_receiver import system_config


async def send_mail(path, content):
    smtp = aiosmtplib.SMTP(system_config.SEND_MAIL_SMTP_HOST, system_config.SEND_MAIL_SMTP_PORT,
                           use_tls=system_config.SEND_MAIL_SMTP_SSL)

    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = Header(system_config.SEND_MAIL_ADDR, 'utf-8')
    message['To'] = Header(system_config.RECV_MAIL_ADDR, 'utf-8')

    subject = f'[XSS Notice] [{path}]'
    message['Subject'] = Header(subject, 'utf-8')

    async def login_and_send():
        await smtp.login(system_config.SEND_MAIL_ADDR, system_config.SEND_MAIL_PASSWD)
        await smtp.sendmail(system_config.SEND_MAIL_ADDR, [system_config.RECV_MAIL_ADDR], message.as_string())

    asyncio.create_task(login_and_send())
