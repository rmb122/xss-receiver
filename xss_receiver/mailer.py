import asyncio
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

import aiosmtplib

from xss_receiver import constants
from xss_receiver import system_config
from xss_receiver.database import session_maker
from xss_receiver.utils import add_system_log


async def send_mail(path, content):
    smtp = aiosmtplib.SMTP(system_config.SEND_MAIL_SMTP_HOST, system_config.SEND_MAIL_SMTP_PORT,
                           use_tls=system_config.SEND_MAIL_SMTP_SSL)

    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = formataddr(("XSS Bot", system_config.SEND_MAIL_ADDR))
    message['To'] = formataddr(("User", system_config.RECV_MAIL_ADDR))

    subject = f'[XSS Notice] [{path}]'
    message['Subject'] = Header(subject, 'utf-8')

    async def login_and_send():
        try:
            await smtp.connect()
            await smtp.login(system_config.SEND_MAIL_ADDR, system_config.SEND_MAIL_PASSWD)
            await smtp.sendmail(system_config.SEND_MAIL_ADDR, [system_config.RECV_MAIL_ADDR], message.as_string())
        except Exception as e:
            db_session = session_maker()
            await add_system_log(db_session, f"Mail send error [{str(e)}]", constants.LOG_TYPE_MAIL_SEND_ERROR)
            await db_session.close()

    asyncio.create_task(login_and_send())
