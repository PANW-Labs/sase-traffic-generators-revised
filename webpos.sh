#!/bin/bash

# Function to get the IP address for a given domain
function getIpAddress() {
  local domain_name="$1"

  if [[ -z "$domain_name" ]]; then
    echo "Domain name is required"
    return 1
  fi

  # 1. Check host file for IP (faster)
  IP_FROM_HOSTFILE=$(grep "$domain_name" /etc/hosts | awk '{print $1}' | head -1)

  if [[ -n "$IP_FROM_HOSTFILE" ]]; then
    echo "$IP_FROM_HOSTFILE"
    return 0
  fi

  # 2. Fallback to DNS resolution if not found in host file
  IP_FROM_DNS=$(getent ahosts "$domain_name" | grep -Eo '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | head -1)

  if [[ -n "$IP_FROM_DNS" ]]; then
    echo "$IP_FROM_DNS"
    return 0
  fi

  echo "IP address not found for $domain_name"
  return 1
}

# Function to get the reachable interface for a given IP.
# Retries up to MAX_RETRIES times (1 s apart) then returns failure —
# prevents an infinite subprocess-spawning loop when the route is absent.
function getReachableInterface() {
  local ip_address="$1"
  local MAX_RETRIES=60
  local attempt=0

  if [[ -z "$ip_address" ]]; then
    echo "Invalid IP address"
    return 1
  fi

  while (( attempt < MAX_RETRIES )); do
    local iface
    iface=$(ip route get "$ip_address" 2>/dev/null | awk '/dev/{for(i=1;i<=NF;i++) if($i=="dev") print $(i+1)}')
    if [[ -n "$iface" ]]; then
      echo "$iface"
      return 0
    fi
    (( attempt++ ))
    sleep 1
  done

  echo "No route to $ip_address after $MAX_RETRIES attempts"
  return 1
}

# Fetch a batch of URLs through curl using a single persistent connection per
# host.  Chaining URLs with --next lets curl reuse the TCP connection across
# requests to the same host, preventing TIME_WAIT socket accumulation in the
# kernel.  --keepalive-time holds the connection open between requests.
# Results are discarded; only the exit status matters.
function fetchBatch() {
  local interface="$1"
  local host="$2"
  local count="$3"
  local path1="${4:-/}"
  local path2="${5:-/}"

  local args=( --interface "$interface" --keepalive-time 30 -sL -m 15 -o /dev/null )

  # Build a single curl invocation with alternating --next pairs so the
  # connection is reused across all count iterations.
  local cmd=( curl "${args[@]}" "http://${host}${path1}" )
  for (( i = 2; i <= count; i++ )); do
    cmd+=( --next "${args[@]}" "http://${host}${path2}" )
  done

  "${cmd[@]}"
}

# Main script logic

TARGET_HOST="${1:-webpos.sasedemo.net}"
echo "Target host: $TARGET_HOST"

IP_ADDRESS=$(getIpAddress "$TARGET_HOST")
if [[ $? -ne 0 ]]; then
  echo "Failed to retrieve IP address for $TARGET_HOST. Exiting."
  exit 1
fi
echo "IP Address for $TARGET_HOST: $IP_ADDRESS"

REACHABLE_INTERFACE=$(getReachableInterface "$IP_ADDRESS")
if [[ $? -ne 0 ]]; then
  echo "No reachable interface found for $TARGET_HOST. Exiting."
  exit 1
fi
echo "Reachable Interface: $REACHABLE_INTERFACE"

while true; do
  # Re-resolve the interface each outer iteration so route changes (DHCP
  # renewal, failover) are picked up without restarting the service.
  CURRENT_INTERFACE=$(getReachableInterface "$IP_ADDRESS")
  if [[ $? -eq 0 && -n "$CURRENT_INTERFACE" ]]; then
    REACHABLE_INTERFACE="$CURRENT_INTERFACE"
  fi
  INTERFACE="$REACHABLE_INTERFACE"

  # Random batch sizes kept within tighter bounds to avoid thousands of
  # simultaneous TIME_WAIT sockets from back-to-back curl launches.
  t=$(( RANDOM % 40 + 20 ))   # 20–59  (was 60–700)
  x=$(( RANDOM % 30 + 10 ))   # 10–39  (was 600–900)

  echo "Phase 1: $t CGI requests via $INTERFACE"
  # Single curl process chains /cgi-bin/get_env.py → /cgi-bin/hw.sh for each
  # iteration, reusing the TCP connection — no TIME_WAIT per request.
  fetchBatch "$INTERFACE" "$TARGET_HOST" "$t" \
    "/cgi-bin/get_env.py" "/cgi-bin/hw.sh"

  # Pause between phases lets the kernel drain TIME_WAIT sockets.
  sleep 5

  echo "Phase 2: $x root requests via $INTERFACE"
  fetchBatch "$INTERFACE" "$TARGET_HOST" "$x" "/" "/"

  sleep 31
done