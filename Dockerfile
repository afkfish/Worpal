FROM python:3.11-slim AS base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1


FROM base AS dependencies

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN apt update
RUN apt install -y --no-install-recommends gcc
RUN apt install -y git

# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy


FROM base AS runtime

# Install ffmpeg for sound playing
RUN apt install -y ffmpeg

# Copy virtual env from python-deps stage
COPY --from=dependencies /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Create and switch to a new user
RUN useradd --create-home app
WORKDIR /home/app
USER app

# Install application into container
COPY . .

ENTRYPOINT ["python3", "main.py"]