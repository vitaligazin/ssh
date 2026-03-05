# =============================================================================
# SSH-enabled base image (non-root, key-only). For serverless/Knative with SSH.
# User: jovyan (platform default ssh_user). Port: 2222.
# =============================================================================
FROM debian:bookworm-slim

LABEL org.opencontainers.image.title="SSH non-root base (ssh + sshd)" \
      org.opencontainers.image.description="Debian with OpenSSH client (ssh) and server (sshd), key-only, HTTP probe for Knative" \
      org.opencontainers.image.source="https://git.sbercloud.tech/products/SERVERLESS/backend"

ENV SSH_AUTHORIZED_KEYS_FILE=/etc/ssh/authorized_keys \
    SSH_HOSTKEY_DIR=/tmp/ssh-hostkeys

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    openssh-client \
    netcat-openbsd \
    python3 \
    openssl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 -s /bin/sh jovyan && \
    mkdir -p /home/jovyan/.ssh /run/sshd && \
    chmod 700 /home/jovyan/.ssh && \
    chown -R jovyan:jovyan /home/jovyan/.ssh && \
    usermod -p "$(openssl passwd -6 -salt $(openssl rand -hex 4) $(openssl rand -base64 24))" jovyan

# Host keys are generated at startup in entrypoint (in /tmp, accessible with readOnlyRootFS).
RUN printf '%s\n' \
    'PidFile /tmp/sshd.pid' \
    'Port 2222' \
    'AddressFamily inet' \
    'ListenAddress 0.0.0.0' \
    'HostKey /tmp/ssh-hostkeys/ssh_host_rsa_key' \
    'HostKey /tmp/ssh-hostkeys/ssh_host_ecdsa_key' \
    'HostKey /tmp/ssh-hostkeys/ssh_host_ed25519_key' \
    'PubkeyAuthentication yes' \
    'PasswordAuthentication no' \
    'UsePAM no' \
    'KbdInteractiveAuthentication no' \
    'PermitRootLogin no' \
    'AllowUsers jovyan' \
    'AuthorizedKeysFile /etc/ssh/authorized_keys' \
    'Subsystem sftp internal-sftp' \
    'ClientAliveInterval 60' \
    'ClientAliveCountMax 3' \
    'AllowTcpForwarding remote' \
    > /etc/ssh/sshd_config

RUN mkdir -p /app
COPY entrypoint.sh /entrypoint.sh
COPY app/http_server.py /app/http_server.py
RUN chmod +x /entrypoint.sh

EXPOSE 2222 8080

ENTRYPOINT ["/entrypoint.sh"]
