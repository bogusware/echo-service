ARG PYTHON_VERSION="3.12"
ARG DEBIAN_RELEASE="bookworm"
ARG POETRY_VERSION="1.8.5"
###############################################################################
# Base Build Stage
# - Skipped for normal builds as final stage does not depend on it
###############################################################################
FROM python:${PYTHON_VERSION}-${DEBIAN_RELEASE} AS build

ARG POETRY_VERSION

RUN pip install poetry==${POETRY_VERSION}

ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=1 \
  POETRY_VIRTUALENVS_CREATE=1 \
  POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

# NOTE: Cache mount may not work well in CI
RUN --mount=type=cache,target=${POETRY_CACHE_DIR} \
    poetry install \
    --no-root \
    --without dev

COPY src ./src

RUN poetry install --without dev

###############################################################################
# Test Stage
# - Skipped for normal builds as final stage does not depend on it
# - Used for CI/CD to run unit tests
###############################################################################
FROM build AS test

ARG POETRY_VERSION

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN --mount=type=cache,target=${POETRY_CACHE_DIR} \
  poetry install

COPY tests ./tests

ENTRYPOINT ["pytest"]

###############################################################################
# Production Stage
# - minimal production layer
###############################################################################
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_RELEASE}

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY --from=build ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=build /app/src /app/src

EXPOSE 8000
ENTRYPOINT ["uvicorn", "--host", "0.0.0.0", "echo.main:app"]

