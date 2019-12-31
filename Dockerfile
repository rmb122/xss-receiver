FROM tiangolo/uwsgi-nginx-flask:python3.7

COPY . /app
COPY ./docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN cp /app/docker/default /etc/nginx/conf.d/default.conf && cp /app/docker/nginx.conf /etc/nginx/nginx.conf

RUN /usr/local/bin/python3 -m pip install -r /app/requirements.txt -i https://mirrors.ustc.edu.cn/pypi/web/simple

EXPOSE 80

ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
