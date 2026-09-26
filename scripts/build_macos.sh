#!/usr/bin/env bash
# ==============================================================================
# build_macos.sh
# Builds macOS application bundle (.app) and disk image (.dmg)
# Includes quarantine stripping, ad-hoc codesigning, and Applications symlink.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "==> Extracting application version..."
VERSION=$(python3 -c "import runpy; print(runpy.run_path('core/version.py')['__version__'])")
APP_NAME="Pa-O Typing Tutor"
DMG_NAME="Pa-O-Typing-Tutor-v${VERSION}-macos.dmg"

echo "==> Building ${APP_NAME} version ${VERSION} for macOS..."

echo "==> Ensuring platform icons are generated..."
python3 make_icons.py

echo "==> Cleaning previous build artifacts..."
rm -rf build dist/*.dmg dist/*.app "dist/${APP_NAME}"

echo "==> Running PyInstaller..."
pyinstaller --clean --noconfirm pao-typing-tutor.spec

APP_BUNDLE="dist/${APP_NAME}.app"
if [ ! -d "${APP_BUNDLE}" ]; then
    echo "ERROR: App bundle not found at ${APP_BUNDLE}" >&2
    exit 1
fi

echo "==> Removing quarantine attributes from bundle..."
xattr -cr "${APP_BUNDLE}"

echo "==> Performing ad-hoc code signing..."
codesign --force --deep --sign - "${APP_BUNDLE}"

echo "==> Verifying signature..."
codesign --verify --deep --strict --verbose=2 "${APP_BUNDLE}"

echo "==> Creating disk image (.dmg)..."
STAGING_DIR="dist/dmg_staging"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

cp -R "${APP_BUNDLE}" "${STAGING_DIR}/"
ln -s /Applications "${STAGING_DIR}/Applications"

DMG_PATH="dist/${DMG_NAME}"
rm -f "${DMG_PATH}"

hdiutil create \
    -volname "${APP_NAME}" \
    -srcfolder "${STAGING_DIR}" \
    -ov \
    -format UDZO \
    "${DMG_PATH}"

rm -rf "${STAGING_DIR}"

echo ""
echo "=============================================================================="
echo " macOS Build Succeeded!"
echo " App bundle: ${APP_BUNDLE}"
echo " DMG image:  ${DMG_PATH}"
ls -lh "${DMG_PATH}"
echo "=============================================================================="
