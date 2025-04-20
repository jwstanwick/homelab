#!/bin/bash

# Check if username, password, and hostname are provided
if [ $# -ne 3 ]; then
    echo "Usage: $0 <username> <password> <hostname_or_ip>"
    exit 1
fi

USERNAME=$1
PASSWORD=$2
HOSTNAME=$3

# Generate SSH key if it doesn't exist
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "Generating SSH key..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
fi

# Add host to known_hosts
echo "Adding host to known_hosts..."
ssh-keyscan -H $HOSTNAME >> ~/.ssh/known_hosts 2>/dev/null

# Configure SSH config
echo "Configuring SSH config..."
cat > ~/.ssh/config << EOF
Host $HOSTNAME
    HostName $HOSTNAME
    User $USERNAME
    IdentityFile ~/.ssh/id_rsa
EOF

# Copy public key to remote host
echo "Copying public key to remote host..."
sshpass -p "$PASSWORD" ssh-copy-id -i ~/.ssh/id_rsa.pub $USERNAME@$HOSTNAME

echo "Setup complete! You can now use 'ssh $HOSTNAME' to connect."
