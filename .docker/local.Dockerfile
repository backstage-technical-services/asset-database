FROM python:3.8.6-alpine

ARG USER_ID
ARG GROUP_ID

ENV PIPENV_VENV_IN_PROJECT=1

# Install the system dependencies
RUN apk upgrade \
    && apk add --upgrade \
      bash \
      curl \
      gcc \
      git \
      libffi-dev \
      musl-dev \
      nodejs \
      npm \
      openssl-dev \
      pkgconfig \
      python3-dev \
      mariadb-dev \
    && python3 -m pip install --upgrade pip \
    && pip3 install pipenv \
    && npm install -g yarn \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Recreate the www-data user and group to match that of the host machine's user
RUN if [ ${USER_ID:-0} -ne 0 ] && [ ${GROUP_ID:-0} -ne 0 ]; then \
    if id www-data >/dev/null 2>&1; then deluser --remove-home www-data; fi \
    && if getent group www-data ; then delgroup www-data; fi \
    && if getent group ${GROUP_ID}; then delgroup $(getent group ${GROUP_ID}); fi \
    && addgroup --gid ${GROUP_ID} www-data \
    && adduser -D -u ${USER_ID} -G www-data www-data \
;fi

RUN rm -rf /app \
    && mkdir -p /app \
    && chown -R www-data:www-data /app

# Copy the entrypoint
COPY --chown=www-data:www-data --chmod=755 .docker/bin/entrypoint.local.sh /bin/entrypoint

WORKDIR /app
USER www-data

VOLUME /app
ENTRYPOINT ["/bin/entrypoint"]
CMD ["pipenv", "run", "python3", "manage.py", "runserver", "0.0.0.0:8000"]
