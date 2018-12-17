FROM python:3

WORKDIR /app
COPY . /app

RUN pip3 install -r requirements.txt

RUN rm -Rf venv
RUN mkdir logs

CMD python ./jinny_remind.py
