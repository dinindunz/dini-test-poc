# Use OpenJDK 17 as base image for development
FROM openjdk:17-jdk-slim

# Install sudo since it's not preinstalled in minimal Ubuntu images
RUN apt-get update -y && apt-get install -y sudo

# Create a user named 'dev-container' with a home directory and set its default shell
RUN useradd -m -s /bin/bash dev-container \
    && mkdir -p /home/dev-container \
    && chown -R dev-container:dev-container /home/dev-container

# Allow 'dev-container' user to run sudo commands without a password
RUN echo "dev-container ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install system dependencies and update apt
RUN apt-get update -y && \
    apt-get install -y \
    zsh \
    curl \
    jq \
    unzip \
    git \
    git-lfs \
    gcc \
    g++ \
    make \
    tar \
    libc6 \
    maven \
    wget \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    && apt-get clean

# Download and install Python 3.13.5
RUN cd /tmp && \
    wget https://www.python.org/ftp/python/3.13.5/Python-3.13.5.tgz && \
    tar xzf Python-3.13.5.tgz && \
    cd Python-3.13.5 && \
    ./configure --enable-optimizations && \
    make -j $(nproc) && \
    make altinstall && \
    cd / && \
    rm -rf /tmp/Python-3.13.5* && \
    ln -s /usr/local/bin/python3.13 /usr/local/bin/python3 && \
    ln -s /usr/local/bin/pip3.13 /usr/local/bin/pip3

# Install AWS CLI with architecture detection
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        AWS_CLI_ARCH="x86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        AWS_CLI_ARCH="aarch64"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_CLI_ARCH}.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && ./aws/install && rm -rf awscliv2.zip aws

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    chmod +x /usr/local/bin/uv

# Install Node.js 18
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g @anthropic-ai/claude-code && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Create workspaces directory and clone the repository
RUN mkdir -p /workspaces && \
    git clone https://github.com/johnhuang316/code-index-mcp.git /workspaces/code-index-mcp && \
    chown -R dev-container:dev-container /workspaces

# Switch to the 'dev-container' user to set up Oh-My-Zsh and its plugins
USER dev-container

# Set environment variables
ENV JAVA_HOME=/usr/local/openjdk-17
ENV PATH=$JAVA_HOME/bin:$PATH

# Oh-my-zsh & plugins
ARG ZSH_PATH=/home/dev-container/.oh-my-zsh/custom
ARG PLUGINS="aws ansible docker zsh-syntax-highlighting colored-man-pages zsh-autosuggestions"

RUN curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh | bash || true && \
    mkdir -p $ZSH_PATH/plugins && \
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_PATH/plugins/zsh-autosuggestions" && \
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_PATH/plugins/zsh-syntax-highlighting" && \
    git clone https://github.com/spaceship-prompt/spaceship-prompt.git "$ZSH_PATH/themes/spaceship-prompt" --depth=1 && \
    ln -s "$ZSH_PATH/themes/spaceship-prompt/spaceship.zsh-theme" "$ZSH_PATH/themes/spaceship.zsh-theme" && \
    sed -i '/^ZSH_THEME/c\ZSH_THEME="spaceship"' /home/dev-container/.zshrc && \
    sed -i '/^plugins=(/ s/)$/ '"$PLUGINS"')/' /home/dev-container/.zshrc
