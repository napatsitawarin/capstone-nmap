FROM python:3.9-slim

RUN apt-get update

RUN apt-get install -y nmap

WORKDIR /app

COPY . .

RUN pip3 install -r requirement.txt

EXPOSE 8000

CMD ["python3", "main.py"]