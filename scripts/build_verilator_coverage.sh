#!/bin/bash
# Verilator Coverage Build Script
# Compiles NutShell Cache RTL with --coverage and --trace enabled
set -e

DUT_VERILOG="rtl/dut_gen/NutShellCache.v"
TOP_MODULE="NutShellCache"
OUTPUT_DIR="reports/verilator_coverage"
SIM_DIR="obj_dir_coverage"

echo "=== Verilator Coverage Build ==="
echo "DUT: $DUT_VERILOG"
echo "Top Module: $TOP_MODULE"
echo "Output: $OUTPUT_DIR"

rm -rf "$OUTPUT_DIR" "$SIM_DIR"
mkdir -p "$OUTPUT_DIR"

echo ""
echo "=== Step 1: Verilate with Coverage ==="
verilator --cc \
  --coverage \
  --trace \
  -Wall \
  -Wno-fatal \
  -Wno-WIDTH \
  -Wno-UNUSED \
  -Wno-UNOPTFLAT \
  --Mdir "$SIM_DIR" \
  "$DUT_VERILOG" \
  --top-module "$TOP_MODULE" \
  --exe \
  scripts/sim_main.cpp

echo "✅ Verilation completed"

echo ""
echo "=== Step 2: Build Simulation ==="
make -C "$SIM_DIR" -f "V${TOP_MODULE}.mk"

echo "✅ Build completed"
echo "Simulation executable: $SIM_DIR/V${TOP_MODULE}"

echo ""
echo "=== Step 3: Create Run Script ==="
cat > "$SIM_DIR/run_with_coverage.sh" << 'RUNEOF'
#!/bin/bash
cd /mnt/d/UCagent
mkdir -p reports/verilator_coverage reports/waveforms
./obj_dir_coverage/VNutShellCache 2>&1 | tee reports/verilator_coverage/simulation.log
RUNEOF
chmod +x "$SIM_DIR/run_with_coverage.sh"

echo "✅ Run script created: $SIM_DIR/run_with_coverage.sh"

echo ""
echo "=== Build Summary ==="
echo "To run simulation:"
echo "  $SIM_DIR/run_with_coverage.sh"
echo ""
echo "To generate coverage report:"
echo "  verilator_coverage --annotate $OUTPUT_DIR/annotated $OUTPUT_DIR/coverage.dat"
