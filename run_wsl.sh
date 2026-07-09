#!/bin/bash
cd /mnt/d/UCagent/NutShell
echo "Checking mill and java..."
which mill
java -version
echo "=== Running verilog generation ==="
make verilog