#!/bin/bash
set -e

# Package info
PACKAGE_NAME="keyboard-key-display"
VERSION="1.0.0"
ARCH="all"
MAINTAINER="Your Name <your.email@example.com>"
DESCRIPTION="Linux desktop keyboard key display application"

# Build directories
BUILD_DIR="build_deb"
DEB_DIR="${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}"

# Clean previous build
rm -rf "${BUILD_DIR}" *.deb

# Create directory structure
mkdir -p "${DEB_DIR}/DEBIAN"
mkdir -p "${DEB_DIR}/usr/share/${PACKAGE_NAME}"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/share/applications"
mkdir -p "${DEB_DIR}/usr/share/polkit-1/actions"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"

# Copy application files
cp key_display.py "${DEB_DIR}/usr/share/${PACKAGE_NAME}/"
cp config.json "${DEB_DIR}/usr/share/${PACKAGE_NAME}/"
cp -r icons "${DEB_DIR}/usr/share/${PACKAGE_NAME}/" 2>/dev/null || true

# Create privileged helper. It only grants device read permission, not launch GUI as root.
cat > "${DEB_DIR}/usr/share/${PACKAGE_NAME}/grant-input-access.sh" << 'EOF'
#!/bin/bash
set -e

TARGET_USER="$1"

if [ -z "$TARGET_USER" ]; then
    echo "Missing target user" >&2
    exit 1
fi

if ! id "$TARGET_USER" >/dev/null 2>&1; then
    echo "Invalid user: $TARGET_USER" >&2
    exit 1
fi

for device in /dev/input/event*; do
    [ -e "$device" ] || continue
    if command -v setfacl >/dev/null 2>&1; then
        setfacl -m "u:${TARGET_USER}:r" "$device" || true
    else
        chmod o+r "$device" || true
    fi
done
EOF
chmod +x "${DEB_DIR}/usr/share/${PACKAGE_NAME}/grant-input-access.sh"

# Create launcher script. The GUI must run as the desktop user, especially on Wayland.
cat > "${DEB_DIR}/usr/bin/${PACKAGE_NAME}" << 'EOF'
#!/bin/bash
set -e

APP_DIR="/usr/share/keyboard-key-display"
APP_FILE="${APP_DIR}/key_display.py"

can_read_input() {
    for device in /dev/input/event*; do
        [ -e "$device" ] || continue
        [ -r "$device" ] && return 0
    done
    return 1
}

if ! can_read_input; then
    if command -v pkexec >/dev/null 2>&1; then
        pkexec "${APP_DIR}/grant-input-access.sh" "$USER"
    else
        echo "Keyboard input permission is required. Please run:" >&2
        echo "  sudo usermod -aG input $USER" >&2
        echo "Then log out and log back in." >&2
        exit 1
    fi
fi

cd "$APP_DIR"
exec /usr/bin/python3 "$APP_FILE" "$@"
EOF
chmod +x "${DEB_DIR}/usr/bin/${PACKAGE_NAME}"

# Create polkit policy file for the permission helper only.
cat > "${DEB_DIR}/usr/share/polkit-1/actions/com.keyboard-key-display.policy" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <vendor>Keyboard Key Display</vendor>
  <vendor_url>https://github.com/ThinkReally114/Keyboard_Key_Display</vendor_url>

  <action id="com.keyboard-key-display.grant-input-access">
    <description>Grant keyboard input access</description>
    <message>Keyboard Key Display needs permission to read keyboard input devices</message>
    <defaults>
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>auth_admin</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/share/keyboard-key-display/grant-input-access.sh</annotate>
  </action>
</policyconfig>
EOF

# Create desktop entry
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

# Create control file
cat > "${DEB_DIR}/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3, python3-tk
Recommends: policykit-1, acl
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 A Linux desktop keyboard key display application that shows
 pressed keys on screen with a visual keyboard layout.
EOF

# Create postinst script
cat > "${DEB_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo "=== Keyboard Key Display installed ==="
echo ""
echo "The app now runs the GUI as your normal desktop user."
echo "If input permission is missing, it will ask for password once and grant temporary /dev/input access."
echo ""
echo "For permanent access without password prompt, run:"
echo "  sudo usermod -aG input \$USER"
echo "Then log out and log back in."

exit 0
EOF
chmod +x "${DEB_DIR}/DEBIAN/postinst"

# Create postrm script
cat > "${DEB_DIR}/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e
exit 0
EOF
chmod +x "${DEB_DIR}/DEBIAN/postrm"

# Build the package
dpkg-deb --build "${DEB_DIR}"

# Move deb to current directory
mv "${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" .

# Clean up
rm -rf "${BUILD_DIR}"

echo "Build complete: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
