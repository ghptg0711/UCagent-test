#!/bin/bash
set -e

echo "=== Step 1: Configure Maven Aliyun mirror ==="
mkdir -p ~/.mill/ammonite
mkdir -p ~/.config/coursier

cat > ~/.mill/mill.properties << 'EOF'
MILL_JVM_OPTS=-Xmx4G -Xss256m -Dcoursier.mirrors=https://maven.aliyun.com/repository/public
EOF

mkdir -p ~/.config/coursier
cat > ~/.config/coursier/mirror.properties << 'EOF'
central.from=https://repo1.maven.org/maven2
central.to=https://maven.aliyun.com/repository/central
jcenter.from=https://jcenter.bintray.com
jcenter.to=https://maven.aliyun.com/repository/public
typesafe.from=https://repo.typesafe.com/typesafe/ivy-releases
typesafe.to=https://maven.aliyun.com/repository/public
sbt-plugin.from=https://repo.scala-sbt.org/scalasbt/sbt-plugin-releases
sbt-plugin.to=https://maven.aliyun.com/repository/public
EOF

echo "=== Step 2: Install Mill 0.11.7 ==="
MILL_VERSION="0.11.7"

curl -fL "https://github.com/com-lihaoyi/mill/releases/download/${MILL_VERSION}/${MILL_VERSION}" -o /tmp/mill && {
    chmod +x /tmp/mill
    echo "1234" | sudo -S mv /tmp/mill /usr/local/bin/mill
    echo "Mill installed successfully"
    mill -version
} || {
    echo "GitHub download failed, trying alternative..."
    echo "Please manually download mill from:"
    echo "  https://github.com/com-lihaoyi/mill/releases/download/0.11.7/0.11.7"
    echo "And place it at /usr/local/bin/mill"
    exit 1
}

echo "=== Step 3: Compile NutShell ==="
cd /mnt/d/UCagent/NutShell
export MILL_JVM_OPTS="-Xmx4G -Xss256m"

echo "Running make verilog..."
make verilog

echo "=== Step 4: Check output ==="
ls -la build/rtl/ 2>/dev/null || ls -la build/ 2>/dev/null || echo "Build directory not found"

echo "=== Done ==="
