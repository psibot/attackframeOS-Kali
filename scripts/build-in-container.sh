#!/usr/bin/env bash
# Runs inside the kali-rolling container started by build.sh.
#
#   1. debootstrap a Kali root filesystem, install GNOME + live-boot, and the
#      curated Kali tools natively (Kali IS the host OS in this edition)
#   2. overlay the AttackFrame files (profile/airootfs) and branding
#   3. build the BlackArch layer image on the host's Docker daemon (socket
#      mounted by docker-compose.yml) and save it into the rootfs
#   4. squash it and wrap it in a hybrid BIOS/UEFI GRUB ISO (Debian live layout)
set -euo pipefail

AF=/af
WORK=/work
ROOT=$WORK/rootfs
ISO=$WORK/iso
SUITE=${KALI_SUITE:-kali-rolling}
MIRROR=${KALI_MIRROR:-http://http.kali.org/kali}
TOOLSET=${TOOLSET:-core}
KERNEL_PKG=${KERNEL_PKG:-linux-image-amd64}
IMGDIR=$ROOT/usr/share/attackframe/images
export DEBIAN_FRONTEND=noninteractive

log()  { printf '\e[1;36m[AF]\e[0m %s\n' "$*" >&2; }
warn() { printf '\e[1;35m[AF:warn]\e[0m %s\n' "$*" >&2; }
die()  { printf '\e[1;31m[AF:error]\e[0m %s\n' "$*" >&2; exit 1; }

in_chroot() { chroot "$ROOT" /usr/bin/env -i HOME=/root TERM="${TERM:-xterm}" LC_ALL=C.UTF-8 \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin DEBIAN_FRONTEND=noninteractive "$@"; }

MOUNTS=()
bind() { mkdir -p "$2"; mount "${@:3}" --bind "$1" "$2"; MOUNTS+=("$2"); }
unmount_all() {
  local i
  for ((i=${#MOUNTS[@]}-1; i>=0; i--)); do umount -lf "${MOUNTS[i]}" 2>/dev/null || true; done
  MOUNTS=()
  # anything left behind by an earlier aborted run
  local m
  for m in $(awk -v r="$ROOT" '$2 == r || index($2, r "/") == 1 {print $2}' /proc/mounts | sort -r); do
    umount -lf "$m" 2>/dev/null || true
  done
  return 0
}
trap unmount_all EXIT

# Strip comments/blank lines, keep names that exist in the chroot's apt repos.
# resolve_apt <missing-log> <list...>
resolve_apt() {
  local miss=$1; shift
  local p pol found=() missing=()
  while read -r p; do
    p=${p%%#*}; p=${p//[[:space:]]/}
    [[ -z $p ]] && continue
    # no pipe into grep -q here: under pipefail its early exit (SIGPIPE) reads as "missing"
    pol=$(in_chroot apt-cache policy "$p" 2>/dev/null || true)
    if [[ $pol == *"Candidate: "* && $pol != *"Candidate: (none)"* ]]; then found+=("$p"); else missing+=("$p"); fi
  done < <(cat "$@")
  if ((${#missing[@]})); then
    warn "not in $SUITE, skipped: ${missing[*]}"
    printf '%s\n' "${missing[@]}" >> "$miss"
  fi
  printf '%s\n' "${found[@]}" | sort -u
}

# apt install that survives one bad package: batch first, then one by one
apt_install_list() {   # apt_install_list <resolved-list> <failed-log>
  # shellcheck disable=SC2046
  if ! in_chroot apt-get -y install --no-install-recommends $(cat "$1"); then
    warn "batch install failed — retrying package by package"
    in_chroot apt-get -y -f install || true
    local p
    while read -r p; do
      in_chroot apt-get -y install --no-install-recommends "$p" || { warn "failed: $p"; echo "$p" >> "$2"; }
    done < "$1"
  fi
}

# ======================================================================= toolchain
log "Installing build toolchain"
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
  debootstrap kali-archive-keyring squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin grub-common mtools \
  dosfstools librsvg2-bin fontconfig curl ca-certificates xz-utils openssl \
  docker-cli docker-buildx >/dev/null 2>&1 \
|| apt-get install -y -qq --no-install-recommends \
  debootstrap kali-archive-keyring squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin grub-common mtools \
  dosfstools librsvg2-bin fontconfig curl ca-certificates xz-utils openssl \
  docker.io docker-buildx >/dev/null
if [[ $TOOLSET != minimal ]] && ! docker info >/dev/null 2>&1; then
  die "can't reach the host Docker daemon — is /var/run/docker.sock mounted? (run ./build.sh, not this script)"
fi

# JetBrains Mono Nerd Font — needed for rendering artwork and shipped in the image
FONTS=$AF/.cache/fonts
mkdir -p "$FONTS"
if [[ ! -f $FONTS/JetBrainsMono.tar.xz ]]; then
  log "Downloading JetBrains Mono Nerd Font"
  curl -fsSL -o "$FONTS/JetBrainsMono.tar.xz" \
    https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.tar.xz \
    || warn "could not download the Nerd Font; artwork falls back to other fonts"
fi
if [[ -f $FONTS/JetBrainsMono.tar.xz ]]; then
  mkdir -p /usr/local/share/fonts/jetbrains-nerd
  tar -xJf "$FONTS/JetBrainsMono.tar.xz" -C /usr/local/share/fonts/jetbrains-nerd --wildcards '*.ttf'
  fc-cache -f >/dev/null
fi

# ======================================================================= rootfs
log "Preparing work area"
unmount_all
rm -rf "$ROOT" "$ISO" "$WORK/ctx-"*
mkdir -p "$ROOT" "$ISO"

log "debootstrap kali:$SUITE (this takes a few minutes)"
mkdir -p "$AF/.cache/kali-debootstrap"
debootstrap --arch=amd64 --components=main,contrib,non-free,non-free-firmware \
  --keyring=/usr/share/keyrings/kali-archive-keyring.gpg \
  --include=kali-archive-keyring,ca-certificates \
  --cache-dir="$AF/.cache/kali-debootstrap" "$SUITE" "$ROOT" "$MIRROR"

bind /dev "$ROOT/dev"
bind /dev/pts "$ROOT/dev/pts"
mount -t proc proc "$ROOT/proc";  MOUNTS+=("$ROOT/proc")
mount -t sysfs sys "$ROOT/sys";   MOUNTS+=("$ROOT/sys")
mount -t tmpfs tmpfs "$ROOT/run"; MOUNTS+=("$ROOT/run")
mkdir -p "$AF/.cache/kali-apt/partial"
bind "$AF/.cache/kali-apt" "$ROOT/var/cache/apt/archives"

# real resolv.conf while building; emptied at the end (NetworkManager owns it on Kali)
rm -f "$ROOT/etc/resolv.conf"; cp -L /etc/resolv.conf "$ROOT/etc/resolv.conf"
# don't start services inside the chroot
printf '#!/bin/sh\nexit 101\n' > "$ROOT/usr/sbin/policy-rc.d"; chmod +x "$ROOT/usr/sbin/policy-rc.d"
echo attackframe > "$ROOT/etc/hostname"
printf '127.0.0.1 localhost\n127.0.1.1 attackframe\n::1 localhost ip6-localhost ip6-loopback\n' > "$ROOT/etc/hosts"

log "Configuring apt sources"
rm -f "$ROOT/etc/apt/sources.list.d/"*.sources
echo "deb $MIRROR $SUITE main contrib non-free non-free-firmware" > "$ROOT/etc/apt/sources.list"

in_chroot apt-get update -qq
in_chroot apt-get -y -qq full-upgrade
in_chroot apt-get -y -qq install --no-install-recommends ca-certificates locales apt-utils debconf-utils
sed -i 's/^# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' "$ROOT/etc/locale.gen"
in_chroot locale-gen >/dev/null
in_chroot update-locale LANG=en_US.UTF-8

# answers for the tool packages that ask questions on install
in_chroot debconf-set-selections <<'EOF'
wireshark-common wireshark-common/install-setuid boolean true
kismet-capture-common kismet-capture-common/install-setuid boolean true
kismet-capture-common kismet-capture-common/install-users string
macchanger macchanger/automatically_run boolean false
sslh sslh/inetd_or_standalone select standalone
console-setup console-setup/charmap47 select UTF-8
keyboard-configuration keyboard-configuration/layoutcode string us
EOF

# ======================================================================= packages
mkdir -p "$ROOT/usr/share/attackframe"
SKIPPED=$ROOT/usr/share/attackframe/kali-skipped.txt
FAILED=$ROOT/usr/share/attackframe/kali-failed.txt
: > "$SKIPPED"; : > "$FAILED"

log "Resolving the system package lists (kernel: $KERNEL_PKG)"
pkgs=$(mktemp)
{ echo "$KERNEL_PKG"; cat "$AF/packages/base.txt" "$AF/packages/desktop.txt"; } > "$pkgs.in"
resolve_apt "$SKIPPED" "$pkgs.in" > "$pkgs"
(( $(wc -l < "$pkgs") >= 50 )) || die "only $(wc -l < "$pkgs") packages resolved — apt in the chroot is broken (check the mirror / sources)"
log "$(wc -l < "$pkgs") system packages selected — installing"
apt_install_list "$pkgs" "$FAILED"
cp "$pkgs" "$ROOT/usr/share/attackframe/packages.txt"

# Kali tools, natively on the host (no Kali container in this edition)
if [[ $TOOLSET == minimal ]]; then
  log "TOOLSET=minimal: no Kali tools baked in (attackframe-kali setup core installs them)"
else
  kali_meta=${KALI_META:-}
  [[ $TOOLSET == large ]] && kali_meta=${kali_meta:-kali-linux-default}
  tools=$(mktemp)
  { cat "$AF/packages/kali-core.txt"; [[ -n $kali_meta ]] && tr ' ' '\n' <<< "$kali_meta"; true; } > "$tools.in"
  resolve_apt "$SKIPPED" "$tools.in" > "$tools"
  log "Installing $(wc -l < "$tools") Kali tool packages natively (large download, be patient)"
  if [[ -n $kali_meta ]]; then
    # metapackages are useless without their recommends
    # shellcheck disable=SC2046
    in_chroot apt-get -y install $(cat "$tools") || apt_install_list "$tools" "$FAILED"
  else
    apt_install_list "$tools" "$FAILED"
  fi
  cat "$tools" >> "$ROOT/usr/share/attackframe/packages.txt"
fi
[[ -s $FAILED ]] && warn "packages that failed to install: $(tr '\n' ' ' < "$FAILED")"

# ======================================================================= overlay
log "Applying AttackFrame overlay"
cp -rT "$AF/profile/airootfs" "$ROOT"
# leftovers from the Arch / Ubuntu / Podman builds, not used on Kali.
# `kali` (the old box wrapper) goes too: Kali tools are native here.
rm -rf "$ROOT/etc/pacman.d" "$ROOT/etc/systemd/system/attackframe-resolv.service" \
       "$ROOT/usr/local/bin/attackframe-gem-retry" "$ROOT/usr/local/bin/attackframe-postinstall" \
       "$ROOT/usr/local/bin/kali" \
       "$ROOT/etc/sudoers.d/attackframe-podman" "$ROOT/etc/containers/storage.conf"
chmod 755 "$ROOT"/usr/local/bin/*
# AttackFrame zsh profile (kept as a non-dot file in the repo; it replaces skel/.zshrc)
if [[ -f $ROOT/usr/share/attackframe/zshrc ]]; then
  mv -f "$ROOT/usr/share/attackframe/zshrc" "$ROOT/usr/share/attackframe/skel/.zshrc"
fi
find "$ROOT/etc/sudoers.d" -name 'attackframe-*' -exec chmod 440 {} + 2>/dev/null || true
install -Dm644 "$AF/packages/kali-core.txt" "$ROOT/usr/share/attackframe/kali-core.txt"
install -Dm644 "$AF/packages/blackarch-core.txt" "$ROOT/usr/share/attackframe/blackarch-core.txt"
if [[ -d /usr/local/share/fonts/jetbrains-nerd ]]; then
  mkdir -p "$ROOT/usr/local/share/fonts"
  cp -r /usr/local/share/fonts/jetbrains-nerd "$ROOT/usr/local/share/fonts/"
  in_chroot fc-cache -f >/dev/null || true
fi

# identity: our os-release, diverted so base-files upgrades keep it.
# ID_LIKE keeps kali first so Kali-aware tooling still recognises the system.
# shellcheck disable=SC1091
VERSION_ID=$(. "$ROOT/usr/lib/os-release"; echo "${VERSION_ID:-rolling}")
in_chroot dpkg-divert --quiet --local --no-rename --divert /usr/lib/os-release.distrib --add /usr/lib/os-release
cat > "$ROOT/usr/lib/os-release" <<EOF
NAME="AttackFrame OS"
PRETTY_NAME="AttackFrame OS (Kali $VERSION_ID)"
ID=attackframe
ID_LIKE="kali debian"
VERSION="$VERSION_ID"
VERSION_ID="$VERSION_ID"
VERSION_CODENAME=kali-rolling
ANSI_COLOR="38;2;0;240;255"
HOME_URL="https://github.com/"
LOGO=attackframe
EOF
ln -sf ../usr/lib/os-release "$ROOT/etc/os-release"

# live session: live-config creates the operator account (autologin, passwordless sudo).
# The same values are on the kernel command line in grub.cfg; this file is the fallback.
mkdir -p "$ROOT/etc/live/config.conf.d"
cat > "$ROOT/etc/live/config.conf.d/attackframe.conf" <<'EOF'
LIVE_HOSTNAME="attackframe"
LIVE_USERNAME="ghost"
LIVE_USER_FULLNAME="AttackFrame Operator"
LIVE_USER_DEFAULT_GROUPS="audio cdrom dip floppy video plugdev netdev powerdev scanner bluetooth sudo docker wireshark kaboxer dialout"
EOF
# live user's password (LIVE_PASSWORD, default "ghost"): stored only as a SHA-512
# crypt hash, applied by attackframe-firstboot after live-config creates the user
install -d -m 755 "$ROOT/etc/attackframe"
printf '%s' "${LIVE_PASSWORD:-ghost}" | openssl passwd -6 -stdin > "$ROOT/etc/attackframe/live-password.hash"
chmod 600 "$ROOT/etc/attackframe/live-password.hash"
log "live login: ghost / $( [[ ${LIVE_PASSWORD:-ghost} == ghost ]] && echo ghost || echo '<LIVE_PASSWORD>' )"

# new users get zsh and the operator profile; .hushlogin silences Kali's
# "minimal installation" notice and the Debian legal MOTD at login
touch "$ROOT/usr/share/attackframe/skel/.hushlogin"
: > "$ROOT/etc/motd"
cp -rT "$ROOT/usr/share/attackframe/skel" "$ROOT/etc/skel"
sed -i 's#^\#\?DSHELL=.*#DSHELL=/usr/bin/zsh#' "$ROOT/etc/adduser.conf" 2>/dev/null || true
sed -i 's#^\#\? *SHELL=.*#SHELL=/usr/bin/zsh#' "$ROOT/etc/default/useradd" 2>/dev/null || true

# NetworkManager manages everything (ifupdown keeps only lo)
mkdir -p "$ROOT/etc/NetworkManager/conf.d" "$ROOT/etc/network"
printf 'auto lo\niface lo inet loopback\n' > "$ROOT/etc/network/interfaces"
printf '[main]\nplugins=ifupdown,keyfile\n\n[ifupdown]\nmanaged=true\n\n[keyfile]\nunmanaged-devices=none\n' \
  > "$ROOT/etc/NetworkManager/conf.d/10-attackframe.conf"

in_chroot systemctl enable attackframe-firstboot.service NetworkManager.service >/dev/null
in_chroot systemctl enable docker.service >/dev/null 2>&1 || true
in_chroot systemctl set-default graphical.target >/dev/null
in_chroot glib-compile-schemas /usr/share/glib-2.0/schemas
in_chroot dconf update || true

# ======================================================================= branding
log "Rendering artwork"
bgdir=$ROOT/usr/share/backgrounds/attackframe
mkdir -p "$bgdir" "$ROOT/usr/share/gnome-background-properties" "$ROOT/usr/share/icons/hicolor/scalable/apps"
install -Dm644 "$AF/assets/gdm-logo.svg" "$ROOT/usr/share/attackframe/gdm-logo.svg"
rsvg-convert -w 3840 -h 2160 "$AF/assets/wallpaper.svg" -o "$bgdir/attackframe-grid.png"
xml=$ROOT/usr/share/gnome-background-properties/attackframe.xml
wp() { printf '  <wallpaper deleted="false"><name>%s</name><filename>%s</filename><filename-dark>%s</filename-dark><options>zoom</options><shade_type>solid</shade_type><pcolor>#05070d</pcolor><scolor>#05070d</scolor></wallpaper>\n' "$1" "$2" "$2"; }
{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">'
  echo '<wallpapers>'
  wp "AttackFrame Grid" /usr/share/backgrounds/attackframe/attackframe-grid.png
  while IFS=$'\t' read -r slug name; do
    [[ -z $slug ]] && continue
    if [[ -f $AF/assets/wallpapers/png/$slug.png ]]; then
      cp "$AF/assets/wallpapers/png/$slug.png" "$bgdir/$slug.png"
    else
      rsvg-convert -w 3840 -h 2160 "$AF/assets/wallpapers/$slug.svg" -o "$bgdir/$slug.png"
    fi
    wp "AttackFrame $name" "/usr/share/backgrounds/attackframe/$slug.png"
  done < "$AF/assets/wallpapers/names.tsv"
  echo '</wallpapers>'
} > "$xml"
cp "$AF"/assets/icons/*.svg "$ROOT/usr/share/icons/hicolor/scalable/apps/"
cp -r "$AF"/assets/icon-themes/AttackFrame-* "$ROOT/usr/share/icons/"
for d in "$ROOT"/usr/share/icons/hicolor "$ROOT"/usr/share/icons/AttackFrame-*; do
  in_chroot gtk-update-icon-cache -qf "/usr/share/icons/${d##*/icons/}" 2>/dev/null || true
done

# boot splash: an AttackFrame plymouth theme (two-step spinner with our logo)
if [[ -d $ROOT/usr/share/plymouth/themes/spinner ]]; then
  pt=$ROOT/usr/share/plymouth/themes/attackframe
  rm -rf "$pt"; cp -r "$ROOT/usr/share/plymouth/themes/spinner" "$pt"
  mv "$pt/spinner.plymouth" "$pt/attackframe.plymouth"
  sed -i 's/^Name=.*/Name=AttackFrame/; s#/themes/spinner#/themes/attackframe#g; s/^BackgroundStartColor=.*/BackgroundStartColor=0x05070d/; s/^BackgroundEndColor=.*/BackgroundEndColor=0x05070d/' \
    "$pt/attackframe.plymouth"
  rsvg-convert -h 64 "$AF/assets/gdm-logo.svg" -o "$pt/watermark.png"
  in_chroot plymouth-set-default-theme attackframe || warn "could not set the plymouth theme"
fi
printf 'AttackFrame OS \\n \\l\n\n' > "$ROOT/etc/issue"
echo 'AttackFrame OS' > "$ROOT/etc/issue.net"

# the initramfs carries live-boot and the splash: regenerate it now
log "Regenerating the initramfs"
in_chroot update-initramfs -u -k all

# ======================================================================= BlackArch layer
mkdir -p "$IMGDIR" "$ROOT/var/lib/attackframe"

if [[ $TOOLSET == minimal ]]; then
  log "TOOLSET=minimal: no BlackArch image baked in; it is pulled on first use"
else
  ba_groups=""; [[ $TOOLSET == large ]] && ba_groups=$BA_GROUPS
  ctx=$WORK/ctx-blackarch
  mkdir -p "$ctx"
  cp "$AF/containers/blackarch/Containerfile" "$ctx/"
  cp "$AF/packages/blackarch-core.txt" "$ctx/packages.txt"
  log "Building the BlackArch layer image (large download, be patient)"
  docker build --network host --pull -f "$ctx/Containerfile" -t attackframe/blackarch:latest \
    --build-arg BASE="$BLACKARCH_BASE" --build-arg STRAP_SHA1="${STRAP_SHA1:-}" --build-arg GROUPS="$ba_groups" \
    "$ctx"

  # which grid tools the image provides → shims in /usr/local/bin (native Kali tools win)
  log "Indexing BlackArch binaries for app-grid shims"
  mapfile -t tsv_bins < <(awk -F'\t' '!/^#/ && NF>=5 {split($5,a," "); print a[1]}' \
    "$ROOT/usr/share/attackframe/tools.tsv" | sort -u)
  docker run --rm --network none --entrypoint sh attackframe/blackarch:latest \
    -c 'for b; do command -v "$b" >/dev/null 2>&1 && echo "$b"; done; true' _ "${tsv_bins[@]}" \
    | tr -d '\r' | sort -u > "$ROOT/var/lib/attackframe/bins-blackarch.txt"
  log "BlackArch layer: $(wc -l < "$ROOT/var/lib/attackframe/bins-blackarch.txt") grid tools"
  log "Saving the BlackArch image into the ISO"
  docker save -o "$IMGDIR/blackarch.tar" attackframe/blackarch:latest
  chmod 644 "$IMGDIR/blackarch.tar"   # docker load reads it client-side, as the user
  bash "$ROOT/usr/local/bin/attackframe-box" sync --root "$ROOT"
fi

# ======================================================================= finalize rootfs
log "Finalising root filesystem"
in_chroot apt-get -y autoremove --purge >/dev/null || true
in_chroot apt-get clean
unmount_all
rm -f "$ROOT/usr/sbin/policy-rc.d"
rm -rf "$ROOT"/tmp/* "$ROOT"/var/lib/apt/lists/* "$ROOT"/root/.bash_history
rm -f "$ROOT/etc/resolv.conf"; : > "$ROOT/etc/resolv.conf"   # NetworkManager writes it at runtime
: > "$ROOT/etc/machine-id"; rm -f "$ROOT/var/lib/dbus/machine-id"

# ======================================================================= ISO tree
log "Building ISO tree"
mkdir -p "$ISO/live" "$ISO/boot/grub" "$ISO/.disk" "$WORK/grub"
kver=$(find "$ROOT/boot" -maxdepth 1 -name 'vmlinuz-*' -printf '%f\n' | sed 's/^vmlinuz-//' | sort -V | tail -1)
[[ -n $kver ]] || die "no kernel found in the root filesystem"
cp "$ROOT/boot/vmlinuz-$kver" "$ISO/live/vmlinuz"
cp "$ROOT/boot/initrd.img-$kver" "$ISO/live/initrd.img"
chroot "$ROOT" dpkg-query -W --showformat='${Package} ${Version}\n' > "$ISO/live/filesystem.packages"
du -sx --block-size=1 "$ROOT" | cut -f1 > "$ISO/live/filesystem.size"
echo "AttackFrame OS $(date +%Y.%m.%d) - kali $SUITE amd64" > "$ISO/.disk/info"
touch "$ISO/attackframe"

log "Squashing the root filesystem (zstd -$SQUASHFS_LEVEL)"
mksquashfs "$ROOT" "$ISO/live/filesystem.squashfs" -noappend -comp zstd \
  -Xcompression-level "${SQUASHFS_LEVEL:-15}" -b 1M -wildcards \
  -e 'proc/*' 'sys/*' 'dev/*' 'run/*' 'tmp/*' 'var/cache/apt/archives/*.deb'

rsvg-convert -w 1920 -h 1080 "$AF/assets/splash.svg" -o "$ISO/boot/grub/splash.png" || true

LIVE_ARGS="boot=live components hostname=attackframe username=ghost"
cat > "$WORK/grub/grub.cfg" <<EOF
search --no-floppy --set=root --file /attackframe
# graphical splash on UEFI; legacy BIOS stays in text mode (core image size limit)
if [ "\$grub_platform" = "efi" ]; then
  insmod all_video
  insmod gfxterm
  insmod gfxterm_background
  insmod png
  if loadfont unicode ; then
    set gfxmode=auto
    terminal_output gfxterm
    background_image /boot/grub/splash.png
  fi
fi
set menu_color_normal=light-cyan/black
set menu_color_highlight=black/light-cyan
set color_normal=light-cyan/black
set default=0
set timeout=8

menuentry "AttackFrame OS  //  live" {
  linux /live/vmlinuz $LIVE_ARGS quiet splash
  initrd /live/initrd.img
}
menuentry "AttackFrame OS  //  live (copy to RAM)" {
  linux /live/vmlinuz $LIVE_ARGS toram quiet splash
  initrd /live/initrd.img
}
menuentry "AttackFrame OS  //  live (persistence: 'persistence' partition)" {
  linux /live/vmlinuz $LIVE_ARGS persistence quiet splash
  initrd /live/initrd.img
}
menuentry "AttackFrame OS  //  live (forensic: no swap, no automount)" {
  linux /live/vmlinuz $LIVE_ARGS noswap noautomount
  initrd /live/initrd.img
}
menuentry "AttackFrame OS  //  live (safe graphics)" {
  linux /live/vmlinuz $LIVE_ARGS nomodeset
  initrd /live/initrd.img
}
if [ "\$grub_platform" = "efi" ]; then
  menuentry "UEFI firmware settings" { fwsetup }
fi
EOF
cp "$WORK/grub/grub.cfg" "$ISO/boot/grub/grub.cfg"

log "Building GRUB (BIOS + UEFI)"
# Kali's kernel isn't signed for Secure Boot, so UEFI uses our own standalone GRUB
# (turn Secure Boot off in the firmware to boot the ISO or an installed system).
grub-mkstandalone --format=x86_64-efi --output="$WORK/grub/bootx64.efi" \
  --locales="" --fonts="unicode" "boot/grub/grub.cfg=$WORK/grub/grub.cfg"
efi=$WORK/grub/efi; rm -rf "$efi"; mkdir -p "$efi"
cp "$WORK/grub/bootx64.efi" "$efi/BOOTX64.EFI"
mkdir -p "$ISO/boot/grub/fonts"
cp /usr/share/grub/unicode.pf2 "$ISO/boot/grub/fonts/" 2>/dev/null || true
rm -f "$WORK/grub/efiboot.img"
dd if=/dev/zero of="$WORK/grub/efiboot.img" bs=1M count=16 status=none
mkfs.vfat -F 16 -n AF_EFI "$WORK/grub/efiboot.img" >/dev/null
LC_CTYPE=C mmd -i "$WORK/grub/efiboot.img" ::/EFI ::/EFI/BOOT
for f in "$efi"/*; do LC_CTYPE=C mcopy -i "$WORK/grub/efiboot.img" "$f" "::/EFI/BOOT/${f##*/}"; done

bios_mods="linux linux16 normal iso9660 biosdisk memdisk search search_fs_file tar ls configfile echo test part_msdos part_gpt"
grub-mkstandalone --format=i386-pc --output="$WORK/grub/core.img" \
  --install-modules="$bios_mods" --modules="linux normal iso9660 biosdisk search" \
  --locales="" --fonts="" "boot/grub/grub.cfg=$WORK/grub/grub.cfg"
cat /usr/lib/grub/i386-pc/cdboot.img "$WORK/grub/core.img" > "$WORK/grub/bios.img"

# plain EFI/BOOT tree too, for USB writers that copy files instead of dd-ing the image
mkdir -p "$ISO/EFI/BOOT"
cp "$efi"/* "$ISO/EFI/BOOT/"

(cd "$ISO" && find . -type f ! -name md5sum.txt ! -path './live/filesystem.squashfs' -print0 \
  | xargs -0 md5sum > md5sum.txt)

OUTISO=$AF/out/attackframe-kali-$(date +%Y.%m.%d)-amd64.iso
log "Writing $OUTISO"
xorriso -as mkisofs -iso-level 3 -full-iso9660-filenames -joliet -joliet-long -rational-rock \
  -volid "ATTACKFRAME" -output "$OUTISO" \
  -eltorito-boot boot/grub/bios.img -no-emul-boot -boot-load-size 4 -boot-info-table \
  --eltorito-catalog boot/grub/boot.cat --grub2-boot-info \
  --grub2-mbr /usr/lib/grub/i386-pc/boot_hybrid.img \
  -eltorito-alt-boot -e EFI/efiboot.img -no-emul-boot \
  -append_partition 2 0xef "$WORK/grub/efiboot.img" \
  -graft-points "/EFI/efiboot.img=$WORK/grub/efiboot.img" "/boot/grub/bios.img=$WORK/grub/bios.img" "$ISO"

(cd "$AF/out" && sha256sum "$(basename "$OUTISO")" > "$(basename "$OUTISO").sha256")
chown -R "${HOST_UID:-0}:${HOST_GID:-0}" "$AF/out" "$AF/.cache" 2>/dev/null || true

# ======================================================================= sanity
[[ -s $ROOT/etc/ssl/certs/ca-certificates.crt ]] || warn "CA bundle missing in the image — HTTPS will fail"
[[ $TOOLSET == minimal ]] || [[ -s $IMGDIR/blackarch.tar ]] || warn "BlackArch image missing from the ISO"
[[ -f $ROOT/usr/share/backgrounds/attackframe/af-kali-blue-horizon.png ]] || warn "default wallpaper af-kali-blue-horizon.png missing"
grep -q af-kali-blue-horizon "$ROOT/etc/dconf/db/local.d/00-attackframe" 2>/dev/null || warn "dconf default wallpaper not set"
[[ $TOOLSET == minimal ]] || [[ -x $ROOT/usr/bin/nmap ]] || warn "nmap missing — did the Kali tool install fail?"
[[ -x $ROOT/usr/lib/user-setup/user-setup-apply ]] || warn "user-setup missing — live-config won't create ghost (firstboot will)"
log "Done: $OUTISO ($(du -h "$OUTISO" | cut -f1))"
