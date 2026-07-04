# =============================================================================
# Dockerfile — Production image for the RAG API service
#
# Build:
#   docker build -t rag-service:latest .
#
# Run:
#   docker run --rm -p 8000:8000 --env-file .env rag-service:latest
#
# Design notes:
#   - Multi-stage build: dependencies are resolved/compiled in a throwaway
#     `builder` stage; the final `runtime` stage only contains the venv and
#     application code, keeping the shipped image small and free of
#     build toolchains.
#   - Poetry installs into an in-project virtualenv (`POETRY_VIRTUALENVS_IN_PROJECT`)
#     so the whole dependency tree is a single directory we can copy wholesale
#     into the runtime stage.
#   - Runs as a non-root user (`appuser`) with no shell login.
#   - HEALTHCHECK hits the liveness endpoint defined in routes/health.py.
#   - Base image is `python:3.11-slim` — small attack surface, glibc-based
#     (avoids the musl/grpcio/pydantic-core compatibility issues common with
#     `-alpine` images).
# =============================================================================

ARG PYTHON_VERSION=3.11
ARG POETRY_VERSION=1.8.3


# --------------------------------------------------------------------------- #
# Stage 1: builder — resolve and install dependencies
# --------------------------------------------------------------------------- #
FROM python:${PYTHON_VERSION}-slim AS builder

ARG POETRY_VERSION

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=${POETRY_VERSION} \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_REQUESTS_TIMEOUT=300 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR="/tmp/poetry_cache"

ENV PATH="${POETRY_HOME}/bin:${PATH}"

# System build dependencies needed to compile wheels for packages such as
# tokenizers / sentencepiece / hnswlib that some embedding/reranker libs pull in.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry itself in an isolated location (not the project venv).
RUN curl -sSL https://install.python-poetry.org | python3 - --version "${POETRY_VERSION}"

WORKDIR /app

# Copy only dependency manifests first so dependency installation is cached
# independently of application source-code changes.
COPY pyproject.toml poetry.lock* /app/

# Which optional dependency groups (see pyproject.toml [tool.poetry.extras])
# to install into the image. Override at build time with
# `--build-arg INSTALL_EXTRAS="pdf html"` to ship a smaller image; defaults
# to "all" so every extractor/embedder/reranker backend works out of the box.
ARG INSTALL_EXTRAS=all

# Install only runtime dependencies (no dev/test groups, no the project
# itself yet — `--no-root` skips installing the local package since source
# hasn't been copied in).
RUN --mount=type=cache,target=/tmp/poetry_cache \
    poetry install --only main --extras "${INSTALL_EXTRAS}" --no-root --no-ansi

# Now copy every top-level source package — these are siblings of app/ in
# the repo root, not nested under it, so each must be copied explicitly
# (a single `COPY app /app/app` would silently omit all of them and
# produce an image that crashes on import at runtime).
COPY app /app/app
COPY routes /app/routes
COPY services /app/services
COPY retrieval /app/retrieval
COPY agents /app/agents
COPY tools /app/tools
COPY prompts /app/prompts
COPY security /app/security
COPY pipeline /app/pipeline
COPY db /app/db
COPY tasks /app/tasks
COPY README.md /app/README.md

RUN --mount=type=cache,target=/tmp/poetry_cache \
    poetry install --only main --extras "${INSTALL_EXTRAS}" --no-ansi


# --------------------------------------------------------------------------- #
# Stage 2: runtime — minimal final image
# --------------------------------------------------------------------------- #
FROM python:${PYTHON_VERSION}-slim AS runtime

LABEL org.opencontainers.image.title="rag-service" \
    org.opencontainers.image.description="Production FastAPI RAG service (Qdrant + Redis + Hybrid Search + CRAG + Agents)" \
    org.opencontainers.image.licenses="Proprietary"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    VIRTUAL_ENV="/app/.venv" \
    PATH="/app/.venv/bin:${PATH}" \
    APP_HOME="/app" \
    ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=8000

# Minimal runtime OS packages:
#   - curl: used by HEALTHCHECK below
#   - libgomp1: required at runtime by several embedding/reranker libraries
#     (e.g. faiss, onnxruntime, torch CPU builds)
# tini is used as PID 1 to correctly forward signals (SIGTERM) and reap
# zombie processes, which matters for graceful shutdown under Kubernetes.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 appgroup \
    && useradd --system --uid 1000 --gid appgroup \
    --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR ${APP_HOME}

# Bring over the fully-populated virtualenv and installed packages from the
# builder stage — no compilers or package managers end up in this image.
# Every top-level package is copied explicitly (siblings of app/, not
# nested under it) so nothing is silently left out of the image.
COPY --from=builder --chown=appuser:appgroup /app/.venv ${APP_HOME}/.venv
COPY --from=builder --chown=appuser:appgroup /app/app ${APP_HOME}/app
COPY --from=builder --chown=appuser:appgroup /app/routes ${APP_HOME}/routes
COPY --from=builder --chown=appuser:appgroup /app/services ${APP_HOME}/services
COPY --from=builder --chown=appuser:appgroup /app/retrieval ${APP_HOME}/retrieval
COPY --from=builder --chown=appuser:appgroup /app/agents ${APP_HOME}/agents
COPY --from=builder --chown=appuser:appgroup /app/tools ${APP_HOME}/tools
COPY --from=builder --chown=appuser:appgroup /app/prompts ${APP_HOME}/prompts
COPY --from=builder --chown=appuser:appgroup /app/security ${APP_HOME}/security
COPY --from=builder --chown=appuser:appgroup /app/pipeline ${APP_HOME}/pipeline
COPY --from=builder --chown=appuser:appgroup /app/db ${APP_HOME}/db
COPY --from=builder --chown=appuser:appgroup /app/tasks ${APP_HOME}/tasks
COPY --chown=appuser:appgroup README.md ${APP_HOME}/README.md

# Writable directories the application needs at runtime (logs, local cache,
# BM25 index files). Created here so the non-root user owns them; mount
# volumes over these paths in docker-compose/k8s for persistence.
RUN mkdir -p ${APP_HOME}/logs ${APP_HOME}/data \
    && chown -R appuser:appgroup ${APP_HOME}/logs ${APP_HOME}/data

USER appuser

EXPOSE 8000

# Liveness/readiness is exposed by app/routes/health.py as `/live`.
# Failure here causes the container orchestrator to restart the container.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/live || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]

# Single-process Uvicorn by default; for multi-worker production deployments
# prefer running multiple replicas of this container (one process per
# container) behind a load balancer rather than `--workers N` in-container,
# so health checks and rolling restarts map 1:1 to processes. Override via
# `docker run ... rag-service:latest <cmd>` if a different entrypoint is needed.
CMD ["uvicorn", "app.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--proxy-headers", \
    "--forwarded-allow-ips=*", \
    "--no-server-header", \
    "--timeout-keep-alive", "30"]