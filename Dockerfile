FROM python:3.11-bullseye
ENV python3="/usr/local/bin/python3"
WORKDIR /app
RUN apt update
RUN apt install ffmpeg -y
COPY . .
RUN pip3 install pipenv
RUN pipenv install
ENTRYPOINT ["pipenv", "run", "python3", "main.py"]