FROM python:3.10.1

COPY requirements.txt /
RUN python3 -m pip install -r /requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

COPY . /app
RUN useradd -ms /bin/bash app && mkdir -m700 /app/uploads && mkdir -m700 /app/temp_uploads &&\
     chown app /app/uploads && chown app /app/temp_uploads

USER app

ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
