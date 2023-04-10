FROM python:3.10-alpine

RUN adduser -D alfredo

WORKDIR /home/alfredo

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY bot.py bot_runner.py database.py models.py util.py entrypoint.sh ./

RUN chmod +x entrypoint.sh

RUN chown -R alfredo:alfredo ./

USER alfredo

VOLUME ["/home/alfredo/ext"]

ENTRYPOINT ["./entrypoint.sh"]
