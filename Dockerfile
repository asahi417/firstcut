FROM python:3.6-slim

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  ffmpeg \
  libpq-dev \
  git \
  gcc \
  python-dev \
  build-essential \
  openssh-server \
  libsndfile1 \
  google-perftools && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

ARG PORT
ARG FIREBASE_SERVICE_ACCOUNT
ARG FIREBASE_APIKEY
ARG FIREBASE_AUTHDOMAIN
ARG FIREBASE_DATABASEURL
ARG FIREBASE_STORAGEBUCKET
ARG FIREBASE_PASSWORD
ARG FIREBASE_GMAIL

WORKDIR /opt/app
COPY . /opt/app

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PORT=${PORT} \
    FIREBASE_APIKEY=${FIREBASE_APIKEY} \
    FIREBASE_AUTHDOMAIN=${FIREBASE_AUTHDOMAIN} \
    FIREBASE_DATABASEURL=${FIREBASE_DATABASEURL} \
    FIREBASE_STORAGEBUCKET=${FIREBASE_STORAGEBUCKET} \
    FIREBASE_PASSWORD=${FIREBASE_PASSWORD} \
    FIREBASE_GMAIL=${FIREBASE_GMAIL} \
    FIREBASE_SERVICE_ACCOUNT=${FIREBASE_SERVICE_ACCOUNT}


RUN pip3 install pip==19.1.1
RUN pip3 install --no-cache-dir .

CMD ["python", "api.py"]