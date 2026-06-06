#!/bin/bash
set -e

PACKAGE_NAME="keyboard-key-display"
VERSION="1.0.0"
ARCH="all"
MAINTAINER="Your Name <your.email@example.com>"
DESCRIPTION="Linux desktop keyboard key display application"

BUILD_DIR="build_deb"
DEB_DIR="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}"

rm -rf "${BUILD_DIR}" *.deb

mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/usr/share/${PACKAGE_NAME}"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/share/applications"
mkdir -p "${DEB_DIR}/etc/udev/rules.d"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"

cp key_display.py "${DEB_DIR}/usr/share/${PACKAGE_NAME}/"
cp config.json "${DEB_DIR}/usr/share/${PACKAGE_NAME}/"
cp -r icons "${DEB_DIR}/usr/share/${PACKAGE_NAME}/" 2>/dev/null || true

# Launcher - no sudo needed after udev rule is installed
cat > "${DEB_DIR}/usr/bin/${PACKAGE_NAME}" << 'EOF'
#!/bin/bash

APP_DIR="/usr/share/keyboard-key-display"

cd "$APP_DIR"
exec /usr/bin/python3 key_display.py "$@"
EOF
chmod +x "${DEB_DIR}/usr/bin/${PACKAGE_NAME}"

# udev rule: make all input event devices readable by everyone
cat > "${DEB_DIR}/etc/udev/rules.d/99-keyboard-key-display.rules" << 'EOF'
# Allow keyboard-key-display to read input events without root
SUBSYSTEM=="input", KERNEL=="event*", MODE="0644"
EOF

# Desktop entry
cat > "${DEB_DIR}/usr/share/applications/${PACKAGE_NAME}.desktop" << EOF
[Desktop Entry]
Name=Keyboard Key Display
Comment=Display keyboard keys on screen
Exec=${PACKAGE_NAME}
Type=Application
Terminal=false
Categories=Utility;Accessibility;
Icon=${PACKAGE_NAME}
EOF

# Control file
cat > "${DEB_DIR}/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-tk
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 A Linux desktop keyboard key display application that shows
 pressed keys on screen with a visual keyboard layout.
EOF

# Post-install: apply udev rule immediately
cat > "${DEB_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo "=== Keyboard Key Display installed ==="

# Reload udev rules and apply immediately
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger --subsystem-match=input 2>/dev/null || true
fi

# Also set current permissions right now
chmod a+r /dev/input/event* 2>/dev/null || true

echo "Keyboard input devices are now readable by all users."
echo "This will persist across reboots via udev rule."
echo "To undo: sudo rm /etc/udev/rules.d/99-keyboard-key-display.rules"

exit 0
EOF
chmod +x "${DEB_DIR}/DEBIAN/postinst"

# Pre-removal: clean up udev rule
cat > "${DEB_DIR}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    rm -f /etc/udev/rules.d/99-keyboard-key-display.rules 2>/dev/null || true
    udevadm control --reload-rules 2>/dev/null || true
fi

exit 0
EOF
chmod +x "${DEB_DIR}/DEBIAN/prerm"

# Build
dpkg-deb --build "${DEB_DIR}"
mv "${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" .
rm -rf "${BUILD_DIR}"

echo "Build complete: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
exit 0

