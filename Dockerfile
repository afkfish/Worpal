FROM python:3.11
ENV python3="/usr/local/bin/python3"
WORKDIR /app
COPY requirements.txt requirements.txt
RUN LIBSODIUM_MAKE_ARGS=-j4 pip3 install -r requirements.txt
RUN apt-get install ffmpeg -y
COPY . .
ENTRYPOINT ["python3", "main.py"]