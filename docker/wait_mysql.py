import socket
import time

def wait_for_mysql(host):
    success = False
    while not success:
        print('[*] Waiting mysql start...')
        time.sleep(1)
        try:
            sck = socket.socket()
            sck.settimeout(1)
            sck.connect((host, 3306))
            sck.close()
            success = True
        except Exception:
            pass


wait_for_mysql("mysql")
