FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends curl ca-certificates ripgrep tmux asciinema wget unzip \
    && curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash \
    && . "$HOME/.nvm/nvm.sh" && nvm install 22 \
    && npm install -g @openai/codex@latest \
    && ln -sf "$(which node)" /usr/local/bin/node \
    && ln -sf "$(which codex)" /usr/local/bin/codex \
    && python -m pip install --no-cache-dir pyyaml python-dateutil pytest \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash agent

COPY payload/etl_project /workspace/etl
COPY payload/etl_support /opt/etl_support

RUN mkdir -p /workspace/etl/data/vendor_exports /workspace/etl/out \
    && python /opt/etl_support/generate_inputs.py \
    && python -m pip install --no-cache-dir -e /workspace/etl \
    && python /opt/etl_support/sanity_check.py \
    && python /opt/etl_support/build_manifest.py \
    && chmod +x /workspace/etl/bin/run-load \
    && chown -R agent:agent /workspace/etl

WORKDIR /workspace/etl
USER agent
