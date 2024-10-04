#!/bin/bash

# Get the interface name (in this case, ens192)
INTERFACE="ens192"

# Get the DHCP-assigned gateway IP
GATEWAY=$(ip route show | grep "default via" | awk '{print $3}')

echo "Current DHCP-assigned gateway: $GATEWAY"

# Check if a gateway was found
if [[ -n "$GATEWAY" ]]; then
    echo "Removing DHCP-assigned gateway: $GATEWAY"
    # Remove the gateway
    sudo ip route del default via "$GATEWAY" dev "$INTERFACE"
    
    # Verify if the route was removed
    if ! ip route show | grep -q "default via $GATEWAY"; then
        echo "Successfully removed the gateway."
    else
        echo "Failed to remove the gateway."
    fi
    
    # Optionally flush the route to ensure it gets removed
    sudo ip route flush table main
else
    echo "No DHCP-assigned gateway found for interface $INTERFACE."
fi
