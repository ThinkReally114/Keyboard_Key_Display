#!/bin/bash
set -e

PACKAGE_NAME="keyboard-key-display"
VERSION="0.0.1"
ARCH="all"
MAINTAINER="ThinkReally <2507164880@qq.com>"
DESCRIPTION="Linux desktop keyboard key display application"

BUILD_DIR="build_deb"
DEB_DIR="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}"

rm -rf "${BUILD_DIR}" *.deb

mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/usr/share/${PACKAGE_NAME}"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/share/applications"
mkdir -p "${DEB_DIR}/usr/share/polkit-1/actions"
mkdir -p "${DEB_DIR}/usr/lib/${PACKAGE_NAME}"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"

cp key_display.py "${DEB_DIR}/usr/share/${PACKAGE_NAME}/"
cp config.json "${DEB_DIR}/usr/share/${PACKAGE_NAME}/"
cp -r icons "${DEB_DIR}/usr/share/${PACKAGE_NAME}/" 2>/dev/null || true

cat > "${DEB_DIR}/usr/lib/${PACKAGE_NAME}/grant-input-read.sh" << 'EOF'
#!/bin/bash
set -e

for device in /dev/input/event*; do
    [ -e "$device" ] || continue
    chmod a+r "$device" || true
done
EOF
chmod +x "${DEB_DIR}/usr/lib/${PACKAGE_NAME}/grant-input-read.sh"

cat > "${DEB_DIR}/usr/bin/${PACKAGE_NAME}" << 'EOF'
#!/bin/bash
set -e

APP_DIR="/usr/share/keyboard-key-display"
APP_FILE="${APP_DIR}/key_display.py"
HELPER="/usr/lib/keyboard-key-display/grant-input-read.sh"

can_read_input() {
    for device in /dev/input/event*; do
        [ -e "$device" ] || continue
        [ -r "$device" ] && return 0
    done
    return 1
}

if ! can_read_input; then
    if command -v pkexec >/dev/null 2>&1; then
        pkexec "$HELPER"
    else
        x-terminal-emulator -e bash -c "echo 'Keyboard input permission is required.'; echo 'Please run: sudo chmod a+r /dev/input/event*'; read -p 'Press Enter to exit...'"
        exit 1
    fi
fi

if ! can_read_input; then
    notify-send "Keyboard Key Display" "Permission denied. Run: sudo chmod a+r /dev/input/event*" 2>/dev/null || true
    exit 1
fi

cd "$APP_DIR"
exec /usr/bin/python3 "$APP_FILE" "$@"
EOF
chmod +x "${DEB_DIR}/usr/bin/${PACKAGE_NAME}"

cat > "${DEB_DIR}/usr/share/polkit-1/actions/com.keyboard-key-display.policy" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <vendor>Keyboard Key Display</vendor>
  <vendor_url>https://github.com/ThinkReally114/Keyboard_Key_Display</vendor_url>

  <action id="com.keyboard-key-display.grant-input-read">
    <description>Grant keyboard input read permission</description>
    <message>Keyboard Key Display needs permission to read keyboard input devices</message>
    <defaults>
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>auth_admin</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/lib/keyboard-key-display/grant-input-read.sh</annotate>
  </action>
</policyconfig>
EOF

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

cat > "${DEB_DIR}/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-tk
Recommends: policykit-1
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 A Linux desktop keyboard key display application that shows
 pressed keys on screen with a visual keyboard layout.
EOF

cat > "${DEB_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo "=== Keyboard Key Display installed ==="
echo "The application may ask for your password once to grant /dev/input read permission."
echo "Security note: this allows local users to read input event devices until reboot or permission reset."

exit 0
EOF
chmod +x "${DEB_DIR}/DEBIAN/postinst"

cat > "${DEB_DIR}/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e
exit 0
EOF
chmod +x "${DEB_DIR}/DEBIAN/postrm"

dpkg-deb --build "${DEB_DIR}"
mv "${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" .
rm -rf "${BUILD_DIR}"

echo "Build complete: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
exit 0
