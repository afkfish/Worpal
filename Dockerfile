FROM python:3.11-bullseye
ENV python3="/usr/local/bin/python3"
WORKDIR /app
RUN apt update
RUN apt install ffmpeg -y
RUN pip3 install pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install
COPY . .
ENTRYPOINT ["pipenv", "run", "python3", "main.py"]