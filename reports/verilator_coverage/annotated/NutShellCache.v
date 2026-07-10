//      // verilator_coverage annotation
        // NutShell-style Cache DUT (simplified)
        // Compatible with NutShell Cache interface conventions
        // Top module: NutShellCache
        
        `timescale 1ns / 1ps
        
        module NutShellCache (
 1000010     input  clock,
%000002     input  reset,
        
            // CPU request interface (valid/ready handshake)
 666667     input         io_cpu_req_valid,
%000002     output        io_cpu_req_ready,
~333333     input  [63:0] io_cpu_req_bits_addr,
 333333     input         io_cpu_req_bits_write,
~333333     input  [63:0] io_cpu_req_bits_wdata,
%000001     input  [7:0]  io_cpu_req_bits_wmask,
        
            // CPU response interface
%000000     output        io_cpu_resp_valid,
%000001     input         io_cpu_resp_ready,
%000000     output [63:0] io_cpu_resp_bits_data,
        
            // Memory request interface (DUT -> Memory)
%000001     output        io_mem_req_valid,
%000001     input         io_mem_req_ready,
%000000     output [63:0] io_mem_req_bits_addr,
%000000     output        io_mem_req_bits_write,
            output [511:0] io_mem_req_bits_wdata,
%000000     output [63:0]  io_mem_req_bits_wmask,
        
            // Memory response interface (Memory -> DUT)
%000000     input          io_mem_resp_valid,
%000001     output         io_mem_resp_ready,
            input  [511:0] io_mem_resp_bits_data
        );
        
            // Cache parameters
            localparam SETS = 64;
            localparam WAYS = 4;
            localparam LINE_BYTES = 64;
            localparam OFFSET_BITS = 6;   // log2(64)
            localparam INDEX_BITS = 6;   // log2(64)
            localparam TAG_BITS = 64 - OFFSET_BITS - INDEX_BITS;
        
            // Cache state
            reg [LINE_BYTES*8-1:0] cache_data [0:SETS-1][0:WAYS-1];
            reg [TAG_BITS-1:0]     cache_tag  [0:SETS-1][0:WAYS-1];
%000000     reg                    cache_valid [0:SETS-1][0:WAYS-1];
%000000     reg                    cache_dirty [0:SETS-1][0:WAYS-1];
%000000     reg [$clog2(WAYS)-1:0] lru_way [0:SETS-1];
        
            // Backing memory (simplified, 64KB)
            reg [7:0] backing_mem [0:65535];
        
            // Request processing state
%000001     reg        req_pending;
%000000     reg        req_write;
%000000     reg [63:0] req_addr;
%000000     reg [63:0] req_wdata;
%000001     reg [7:0]  req_wmask;
%000000     reg [63:0] resp_data;
%000000     reg        resp_valid_r;
        
            // Memory request state
%000001     reg        mem_req_pending;
%000000     reg [63:0] mem_req_addr;
%000000     reg        mem_req_write;
            reg [511:0] mem_req_wdata;
%000000     reg [63:0]  mem_req_wmask;
        
            // Index/tag extraction
%000000     wire [OFFSET_BITS-1:0] offset = req_addr[OFFSET_BITS-1:0];
%000000     wire [INDEX_BITS-1:0] index = req_addr[OFFSET_BITS+INDEX_BITS-1:OFFSET_BITS];
%000000     wire [TAG_BITS-1:0]   tag = req_addr[63:OFFSET_BITS+INDEX_BITS];
        
            // Hit detection
%000000     reg [31:0] hit_way; // 0-indexed
%000000     reg        hit;
        
            // Find hit
 500006     always @(*) begin
 500006         hit = 0;
 500006         hit_way = 0;
 2000024         for (integer w = 0; w < WAYS; w = w + 1) begin
~2000024             if (cache_valid[index][w] && cache_tag[index][w] == tag) begin
%000000                 hit = 1;
%000000                 hit_way = w;
                    end
                end
            end
        
            // Ready signal
            assign io_cpu_req_ready = ~req_pending && ~mem_req_pending;
            assign io_cpu_resp_valid = resp_valid_r;
            assign io_cpu_resp_bits_data = resp_data;
        
            // Memory request signals
            assign io_mem_req_valid = mem_req_pending;
            assign io_mem_req_bits_addr = mem_req_addr;
            assign io_mem_req_bits_write = mem_req_write;
            assign io_mem_req_bits_wdata = mem_req_wdata;
            assign io_mem_req_bits_wmask = mem_req_wmask;
            assign io_mem_resp_ready = 1'b1;
        
            // Main processing
 500005     always @(posedge clock) begin
~500000         if (reset) begin
%000005             req_pending <= 0;
%000005             resp_valid_r <= 0;
%000005             mem_req_pending <= 0;
~000320             for (integer s = 0; s < SETS; s = s + 1) begin
 000320                 lru_way[s] <= 0;
 001280                 for (integer w = 0; w < WAYS; w = w + 1) begin
 001280                     cache_valid[s][w] <= 0;
 001280                     cache_dirty[s][w] <= 0;
                        end
                    end
 500000         end else begin
                    // Clear response
~500000             if (resp_valid_r && io_cpu_resp_ready) begin
%000000                 resp_valid_r <= 0;
                    end
        
                    // Handle memory response (fill)
~500000             if (io_mem_resp_valid && mem_req_pending) begin
%000000                 mem_req_pending <= 0;
                        // Fill cache line
%000000                 cache_data[index][lru_way[index]] <= io_mem_resp_bits_data;
%000000                 cache_tag[index][lru_way[index]] <= tag;
%000000                 cache_valid[index][lru_way[index]] <= 1;
%000000                 cache_dirty[index][lru_way[index]] <= 0;
                        // Generate response
%000000                 resp_data <= io_mem_resp_bits_data[offset*8 +: 64];
%000000                 resp_valid_r <= 1;
%000000                 req_pending <= 0;
                    end
        
                    // Accept new request
~499999             if (io_cpu_req_valid && io_cpu_req_ready && !req_pending) begin
%000001                 req_pending <= 1;
%000001                 req_write <= io_cpu_req_bits_write;
%000001                 req_addr <= io_cpu_req_bits_addr;
%000001                 req_wdata <= io_cpu_req_bits_wdata;
%000001                 req_wmask <= io_cpu_req_bits_wmask;
                    end
        
                    // Process request
~499999             if (req_pending && !resp_valid_r) begin
~499999                 if (hit) begin
                            // Cache hit
%000000                     if (req_write) begin
                                // Write hit - update data with mask
%000000                         for (integer i = 0; i < 8; i = i + 1) begin
%000000                             if (req_wmask[i]) begin
%000000                                 cache_data[index][hit_way][offset*8 + i*8 +: 8] <= req_wdata[i*8 +: 8];
                                    end
                                end
%000000                         cache_dirty[index][hit_way] <= 1;
%000000                         resp_data <= 0;
%000000                         resp_valid_r <= 1;
%000000                         req_pending <= 0;
%000000                     end else begin
                                // Read hit
%000000                         resp_data <= cache_data[index][hit_way][offset*8 +: 64];
%000000                         resp_valid_r <= 1;
%000000                         req_pending <= 0;
                            end
                            // Update LRU
%000000                     lru_way[index] <= (hit_way == WAYS-1) ? 0 : hit_way + 1;
 499999                 end else begin
                            // Cache miss - need to fill from memory
~499998                     if (!mem_req_pending) begin
                                // Check if victim is dirty
%000001                         if (cache_valid[index][lru_way[index]] && cache_dirty[index][lru_way[index]]) begin
                                    // Writeback dirty line
%000000                             mem_req_pending <= 1;
%000000                             mem_req_addr <= {cache_tag[index][lru_way[index]], index, {OFFSET_BITS{1'b0}}};
%000000                             mem_req_write <= 1;
%000000                             mem_req_wdata <= cache_data[index][lru_way[index]];
%000000                             mem_req_wmask <= {LINE_BYTES{1'b1}};
%000001                         end else begin
                                    // Just fill
%000001                             mem_req_pending <= 1;
%000001                             mem_req_addr <= {tag, index, {OFFSET_BITS{1'b0}}};
%000001                             mem_req_write <= 0;
%000001                             mem_req_wdata <= 0;
%000001                             mem_req_wmask <= 0;
                                end
                            end
                        end
                    end
                end
            end
        
        endmodule
        
