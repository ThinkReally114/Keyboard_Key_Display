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
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"

# Copy application files
cp key_display.py "${DEB_DIR}/usr/share/${PACKAGE_NAME}/"
cp config.json "${DEB_DIR}/usr/share/${PACKAGE_NAME}/"
cp -r icons "${DEB_DIR}/usr/share/${PACKAGE_NAME}/" 2>/dev/null || true

# Create launcher script
cat > "${DEB_DIR}/usr/bin/${PACKAGE_NAME}" << 'EOF'
#!/bin/bash
cd /usr/share/keyboard-key-display
python3 key_display.py "$@"
EOF
chmod +x "${DEB_DIR}/usr/bin/${PACKAGE_NAME}"

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
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 A Linux desktop keyboard key display application that shows
 pressed keys on screen with a visual keyboard layout.
EOF

# Create postinst script
cat > "${DEB_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Add user to input group for keyboard access
echo "To use keyboard-key-display without sudo, add your user to the 'input' group:"
echo "  sudo usermod -aG input \$USER"
echo "Then log out and log back in."

exit 0
EOF
chmod +x "${DEB_DIR}/DEBIAN/postinst"

# Build the package
dpkg-deb --build "${DEB_DIR}"

# Move deb to current directory
mv "${BUILD_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" .

# Clean up
rm -rf "${BUILD_DIR}"

echo "Build complete: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
