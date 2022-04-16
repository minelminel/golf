FROM python

RUN python3 -m pip install --upgrade pip wheel setuptools
# RUN apt-get update && apt-get install -y netcat
WORKDIR /tmp
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt && rm requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_ENVIRONMENT=docker

WORKDIR /src
COPY . .
EXPOSE 4000
# ENTRYPOINT ["./docker-entrypoint.sh"]