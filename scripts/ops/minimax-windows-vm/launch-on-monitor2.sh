#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_ENV="${VM_ENV:-$HOME/VMs/minimax-sandbox/vm.env}"

minimax-vm &
sleep 4

# HDMI-2 is top monitor @ 0,0 per xrandr (1920x1080)
if command -v wmctrl >/dev/null 2>&1; then
  for _ in 1 2 3 4 5; do
    ID=$(wmctrl -l | grep -iE 'QEMU|minimax' | awk '{print $1}' | head -1)
    [[ -n "$ID" ]] && wmctrl -i -r "$ID" -e 0,0,0,1920,1080 && break
    sleep 1
  done
  echo "VM window → HDMI-2 (0,0). F11 for fullscreen inside guest view."
else
  echo "VM started — drag window to top monitor. Optional: sudo apt install wmctrl"
fi

wait