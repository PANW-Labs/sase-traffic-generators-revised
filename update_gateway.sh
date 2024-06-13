#!/bin/bash

# Update the script header to accept arguments
script_path="$1"
gateway="$2"

while true; do
  if [[ -f "$script_path" ]]; then
    # Use the passed script_path
    if [[ ! -z "${gateway}" ]]; then
      echo "Found valid gateway: ${gateway}"
      python3 "$(dirname "$script_path")"/create_traffic_services.py "${gateway}"
      break
    fi
  else
    echo "Waiting for valid gateway..."
    sleep 10
  fi
done
