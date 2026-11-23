#!/usr/bin/env bash
# Render assets/wallpapers/*.svg to 3840x2160 PNGs inside an Ubuntu Docker
# container (needs librsvg + JetBrains Mono Nerd Font, which the host may not have).
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
python3 "$HERE/scripts/gen-wallpapers.py"
python3 "$HERE/scripts/gen-wallpapers2.py"
python3 "$HERE/scripts/gen-wallpapers3.py"
python3 "$HERE/scripts/gen-wallpapers-kali.py"
python3 "$HERE/scripts/gen-icon-themes.py"
mkdir -p "$HERE/.cache/apt-render" "$HERE/.cache/fonts"
docker run --rm -v "$HERE:/af" -v "$HERE/.cache/apt-render:/var/cache/apt/archives" \
  docker.io/library/ubuntu:noble bash -c '
    set -e
    rm -f /etc/apt/apt.conf.d/docker-clean
    apt-get update -qq && apt-get install -y -qq --no-install-recommends librsvg2-bin fontconfig curl ca-certificates xz-utils >/dev/null
    f=/af/.cache/fonts/JetBrainsMono.tar.xz
    [ -f "$f" ] || curl -fsSL -o "$f" https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.tar.xz
    mkdir -p /usr/local/share/fonts/jb && tar -xJf "$f" -C /usr/local/share/fonts/jb --wildcards "*.ttf" && fc-cache -f >/dev/null
    mkdir -p /af/assets/wallpapers/png
    for f in /af/assets/wallpapers/af-*.svg; do
      n=$(basename "$f" .svg); echo "render $n"
      rsvg-convert -w 3840 -h 2160 "$f" -o "/af/assets/wallpapers/png/$n.png"
    done
    for f in /af/assets/icon-themes/preview-*.svg; do [ -f "$f" ] && rsvg-convert "$f" -o "${f%.svg}.png"; done
    chown -R '"$(id -u):$(id -g)"' /af/assets/wallpapers/png /af/.cache/fonts'
echo "PNGs in $HERE/assets/wallpapers/png"
