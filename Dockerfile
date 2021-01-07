FROM python:3.7

RUN mkdir /telegram
WORKDIR /telegram
ADD . /telegram/
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "/telegram/telegram.py"]
