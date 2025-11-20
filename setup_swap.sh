#!/bin/bash

# Check if swap file already exists
if [ -f /swapfile ]; then
    echo "Swap file already exists."
else
    echo "Creating 1G swap file..."
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    echo "Swap created and enabled."
fi

# Verify swap
free -h
