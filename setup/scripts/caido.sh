#!/bin/bash

install_caido() {
    local CAIDO_LATEST_VERSION=$(curl -s https://api.github.com/repos/caido/caido/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
    local CAIDO_DEB_PATH="/opt/my-resources/sources/caido.deb"
    local DOWNLOAD_URL="https://caido.download/releases/${CAIDO_LATEST_VERSION}/caido-desktop-${CAIDO_LATEST_VERSION}-linux-x86_64.deb"

    if [ ! -f "$CAIDO_DEB_PATH" ]; then
        DOWNLOAD_URL="https://caido.download/releases/${CAIDO_LATEST_VERSION}/caido-desktop-${CAIDO_LATEST_VERSION}-linux-x86_64.deb"
        wget -q -O "$CAIDO_DEB_PATH" "$DOWNLOAD_URL" || exit 1
    fi

    dpkg -i "$CAIDO_DEB_PATH" > /dev/null 2>&1 || {
        apt-get update -qq > /dev/null
        apt-get -f install -y -qq > /dev/null
        dpkg -i "$CAIDO_DEB_PATH" > /dev/null 2>&1 || exit 1
    }
}
