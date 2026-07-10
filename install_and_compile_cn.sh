#!/bin/bash
set -e

echo "=== Install Mill using ghproxy mirror ==="
MILL_VERSION="0.11.7"

# Try multiple ghproxy mirrors
MIRRORS=(
    "https://mirror.ghproxy.com/https://github.com/com-lihaoyi/mill/releases/download/${MILL_VERSION}/${MILL_VERSION}"
    "https://ghproxy.com/https://github.com/com-lihaoyi/mill/releases/download/${MILL_VERSION}/${MILL_VERSION}"
    "https://gh.api.99988866.xyz/https://github.com/com-lihaoyi/mill/releases/download/${MILL_VERSION}/${MILL_VERSION}"
)

for mirror in "${MIRRORS[@]}"; do
    echo "Trying: $mirror"
    if curl -fL --connect-timeout 10 --max-time 120 "$mirror" -o /tmp/mill; then
        echo "Download successful!"
        chmod +x /tmp/mill
        echo "1234" | sudo -S mv /tmp/mill /usr/local/bin/mill
        mill -version
        break
    else
        echo "Failed, trying next mirror..."
    fi
done

if ! command -v mill &> /dev/null; then
    echo "ERROR: Failed to download mill from all mirrors"
    exit 1
fi

echo "=== Configure Maven Aliyun mirror ==="
mkdir -p ~/.mill
cat > ~/.mill/mill.properties << 'EOF'
MILL_JVM_OPTS=-Xmx4G -Xss256m
EOF

mkdir -p ~/.config/coursier
cat > ~/.config/coursier/mirror.properties << 'EOF'
central.from=https://repo1.maven.org/maven2
central.to=https://maven.aliyun.com/repository/central
jcenter.from=https://jcenter.bintray.com
jcenter.to=https://maven.aliyun.com/repository/public
EOF

echo "=== Compile NutShell ==="
cd /mnt/d/UCagent/NutShell
export MILL_JVM_OPTS="-Xmx4G -Xss256m"

echo "Running make verilog (this may take several minutes)..."
make verilog 2>&1

echo "=== Check build output ==="
ls -la build/ 2>/dev/null || echo "No build directory"
find build -name "*.v" -o -name "*.sv" 2>/dev/null | head -20 || echo "No Verilog files found"

echo "=== Done ==="
