#!/bin/bash
set -e

echo "=== 安裝 Buildozer 依賴 ==="

# 更新系統
sudo apt update

# 安裝必要依賴
sudo apt install -y \
    git \
    zip \
    unzip \
    openjdk-17-jdk \
    python3-pip \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev \
    build-essential \
    libltdl-dev \
    ccache

# 安裝 buildozer 和 cython
pip3 install --user --upgrade buildozer cython

# 將 pip 安裝路徑加入 PATH
export PATH=$PATH:~/.local/bin

echo "=== Buildozer 安裝完成 ==="
echo "現在可以執行: buildozer -v android debug"
