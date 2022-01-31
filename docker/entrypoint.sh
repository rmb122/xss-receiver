#! /usr/bin/env bash

mkdir -m755 /app/uploads && mkdir -m755 /app/temp_uploads &&\
     chown www-data /app/uploads && chown www-data /app/temp_uploads

python3 /app/docker/wait_mysql.py
su www-data -s /bin/bash -c 'python3 /app/app.py'