FROM python:3.8.6-alpine AS base

FROM base AS python-requirements

WORKDIR /app
COPY Pipfile.lock ./
RUN python3 -m pip install --upgrade pip && \
    pip3 install pipenv && \
    pipenv requirements > requirements.txt

FROM node:lts AS node-deps

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM base

# Install the system dependencies
RUN apk upgrade && apk add --upgrade \
    curl \
    bash \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    pkgconfig \
    mariadb-dev

# Install rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy the entrypoint
COPY .docker/bin/entrypoint.sh /bin/entrypoint
RUN chmod +x /bin/entrypoint

WORKDIR /app

# Install python dependencies
COPY --from=python-requirements /app/requirements.txt requirements.txt
RUN pip install -r requirements.txt && \
    rm requirements.txt

# Add node dependencies
COPY --from=node-deps /app/node_modules node_modules

# Copy source code
COPY bts_asset_db/ ./bts_asset_db/
COPY bts_core/ ./bts_core/
COPY data/ ./data/
COPY utilities/ ./utilities/
COPY manage.py ./

VOLUME /app/data
ENTRYPOINT ["/bin/entrypoint"]
CMD ["python3", "manage.py", "runserver", "--noreload", "0.0.0.0:8000"]
