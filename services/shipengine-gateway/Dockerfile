FROM azureks.azurecr.io/base/pybase:v2

WORKDIR /app
RUN mkdir logs

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

RUN apt-get update && apt-get dist-upgrade -y
EXPOSE 80

CMD ["bash", "startup.sh"]
