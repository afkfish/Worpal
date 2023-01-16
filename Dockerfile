FROM python:3.11-slim
ENV python3="/usr/local/bin/python3"
WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install python3-dev \
                                      gcc \
                                      make \
                                      libc-dev \
                                      libffi-dev -y
RUN LIBSODIUM_MAKE_ARGS=-j4 pip3 install -r requirements.txt
RUN apt-get install ffmpeg -y
COPY . .
ENTRYPOINT ["python3", "main.py"]