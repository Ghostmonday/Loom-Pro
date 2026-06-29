#!/usr/bin/env bash
# Stage MiniMax + Hermes integration files into the VM shared folder.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_ENV="${VM_ENV:-$HOME/VMs/minimax-sandbox/vm.env}"
[[ -f "$VM_ENV" ]] || { echo "Missing $VM_ENV — run install.sh first" >&2; exit 1; }
# shellcheck source=/dev/null
source "$VM_ENV"

SHARE_PATH="${SHARE_PATH:-$VM_ROOT/share}"
mkdir -p "$SHARE_PATH"

cp "$SCRIPT_DIR/windows-postinstall.ps1" "$SHARE_PATH/"
chmod +x "$SHARE_PATH/windows-postinstall.ps1" 2>/dev/null || true

if [[ -f "$HOME/.mmx/config.json" ]]; then
  cp "$HOME/.mmx/config.json" "$SHARE_PATH/mmx-config.json"
  echo "==> Copied mmx config → $SHARE_PATH/mmx-config.json"
else
  echo "WARN: no ~/.mmx/config.json — run 'mmx auth login' on Linux host first" >&2
fi

if [[ -f "$HOME/Desktop/Gaijinn/project.executor-profile.json" ]]; then
  cp "$HOME/Desktop/Gaijinn/project.executor-profile.json" "$SHARE_PATH/"
fi

cat > "$SHARE_PATH/README.txt" <<'EOF'
MiniMax Windows sandbox — host share (virtio-9p tag: hostshare)
================================================================

Inside Windows (after virtio-9p driver is installed):
  1. Open Device Manager → Other devices → "VirtIO FS Device" → Update driver
  2. Browse virtio-win CD → vioscsi\w11\amd64 (or NetKVM for network first)
  3. Map share: from elevated PowerShell run windows-postinstall.ps1

Or mount manually:
  net use Z: \\hostshare

Then in PowerShell (Admin):
  Set-ExecutionPolicy Bypass -Scope Process -Force
  Z:\windows-postinstall.ps1

After Windows is installed on the VM, on Linux host:
  sed -i 's/^FIRST_BOOT=1/FIRST_BOOT=0/' ~/VMs/minimax-sandbox/vm.env
EOF

echo ""
echo "==> Integration bundle staged at: $SHARE_PATH"
echo "    Launch VM: minimax-vm"
echo "    In Windows (Admin PowerShell):"
echo "      Set-ExecutionPolicy Bypass -Scope Process -Force"
echo "      .\\windows-postinstall.ps1   # from mapped hostshare drive"
echo ""
ls -la "$SHARE_PATH"