FROM python:3.11-slim

ARG ARTIFACT_FEED=py-packages
ARG ARTIFACT_FEED_TOKEN

WORKDIR /app

RUN mkdir utilities
# RUN apt-get update -y
RUN apt-get update && apt-get dist-upgrade -y

RUN mkdir logs

ENV ARTIFACT_INDEX=https://${ARTIFACT_FEED}:${ARTIFACT_FEED_TOKEN}@pkgs.dev.azure.com/dcl525/_packaging/${ARTIFACT_FEED}/pypi/simple/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --extra-index-url=${ARTIFACT_INDEX}

RUN pip install uvloop
RUN pip install uvicorn

COPY . .

RUN apt-get update && apt-get dist-upgrade -y
EXPOSE 80

CMD ["bash", "startup.sh"]