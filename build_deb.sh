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
mkdir -p "${DEB_DIR}/etc/sudoers.d"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"

# Copy application files
cp key_display.py "${DEB_DIR}/usr/share/${PACKAGE_NAME}/"
cp config.json "${DEB_DIR}/usr/share/${PACKAGE_NAME}/"
cp -r icons "${DEB_DIR}/usr/share/${PACKAGE_NAME}/" 2>/dev/null || true

# Create wrapper script that preserves environment
cat > "${DEB_DIR}/usr/share/${PACKAGE_NAME}/run-with-env.sh" << 'EOF'
#!/bin/bash
# This script is executed by pkexec with root privilege
# Environment variables are passed as arguments

cd /usr/share/keyboard-key-display

# Restore display environment from arguments
export DISPLAY="$1"
export XDG_RUNTIME_DIR="$2"
export WAYLAND_DISPLAY="$3"
export XAUTHORITY="$4"

# Run the application
exec /usr/bin/python3 /usr/share/keyboard-key-display/key_display.py
EOF
chmod +x "${DEB_DIR}/usr/share/${PACKAGE_NAME}/run-with-env.sh"

# Create launcher script
cat > "${DEB_DIR}/usr/bin/${PACKAGE_NAME}" << 'EOF'
#!/bin/bash

# Check if we're in input group
if groups | grep -q '\binput\b'; then
    # User is in input group, run directly
    cd /usr/share/keyboard-key-display
    exec /usr/bin/python3 /usr/share/keyboard-key-display/key_display.py "$@"
else
    # Need root permission, use pkexec with environment wrapper
    pkexec /usr/share/keyboard-key-display/run-with-env.sh \
        "$DISPLAY" \
        "$XDG_RUNTIME_DIR" \
        "$WAYLAND_DISPLAY" \
        "$XAUTHORITY"
fi
EOF
chmod +x "${DEB_DIR}/usr/bin/${PACKAGE_NAME}"

# Create polkit policy file
cat > "${DEB_DIR}/usr/share/polkit-1/actions/com.keyboard-key-display.policy" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <vendor>Keyboard Key Display</vendor>
  <vendor_url>https://github.com/ThinkReally114/Keyboard_Key_Display</vendor_url>

  <action id="com.keyboard-key-display.run">
    <description>Run Keyboard Key Display</description>
    <message>Keyboard Key Display needs root access to read keyboard input</message>
    <defaults>
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>auth_self</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/share/keyboard-key-display/run-with-env.sh</annotate>
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
Recommends: policykit-1
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
echo "To use without password prompt, add your user to the 'input' group:"
echo "  sudo usermod -aG input $USER"
echo "Then log out and log back in."
echo ""
echo "If not in 'input' group, the application will prompt for password."

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

