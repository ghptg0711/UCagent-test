// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Prototypes for DPI import and export functions.
//
// Verilator includes this file in all generated .cpp files that use DPI functions.
// Manually include this file where DPI .c import functions are declared to ensure
// the C functions match the expectations of the DPI imports.

#ifndef VERILATED_VNUTSHELLCACHE__DPI_H_
#define VERILATED_VNUTSHELLCACHE__DPI_H_  // guard

#include "svdpi.h"

#ifdef __cplusplus
extern "C" {
#endif


    // DPI EXPORTS
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:242:17
    extern void finish_PfBDHOhl2mS();
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:82:17
    extern void get_clockxxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:117:17
    extern void get_io_cpu_req_bits_addrxxPfBDHOhl2mS(svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:137:17
    extern void get_io_cpu_req_bits_wdataxxPfBDHOhl2mS(svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:147:17
    extern void get_io_cpu_req_bits_wmaskxxPfBDHOhl2mS(svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:127:17
    extern void get_io_cpu_req_bits_writexxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:112:17
    extern void get_io_cpu_req_readyxxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:102:17
    extern void get_io_cpu_req_validxxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:172:17
    extern void get_io_cpu_resp_bits_dataxxPfBDHOhl2mS(svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:162:17
    extern void get_io_cpu_resp_readyxxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:157:17
    extern void get_io_cpu_resp_validxxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:192:17
    extern void get_io_mem_req_bits_addrxxPfBDHOhl2mS(svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:202:17
    extern void get_io_mem_req_bits_wdataxxPfBDHOhl2mS(svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:207:17
    extern void get_io_mem_req_bits_wmaskxxPfBDHOhl2mS(svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:197:17
    extern void get_io_mem_req_bits_writexxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:182:17
    extern void get_io_mem_req_readyxxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:177:17
    extern void get_io_mem_req_validxxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:227:17
    extern void get_io_mem_resp_bits_dataxxPfBDHOhl2mS(svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:222:17
    extern void get_io_mem_resp_readyxxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:212:17
    extern void get_io_mem_resp_validxxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:92:17
    extern void get_resetxxPfBDHOhl2mS(svLogic* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:87:17
    extern void set_clockxxPfBDHOhl2mS(svLogic value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:122:17
    extern void set_io_cpu_req_bits_addrxxPfBDHOhl2mS(const svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:142:17
    extern void set_io_cpu_req_bits_wdataxxPfBDHOhl2mS(const svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:152:17
    extern void set_io_cpu_req_bits_wmaskxxPfBDHOhl2mS(const svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:132:17
    extern void set_io_cpu_req_bits_writexxPfBDHOhl2mS(svLogic value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:107:17
    extern void set_io_cpu_req_validxxPfBDHOhl2mS(svLogic value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:167:17
    extern void set_io_cpu_resp_readyxxPfBDHOhl2mS(svLogic value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:187:17
    extern void set_io_mem_req_readyxxPfBDHOhl2mS(svLogic value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:232:17
    extern void set_io_mem_resp_bits_dataxxPfBDHOhl2mS(const svLogicVecVal* value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:217:17
    extern void set_io_mem_resp_validxxPfBDHOhl2mS(svLogic value);
    // DPI export at /mnt/d/UCagent/rtl/dut_gen/NutShellCache_top.sv:97:17
    extern void set_resetxxPfBDHOhl2mS(svLogic value);

#ifdef __cplusplus
}
#endif

#endif  // guard
