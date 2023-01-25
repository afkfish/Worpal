FROM python:3.11-bullseye
ENV python3="/usr/local/bin/python3"
WORKDIR /app
RUN apt update && apt upgrade -y
RUN apt install ffmpeg -y
COPY requirements.txt requirements.txt
RUN LIBSODIUM_MAKE_ARGS=-j4 pip3 install -r requirements.txt
COPY . .
ENTRYPOINT ["python3", "main.py"]