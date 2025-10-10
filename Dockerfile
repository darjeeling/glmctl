

ARG CLAUDE_CODE_VERSION=latest
# 1. 최신 LTS 베이스 이미지 설정 (ubuntu:24.04)
FROM ubuntu:24.04

# 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive

# 2. 시스템 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    curl \
    git \
    wget \
    tmux \
    python3 \
    python3-pip \
    python3-venv \
    gpg \
    ca-certificates \
    tmux \
    less \
    git \
    procps \
    sudo \
    fzf \
    zsh \
    man-db \
    unzip \
    gnupg2 \
    gh \
    iptables \
    ipset \
    iproute2 \
    dnsutils \
    aggregate \
    jq \
    nano \
    vim \
    && rm -rf /var/lib/apt/lists/*



ARG GIT_DELTA_VERSION=0.18.2
RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  sudo dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  rm "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"

# 3. GitHub CLI (gh) 설치
RUN mkdir -p -m 755 /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && mkdir -p -m 755 /etc/apt/sources.list.d \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& apt update \
	&& apt install gh -y

# 4. Node.js 및 npm 설치 (nvm 사용)
ENV NVM_DIR=/usr/local/nvm
ENV NODE_VERSION=22.20.0
RUN mkdir -p $NVM_DIR && \
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash && \
    . $NVM_DIR/nvm.sh && \
    nvm install $NODE_VERSION && \
    nvm alias default $NODE_VERSION && \
    nvm use default
ENV PATH="$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH"

# 5. Claude Code 설치
RUN npm install -g @anthropic-ai/claude-code
RUN mkdir ~/.claude/

# 6. Rust 설치 (rustup 사용)
ENV RUSTUP_HOME=/usr/local/rustup
ENV CARGO_HOME=/usr/local/cargo
ENV PATH="/usr/local/cargo/bin:$PATH"
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# 7. uv 설치
ENV UV_HOME=/usr/local/uv
ENV PATH="/usr/local/uv/bin:$PATH"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Docker CLI 설치
RUN apt-get update && apt-get install -y ca-certificates curl && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli

# Set the default editor and visual
ENV EDITOR=nano
ENV VISUAL=nano

# TODO
# install some mcp tools
# like
# https://github.com/BeaconBay/ck

# install mcp - ck - Semantic Code Search
# https://github.com/BeaconBay/ck
RUN cargo install ck-search

# Set the default editor and visual
ENV EDITOR=nano
ENV VISUAL=nano

# 8. 작업 디렉토리 설정
WORKDIR /workspace


# 9. 컨테이너 시작 시 tmux 세션 자동 실행 (옵션)
# CMD ["claude","--dangerously-skip-permissions"]
