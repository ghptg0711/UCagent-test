#include "VNutShellCache.h"
#include "verilated.h"
#include "verilated_vcd_c.h"
#include "verilated_cov.h"
#include <chrono>
#include <cstdio>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>

namespace {
constexpr int RESET_CYCLES = 10;
constexpr int SIMULATION_CYCLES = 1000000;
constexpr int CPU_REQUEST_PERIOD = 3;
constexpr int PROGRESS_PRINT_PERIOD = 50000;
constexpr int ADDRESS_STRIDE_BYTES = 64;
constexpr int MAX_CACHE_ADDR = 0xFFFF;
constexpr int DEFAULT_SEED = 42;
constexpr unsigned long long WRITE_DATA_PATTERN = 0x11111111ULL;
constexpr unsigned int FULL_WRITE_MASK = 0xFF;

void write_coverage_metadata(int total_cycles) {
    std::filesystem::create_directories("reports/verilator_coverage");
    std::ofstream meta("reports/verilator_coverage/coverage_metadata.json");

    const auto now = std::chrono::system_clock::now();
    const auto now_time = std::chrono::system_clock::to_time_t(now);
    std::tm tm{};
#ifdef _WIN32
    localtime_s(&tm, &now_time);
#else
    localtime_r(&now_time, &tm);
#endif

    meta << "{\n";
    meta << "  \"tool\": \"Verilator\",\n";
    meta << "  \"tool_version\": \"" << Verilated::productVersion() << "\",\n";
    meta << "  \"timestamp\": \"" << std::put_time(&tm, "%Y-%m-%dT%H:%M:%S%z") << "\",\n";
    meta << "  \"simulation_seed\": " << DEFAULT_SEED << ",\n";
    meta << "  \"total_cycles\": " << total_cycles << ",\n";
    meta << "  \"dut_file\": \"rtl/dut_gen/NutShellCache.v\",\n";
    meta << "  \"coverage_file\": \"reports/verilator_coverage/coverage.dat\"\n";
    meta << "}\n";
}
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    VNutShellCache* dut = new VNutShellCache;

    // Enable VCD waveform tracing
    VerilatedVcdC* tfp = new VerilatedVcdC;
    Verilated::traceEverOn(true);
    dut->trace(tfp, 99);
    tfp->open("reports/waveforms/nutshell_cache_trace.vcd");

    // Initialize
    dut->clock = 0;
    dut->reset = 1;
    dut->io_cpu_req_valid = 0;
    dut->io_cpu_resp_ready = 0;
    dut->io_mem_req_ready = 0;
    dut->io_mem_resp_valid = 0;
    dut->eval();
    tfp->dump(0);

    std::filesystem::create_directories("reports/waveforms");

    // Reset for a deterministic number of cycles.
    for (int i = 0; i < RESET_CYCLES; i++) {
        dut->clock = !dut->clock;
        dut->eval();
        tfp->dump(i + 1);
    }
    dut->reset = 0;

    // Run a 1M-cycle sign-off smoke with deterministic stimulus.
    for (int cycle = 0; cycle < SIMULATION_CYCLES; cycle++) {
        dut->clock = !dut->clock;

        // Toggle CPU request randomly
        if (cycle % CPU_REQUEST_PERIOD == 0) {
            dut->io_cpu_req_valid = 1;
            dut->io_cpu_req_bits_addr = (cycle * ADDRESS_STRIDE_BYTES) & MAX_CACHE_ADDR;
            dut->io_cpu_req_bits_write = (cycle % 2);
            dut->io_cpu_req_bits_wdata = cycle * WRITE_DATA_PATTERN;
            dut->io_cpu_req_bits_wmask = FULL_WRITE_MASK;
        } else {
            dut->io_cpu_req_valid = 0;
        }

        dut->io_cpu_resp_ready = 1;
        dut->io_mem_req_ready = 1;

        dut->eval();
        tfp->dump(cycle + RESET_CYCLES + 1);

        if (cycle % PROGRESS_PRINT_PERIOD == 0) {
            printf("Cycle %d\n", cycle);
        }
    }

    // Write coverage
    VerilatedCov::write("reports/verilator_coverage/coverage.dat");
    write_coverage_metadata(SIMULATION_CYCLES);
    printf("Coverage data written to reports/verilator_coverage/coverage.dat\n");
    printf("Coverage metadata written to reports/verilator_coverage/coverage_metadata.json\n");
    printf("Total cycles: %d\n", SIMULATION_CYCLES);
    printf("Waveform written to reports/waveforms/nutshell_cache_trace.vcd\n");

    tfp->close();
    delete tfp;
    delete dut;
    return 0;
}
