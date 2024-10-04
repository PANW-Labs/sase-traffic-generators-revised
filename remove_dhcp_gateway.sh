#!/bin/bash

# Specify the network interface
INTERFACE="eth0"  # Replace with your interface name

# Get the current default gateway
DEFAULT_GW=$(ip route | grep default | grep $INTERFACE | awk '{print $3}')

# Remove the default gateway if it exists
if [ -n "$DEFAULT_GW" ]; then
    echo "Removing default gateway: $DEFAULT_GW from interface: $INTERFACE"
    sudo ip route del default via $DEFAULT_GW dev $INTERFACE
else
    echo "No default gateway found for interface: $INTERFACE"
fi
