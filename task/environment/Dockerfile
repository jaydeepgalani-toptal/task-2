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
    && python -m pip install --no-cache-dir requests beautifulsoup4 packaging pytest==8.4.1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash agent

COPY payload/project /workspace
COPY payload/forum /opt/localforum

RUN chmod +x /workspace/bin/download-mods \
    && chmod +x /opt/localforum/forum_serverctl \
    && ln -sf /opt/localforum/forum_serverctl /usr/local/bin/forum-serverctl \
    && cp /opt/localforum/forum_env.sh /etc/profile.d/forum_env.sh \
    && python /opt/localforum/generate_forum_assets.py \
    && python /opt/localforum/sanity_check.py \
    && python /opt/localforum/build_manifest.py \
    && chown -R agent:agent /workspace

WORKDIR /workspace
USER agent
