#!/usr/bin/env bash
set -euo pipefail

readonly bubblewrap_version=0.13.1
readonly bubblewrap_sha256=0e85c8702248b8dd64144f594147553650cdd0e4c951690345faace79c217c4d
readonly lame_version=4.0
readonly lame_sha256=3df5124d5ad3a98312ffd7ba6a9b36230e4f8a3e66d3ce0f425e336c32d216eb
readonly ffmpeg_version=9.0.2
readonly ffmpeg_sha256=8c3850283eb25fa026482078a04051e0be17347b09ef81a0849bec15a96e002e
readonly m4b_tool_default_url=https://github.com/sandreas/m4b-tool/releases/download/v0.5.2/m4b-tool.phar
readonly m4b_tool_default_sha256=a3ea9b81a4e8ce10ecc85c1fc712c982ba2622f2ed0318fb558dadfad4a590fa
readonly work_dir="$(mktemp -d /tmp/chaptarr-hardened-tools.XXXXXX)"
trap 'rm -rf "$work_dir"' EXIT

download_verified() {
    local url="$1"
    local sha256="$2"
    local output="$3"

    curl --fail --location --silent --show-error "$url" -o "$output"
    printf '%s  %s\n' "$sha256" "$output" | sha256sum --check --status || {
        echo "SHA-256 verification failed for $url" >&2
        exit 1
    }
}

download_verified \
    "https://github.com/containers/bubblewrap/releases/download/v${bubblewrap_version}/bubblewrap-${bubblewrap_version}.tar.xz" \
    "$bubblewrap_sha256" \
    "$work_dir/bubblewrap.tar.xz"
tar -xJf "$work_dir/bubblewrap.tar.xz" -C "$work_dir"
meson setup "$work_dir/bubblewrap-build" "$work_dir/bubblewrap-${bubblewrap_version}" \
    --prefix=/usr/local \
    --buildtype=release \
    -Dman=disabled \
    -Dtests=false \
    -Dselinux=enabled \
    -Dbash_completion=disabled \
    -Dzsh_completion=disabled
meson compile --jobs "$(nproc)" -C "$work_dir/bubblewrap-build"
meson install -C "$work_dir/bubblewrap-build"
bwrap --version

download_verified \
    "https://downloads.sourceforge.net/project/lame/lame/${lame_version}/lame-${lame_version}.tar.gz" \
    "$lame_sha256" \
    "$work_dir/lame.tar.gz"
tar -xzf "$work_dir/lame.tar.gz" -C "$work_dir"
(
    cd "$work_dir/lame-${lame_version}"
    ./configure \
        --prefix=/usr/local \
        --disable-decoder \
        --disable-frontend \
        --enable-shared \
        --disable-static
    make -j"$(nproc)"
    make install
    install -Dm644 LICENSE /usr/local/share/licenses/lame/LICENSE
    install -Dm644 COPYING /usr/local/share/licenses/lame/COPYING
)
ldconfig

download_verified \
    "https://ffmpeg.org/releases/ffmpeg-${ffmpeg_version}.tar.xz" \
    "$ffmpeg_sha256" \
    "$work_dir/ffmpeg.tar.xz"
tar -xJf "$work_dir/ffmpeg.tar.xz" -C "$work_dir"
(
    cd "$work_dir/ffmpeg-${ffmpeg_version}"
    ./configure \
        --prefix=/usr/local \
        --disable-debug \
        --disable-doc \
        --disable-ffplay \
        --disable-network \
        --enable-libmp3lame
    make -j"$(nproc)"
    make install
)

ldconfig
ldd /usr/local/bin/ffmpeg | grep -F 'libmp3lame.so.0 => /usr/local/lib/libmp3lame.so.0'
ffmpeg -hide_banner -version
ffmpeg -hide_banner -h encoder=aac >/dev/null
ffmpeg -hide_banner -h encoder=libmp3lame >/dev/null
ffmpeg -hide_banner -h demuxer=matroska >/dev/null
ffmpeg -hide_banner -f lavfi -i sine=frequency=1000:duration=1 -c:a aac -b:a 96k -f ipod "$work_dir/smoke.m4a" -y
ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1 "$work_dir/smoke.m4a" | grep -F 'format_name=mov,mp4,m4a'
ffmpeg -hide_banner -f lavfi -i sine=frequency=1000:duration=1 -c:a libmp3lame -q:a 5 "$work_dir/smoke.mp3" -y
ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1 "$work_dir/smoke.mp3" | grep -F 'format_name=mp3'

m4b_tool_url=${M4B_TOOL_URL:-$m4b_tool_default_url}
m4b_tool_sha256=${M4B_TOOL_SHA256:-$m4b_tool_default_sha256}
download_verified "$m4b_tool_url" "$m4b_tool_sha256" "$work_dir/m4b-tool.phar"
install -m 0755 "$work_dir/m4b-tool.phar" /usr/local/bin/m4b-tool
