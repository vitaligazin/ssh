#!/bin/sh
set -e

shutdown() {
    echo "Shutting down..."
    kill -TERM "$SSHD_PID" 2>/dev/null || true
    kill -TERM "$PYTHON_PID" 2>/dev/null || true
    sleep 3
    exit 0
}
trap shutdown TERM

# Host keys in /tmp (accessible with readOnlyRootFS)
mkdir -p /tmp/ssh-hostkeys
if [ ! -f /tmp/ssh-hostkeys/ssh_host_rsa_key ]; then
    ssh-keygen -t rsa -f /tmp/ssh-hostkeys/ssh_host_rsa_key -N ''
    ssh-keygen -t ecdsa -f /tmp/ssh-hostkeys/ssh_host_ecdsa_key -N ''
    ssh-keygen -t ed25519 -f /tmp/ssh-hostkeys/ssh_host_ed25519_key -N ''
fi

# Start sshd (port 2222, user jovyan — from sshd_config)
/usr/sbin/sshd -D -e &
SSHD_PID=$!
sleep 1

if ! kill -0 $SSHD_PID 2>/dev/null; then
    echo "SSH daemon failed to start"
    exit 1
fi

# Start HTTP server in background (shell stays as PID 1 for SIGTERM handling)
python3 /app/http_server.py &
PYTHON_PID=$!

wait
exit $?
