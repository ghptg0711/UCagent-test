module NutShellCache_top();

  logic  clock;
  logic  reset;
  logic  io_cpu_req_valid;
  logic  io_cpu_req_ready;
  logic [63:0] io_cpu_req_bits_addr;
  logic  io_cpu_req_bits_write;
  logic [63:0] io_cpu_req_bits_wdata;
  logic [7:0] io_cpu_req_bits_wmask;
  logic  io_cpu_resp_valid;
  logic  io_cpu_resp_ready;
  logic [63:0] io_cpu_resp_bits_data;
  logic  io_mem_req_valid;
  logic  io_mem_req_ready;
  logic [63:0] io_mem_req_bits_addr;
  logic  io_mem_req_bits_write;
  logic [511:0] io_mem_req_bits_wdata;
  logic [63:0] io_mem_req_bits_wmask;
  logic  io_mem_resp_valid;
  logic  io_mem_resp_ready;
  logic [511:0] io_mem_resp_bits_data;


 NutShellCache NutShellCache(
    .clock(clock),
    .reset(reset),
    .io_cpu_req_valid(io_cpu_req_valid),
    .io_cpu_req_ready(io_cpu_req_ready),
    .io_cpu_req_bits_addr(io_cpu_req_bits_addr),
    .io_cpu_req_bits_write(io_cpu_req_bits_write),
    .io_cpu_req_bits_wdata(io_cpu_req_bits_wdata),
    .io_cpu_req_bits_wmask(io_cpu_req_bits_wmask),
    .io_cpu_resp_valid(io_cpu_resp_valid),
    .io_cpu_resp_ready(io_cpu_resp_ready),
    .io_cpu_resp_bits_data(io_cpu_resp_bits_data),
    .io_mem_req_valid(io_mem_req_valid),
    .io_mem_req_ready(io_mem_req_ready),
    .io_mem_req_bits_addr(io_mem_req_bits_addr),
    .io_mem_req_bits_write(io_mem_req_bits_write),
    .io_mem_req_bits_wdata(io_mem_req_bits_wdata),
    .io_mem_req_bits_wmask(io_mem_req_bits_wmask),
    .io_mem_resp_valid(io_mem_resp_valid),
    .io_mem_resp_ready(io_mem_resp_ready),
    .io_mem_resp_bits_data(io_mem_resp_bits_data)
 );


  export "DPI-C" function get_clockxxPfBDHOhl2mS;
  export "DPI-C" function set_clockxxPfBDHOhl2mS;
  export "DPI-C" function get_resetxxPfBDHOhl2mS;
  export "DPI-C" function set_resetxxPfBDHOhl2mS;
  export "DPI-C" function get_io_cpu_req_validxxPfBDHOhl2mS;
  export "DPI-C" function set_io_cpu_req_validxxPfBDHOhl2mS;
  export "DPI-C" function get_io_cpu_req_readyxxPfBDHOhl2mS;
  export "DPI-C" function get_io_cpu_req_bits_addrxxPfBDHOhl2mS;
  export "DPI-C" function set_io_cpu_req_bits_addrxxPfBDHOhl2mS;
  export "DPI-C" function get_io_cpu_req_bits_writexxPfBDHOhl2mS;
  export "DPI-C" function set_io_cpu_req_bits_writexxPfBDHOhl2mS;
  export "DPI-C" function get_io_cpu_req_bits_wdataxxPfBDHOhl2mS;
  export "DPI-C" function set_io_cpu_req_bits_wdataxxPfBDHOhl2mS;
  export "DPI-C" function get_io_cpu_req_bits_wmaskxxPfBDHOhl2mS;
  export "DPI-C" function set_io_cpu_req_bits_wmaskxxPfBDHOhl2mS;
  export "DPI-C" function get_io_cpu_resp_validxxPfBDHOhl2mS;
  export "DPI-C" function get_io_cpu_resp_readyxxPfBDHOhl2mS;
  export "DPI-C" function set_io_cpu_resp_readyxxPfBDHOhl2mS;
  export "DPI-C" function get_io_cpu_resp_bits_dataxxPfBDHOhl2mS;
  export "DPI-C" function get_io_mem_req_validxxPfBDHOhl2mS;
  export "DPI-C" function get_io_mem_req_readyxxPfBDHOhl2mS;
  export "DPI-C" function set_io_mem_req_readyxxPfBDHOhl2mS;
  export "DPI-C" function get_io_mem_req_bits_addrxxPfBDHOhl2mS;
  export "DPI-C" function get_io_mem_req_bits_writexxPfBDHOhl2mS;
  export "DPI-C" function get_io_mem_req_bits_wdataxxPfBDHOhl2mS;
  export "DPI-C" function get_io_mem_req_bits_wmaskxxPfBDHOhl2mS;
  export "DPI-C" function get_io_mem_resp_validxxPfBDHOhl2mS;
  export "DPI-C" function set_io_mem_resp_validxxPfBDHOhl2mS;
  export "DPI-C" function get_io_mem_resp_readyxxPfBDHOhl2mS;
  export "DPI-C" function get_io_mem_resp_bits_dataxxPfBDHOhl2mS;
  export "DPI-C" function set_io_mem_resp_bits_dataxxPfBDHOhl2mS;


  function void get_clockxxPfBDHOhl2mS;
    output logic  value;
    value=clock;
  endfunction

  function void set_clockxxPfBDHOhl2mS;
    input logic  value;
    clock=value;
  endfunction

  function void get_resetxxPfBDHOhl2mS;
    output logic  value;
    value=reset;
  endfunction

  function void set_resetxxPfBDHOhl2mS;
    input logic  value;
    reset=value;
  endfunction

  function void get_io_cpu_req_validxxPfBDHOhl2mS;
    output logic  value;
    value=io_cpu_req_valid;
  endfunction

  function void set_io_cpu_req_validxxPfBDHOhl2mS;
    input logic  value;
    io_cpu_req_valid=value;
  endfunction

  function void get_io_cpu_req_readyxxPfBDHOhl2mS;
    output logic  value;
    value=io_cpu_req_ready;
  endfunction

  function void get_io_cpu_req_bits_addrxxPfBDHOhl2mS;
    output logic [63:0] value;
    value=io_cpu_req_bits_addr;
  endfunction

  function void set_io_cpu_req_bits_addrxxPfBDHOhl2mS;
    input logic [63:0] value;
    io_cpu_req_bits_addr=value;
  endfunction

  function void get_io_cpu_req_bits_writexxPfBDHOhl2mS;
    output logic  value;
    value=io_cpu_req_bits_write;
  endfunction

  function void set_io_cpu_req_bits_writexxPfBDHOhl2mS;
    input logic  value;
    io_cpu_req_bits_write=value;
  endfunction

  function void get_io_cpu_req_bits_wdataxxPfBDHOhl2mS;
    output logic [63:0] value;
    value=io_cpu_req_bits_wdata;
  endfunction

  function void set_io_cpu_req_bits_wdataxxPfBDHOhl2mS;
    input logic [63:0] value;
    io_cpu_req_bits_wdata=value;
  endfunction

  function void get_io_cpu_req_bits_wmaskxxPfBDHOhl2mS;
    output logic [7:0] value;
    value=io_cpu_req_bits_wmask;
  endfunction

  function void set_io_cpu_req_bits_wmaskxxPfBDHOhl2mS;
    input logic [7:0] value;
    io_cpu_req_bits_wmask=value;
  endfunction

  function void get_io_cpu_resp_validxxPfBDHOhl2mS;
    output logic  value;
    value=io_cpu_resp_valid;
  endfunction

  function void get_io_cpu_resp_readyxxPfBDHOhl2mS;
    output logic  value;
    value=io_cpu_resp_ready;
  endfunction

  function void set_io_cpu_resp_readyxxPfBDHOhl2mS;
    input logic  value;
    io_cpu_resp_ready=value;
  endfunction

  function void get_io_cpu_resp_bits_dataxxPfBDHOhl2mS;
    output logic [63:0] value;
    value=io_cpu_resp_bits_data;
  endfunction

  function void get_io_mem_req_validxxPfBDHOhl2mS;
    output logic  value;
    value=io_mem_req_valid;
  endfunction

  function void get_io_mem_req_readyxxPfBDHOhl2mS;
    output logic  value;
    value=io_mem_req_ready;
  endfunction

  function void set_io_mem_req_readyxxPfBDHOhl2mS;
    input logic  value;
    io_mem_req_ready=value;
  endfunction

  function void get_io_mem_req_bits_addrxxPfBDHOhl2mS;
    output logic [63:0] value;
    value=io_mem_req_bits_addr;
  endfunction

  function void get_io_mem_req_bits_writexxPfBDHOhl2mS;
    output logic  value;
    value=io_mem_req_bits_write;
  endfunction

  function void get_io_mem_req_bits_wdataxxPfBDHOhl2mS;
    output logic [511:0] value;
    value=io_mem_req_bits_wdata;
  endfunction

  function void get_io_mem_req_bits_wmaskxxPfBDHOhl2mS;
    output logic [63:0] value;
    value=io_mem_req_bits_wmask;
  endfunction

  function void get_io_mem_resp_validxxPfBDHOhl2mS;
    output logic  value;
    value=io_mem_resp_valid;
  endfunction

  function void set_io_mem_resp_validxxPfBDHOhl2mS;
    input logic  value;
    io_mem_resp_valid=value;
  endfunction

  function void get_io_mem_resp_readyxxPfBDHOhl2mS;
    output logic  value;
    value=io_mem_resp_ready;
  endfunction

  function void get_io_mem_resp_bits_dataxxPfBDHOhl2mS;
    output logic [511:0] value;
    value=io_mem_resp_bits_data;
  endfunction

  function void set_io_mem_resp_bits_dataxxPfBDHOhl2mS;
    input logic [511:0] value;
    io_mem_resp_bits_data=value;
  endfunction





  export "DPI-C" function finish_PfBDHOhl2mS;
  function void finish_PfBDHOhl2mS;
    $finish;
  endfunction


endmodule
