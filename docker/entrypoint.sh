#! /usr/bin/env bash

/usr/local/bin/python3 /app/docker/wait_mysql.py

if [ ! -f /app/xss_receiver/Config.py ];then
    mkdir /app/uploads;
    mkdir /app/temp_uploads;
    mkdir -p /app/static$URL_PREFIX/;
    cp -r /app/docker/front_dist/* /app/static$URL_PREFIX/;

    /usr/local/bin/python3 /app/gen_config.py $LOGIN_PASSWORD

fi

chown www-data /app/uploads && chmod 700 /app/uploads
chown www-data /app/temp_uploads && chmod 700 /app/temp_uploads
chown www-data /app/xss_receiver/Config.py && chmod 700 /app/xss_receiver/Config.py

/usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
