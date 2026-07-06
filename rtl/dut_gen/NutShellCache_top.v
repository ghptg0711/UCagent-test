module NutShellCache_top;

  wire  clock;
  wire  reset;
  wire  io_cpu_req_valid;
  wire  io_cpu_req_ready;
  wire [63:0] io_cpu_req_bits_addr;
  wire  io_cpu_req_bits_write;
  wire [63:0] io_cpu_req_bits_wdata;
  wire [7:0] io_cpu_req_bits_wmask;
  wire  io_cpu_resp_valid;
  wire  io_cpu_resp_ready;
  wire [63:0] io_cpu_resp_bits_data;
  wire  io_mem_req_valid;
  wire  io_mem_req_ready;
  wire [63:0] io_mem_req_bits_addr;
  wire  io_mem_req_bits_write;
  wire [511:0] io_mem_req_bits_wdata;
  wire [63:0] io_mem_req_bits_wmask;
  wire  io_mem_resp_valid;
  wire  io_mem_resp_ready;
  wire [511:0] io_mem_resp_bits_data;


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


endmodule
