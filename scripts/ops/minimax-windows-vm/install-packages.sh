#!/usr/bin/env bash
# One-time host packages — run in YOUR terminal (needs sudo password).
set -euo pipefail
sudo apt-get update
sudo apt-get install -y \
  qemu-system-x86 qemu-utils cpu-checker ovmf swtpm \
  libvirt-daemon-system libvirt-clients virt-viewer wmctrl \
  wget curl
# Ubuntu 24.10+ / Resolute: qemu-kvm is virtual — qemu-system-x86 provides KVM.
# Optional HWE build if host kernel is HWE: qemu-system-x86-hwe
sudo usermod -aG kvm,libvirt "$USER"
echo ""
echo "DONE. Next (copy one line at a time):"
echo "  1) Log out and back in (kvm group)"
echo "  2) bash ~/Desktop/Gaijinn/scripts/ops/minimax-windows-vm/install.sh"