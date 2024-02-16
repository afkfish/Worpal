FROM python:3.12 AS base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1


FROM base AS pipenv

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN apt update

# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy


FROM python:3.12-slim AS runtime

# install runtime dependencies
RUN apt update
RUN apt install -y ffmpeg

# Copy virtual env from python-deps stage
COPY --from=pipenv /.venv /.venv
ENV PATH="/.venv/bin:$PATH"
ARG dotenv=""
ENV DOTENV_KEY=${dotenv}

# Create and switch to a new user
RUN useradd --create-home app
WORKDIR /home/app
USER app

# Install application into container
COPY . .

ENTRYPOINT ["python3", "-O", "main.py"]