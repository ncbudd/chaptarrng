#!/usr/bin/env bash
set -euo pipefail

readonly expat_version=2.10.0
readonly expat_sha256=c624ba2998fc65df1163a49641ff3f9ab73138b11641d92c86bee0fb01b1bc7f
readonly expat_url="https://github.com/libexpat/libexpat/releases/download/R_2_10_0/expat-${expat_version}.tar.xz"
readonly work_dir="$(mktemp -d /tmp/chaptarr-expat.XXXXXX)"
trap 'rm -rf "$work_dir"' EXIT

curl --fail --location --silent --show-error "$expat_url" -o "$work_dir/expat.tar.xz"
printf '%s  %s\n' "$expat_sha256" "$work_dir/expat.tar.xz" | sha256sum --check --status || {
    echo "SHA-256 verification failed for $expat_url" >&2
    exit 1
}

tar -xJf "$work_dir/expat.tar.xz" -C "$work_dir"
readonly multiarch="$(dpkg-architecture -qDEB_HOST_MULTIARCH)"
readonly architecture="$(dpkg --print-architecture)"
readonly package_root="$work_dir/package"

(
    cd "$work_dir/expat-${expat_version}"
    ./configure \
        --prefix=/usr \
        --libdir="/usr/lib/${multiarch}" \
        --disable-static \
        --enable-shared
    make -j"$(nproc)"
    make DESTDIR="$work_dir/install" install
)

install -d "$package_root/DEBIAN" "$package_root/usr/lib/${multiarch}" "$package_root/usr/share/doc/libexpat1"
for library in "$work_dir/install/usr/lib/${multiarch}"/libexpat.so.1*; do
    [ -e "$library" ] || continue
    install -D -m 0755 "$library" "$package_root/usr/lib/${multiarch}/$(basename "$library")"
done
test -e "$package_root/usr/lib/${multiarch}/libexpat.so.1"
install -m 0644 "$work_dir/expat-${expat_version}/COPYING" "$package_root/usr/share/doc/libexpat1/copyright"

cat > "$package_root/DEBIAN/control" <<EOF
Package: libexpat1
Version: ${expat_version}-1chaptarr1
Section: libs
Priority: optional
Architecture: ${architecture}
Maintainer: ChaptarrNG build maintainers
Depends: libc6 (>= 2.34)
Description: XML parser shared library built from upstream Expat ${expat_version}
 This package replaces the Ubuntu binary in ChaptarrNG container images with
 the pinned upstream security release while retaining the libexpat1 ABI.
EOF

dpkg-deb --build --root-owner-group "$package_root" /tmp/chaptarr-libexpat1.deb >/dev/null
dpkg-deb --info /tmp/chaptarr-libexpat1.deb | grep -F "Version: ${expat_version}-1chaptarr1"
