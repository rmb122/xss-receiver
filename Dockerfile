FROM python:3.10.1

ENV DEBIAN_FRONTEND noninteractive

RUN sed -i 's|security.debian.org/debian-security|mirrors.ustc.edu.cn/debian-security|g' /etc/apt/sources.list &&\
      sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && apt update -y && apt install -y libcap2-bin &&\
        setcap 'cap_net_bind_service=+ep' $(realpath $(which python3))

COPY requirements.txt /
RUN python3 -m pip install -r /requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

COPY . /app
RUN useradd -ms /bin/bash app && mkdir -m700 /app/uploads && mkdir -m700 /app/temp_uploads &&\
     chown app /app/uploads && chown app /app/temp_uploads

USER app

ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
