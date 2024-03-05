FROM python:3.12-slim-bookworm

ENV LANG=C.UTF-8 \
  LC_ALL=C.UTF-8 \
  PATH="${PATH}:/root/.poetry/bin"

WORKDIR /app/

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock README.md ./
COPY src/ ./src/

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install ; else poetry install --no-dev ; fi"

CMD [ "/usr/local/bin/shrpid" ]

