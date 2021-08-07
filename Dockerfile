FROM python:3.6-slim

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  ffmpeg \
  libsndfile1

WORKDIR /opt/app
COPY . /opt/app


ARG KEEP_LOG_SEC=1800
ARG MAX_SAMPLE_LENGTH=30000000
ENV KEEP_LOG_SEC=${KEEP_LOG_SEC} \
    MAX_SAMPLE_LENGTH=${MAX_SAMPLE_LENGTH}

RUN pip install pip -U
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]