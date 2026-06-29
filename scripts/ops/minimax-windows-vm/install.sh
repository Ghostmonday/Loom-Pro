#!/usr/bin/env bash
# MiniMax AI sandbox — Windows 11 KVM on NVMe (~/VMs/minimax-sandbox).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_ENV="${VM_ENV:-$HOME/VMs/minimax-sandbox/vm.env}"

if [[ ! -f "$VM_ENV" ]]; then
  mkdir -p "$HOME/VMs/minimax-sandbox"
  if [[ -f "$HOME/VMs/minimax-sandbox/vm.env" ]]; then
    VM_ENV="$HOME/VMs/minimax-sandbox/vm.env"
  else
    echo "ERROR: missing $VM_ENV" >&2
    exit 1
  fi
fi
# shellcheck source=/dev/null
source "$VM_ENV"

VM_ROOT="${VM_ROOT:-$HOME/VMs/minimax-sandbox}"
DISK_PATH="${DISK_PATH:-$VM_ROOT/disk/system.qcow2}"
ISO_PATH="${ISO_PATH:-$VM_ROOT/install/Win11_Eval_Enterprise.iso}"
VIRTIO_ISO_PATH="${VIRTIO_ISO_PATH:-$VM_ROOT/install/virtio-win.iso}"
OVMF_VARS_PATH="${OVMF_VARS_PATH:-$VM_ROOT/firmware/OVMF_VARS.fd}"
ISO_URL="${ISO_URL:-https://go.microsoft.com/fwlink/?linkid=2208844}"
VIRTIO_ISO_URL="${VIRTIO_ISO_URL:-https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso}"
SHARE_PATH="${SHARE_PATH:-$VM_ROOT/share}"
TPM_DIR="${TPM_DIR:-$VM_ROOT/state/tpm}"
DISK_GB="${DISK_GB:-80}"
RAM_MB="${RAM_MB:-8192}"
VCPUS="${VCPUS:-4}"

echo "==> MiniMax Windows sandbox"
echo "    Root:  $VM_ROOT  (NVMe ext4 — local I/O)"
echo "    Disk:  $DISK_PATH"
echo "    ISO:   $ISO_PATH"
echo "    RAM:   ${RAM_MB}MB  CPUs: $VCPUS"
echo ""

mkdir -p "$VM_ROOT"/{disk,install,firmware,logs,state,share}
mkdir -p "$TPM_DIR"
mkdir -p "$HOME/.local/bin"

if ! command -v qemu-system-x86_64 >/dev/null 2>&1 || ! command -v swtpm >/dev/null 2>&1; then
  echo "==> Installing KVM/QEMU + TPM emulator (sudo once)..."
  sudo apt-get update
  sudo apt-get install -y \
    qemu-system-x86 qemu-utils cpu-checker ovmf swtpm \
    libvirt-daemon-system libvirt-clients virt-viewer wmctrl \
    wget curl
  sudo usermod -aG kvm,libvirt "$USER"
  echo "!! Log out/in after install so kvm group applies."
fi

if [[ ! -f "$DISK_PATH" ]]; then
  echo "==> Creating qcow2 disk (${DISK_GB}G, thin — grows on use)..."
  qemu-img create -f qcow2 "$DISK_PATH" "${DISK_GB}G"
  qemu-img info "$DISK_PATH"
fi

if [[ ! -f "$ISO_PATH" ]]; then
  echo "==> Downloading Windows 11 Evaluation ISO (~6 GB)..."
  wget -c --progress=bar:force -O "$ISO_PATH" "$ISO_URL"
  echo "==> ISO SHA check (size)..."
  ls -lh "$ISO_PATH"
fi

if [[ ! -f "$VIRTIO_ISO_PATH" ]]; then
  echo "==> Downloading virtio-win drivers ISO (~700 MB)..."
  wget -c --progress=bar:force -O "$VIRTIO_ISO_PATH" "$VIRTIO_ISO_URL"
  ls -lh "$VIRTIO_ISO_PATH"
fi

if [[ ! -f "$OVMF_VARS_PATH" ]]; then
  for template in /usr/share/OVMF/OVMF_VARS_4M.ms.fd /usr/share/OVMF/OVMF_VARS.fd; do
    if [[ -f "$template" ]]; then
      cp "$template" "$OVMF_VARS_PATH"
      echo "==> UEFI vars: $OVMF_VARS_PATH"
      break
    fi
  done
fi

OVMF_CODE=""
for candidate in /usr/share/OVMF/OVMF_CODE_4M.ms.fd /usr/share/OVMF/OVMF_CODE.fd; do
  [[ -f "$candidate" ]] && OVMF_CODE="$candidate" && break
done
if [[ -z "$OVMF_CODE" || ! -f "$OVMF_VARS_PATH" ]]; then
  echo "ERROR: OVMF missing — run: sudo apt install ovmf" >&2
  exit 1
fi

INSTALLER_LAUNCHER="$SCRIPT_DIR/minimax-vm"
TARGET_LAUNCHER="$HOME/.local/bin/minimax-vm"
cp "$INSTALLER_LAUNCHER" "$TARGET_LAUNCHER"
chmod +x "$TARGET_LAUNCHER" "$SCRIPT_DIR/launch-on-monitor2.sh" "$SCRIPT_DIR/integrate.sh"

bash "$SCRIPT_DIR/integrate.sh"

cat > "$VM_ROOT/README.txt" <<EOF
MiniMax Windows sandbox VM
==========================
NVMe path: $VM_ROOT

disk/system.qcow2     — VM disk (virtio-blk, qcow2 thin)
install/*.iso         — Win11 + virtio-win drivers (detach Win11 after setup)
firmware/OVMF_VARS.fd — UEFI NVRAM (per-VM, do not delete)
share/                — host↔guest files (virtio-9p tag: hostshare)
state/tpm/            — software TPM 2.0 state
vm.env                — paths + RAM/CPU (source of truth)
logs/                 — optional QEMU logs

Launch:     minimax-vm
Monitor:    bash $SCRIPT_DIR/launch-on-monitor2.sh
Integrate:  bash $SCRIPT_DIR/integrate.sh

Windows install:
  1) Boot DVD → Win11 ISO
  2) "Where to install" → Load driver → virtio-win → viostor\\w11\\amd64
  3) After OS boots: run share\\windows-postinstall.ps1 (Admin PowerShell)

After Windows install:
  sed -i 's/^FIRST_BOOT=1/FIRST_BOOT=0/' $VM_ENV
EOF

echo ""
echo "==> Ready."
echo "    Config: $VM_ENV"
echo "    Launch: minimax-vm"
echo "    HDMI-2: bash $SCRIPT_DIR/launch-on-monitor2.sh"
echo "    Integrate: bash $SCRIPT_DIR/integrate.sh"