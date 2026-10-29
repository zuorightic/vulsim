`timescale 1ns/1ps

module Top_sim_top(
  input clk,
  input rstn,
  output [0:0] valid__query__,
  output [4265:0] result__query__,
  input echo257__vld__,
  input [256:0] echo257_value__,
  output [256:0] echo257_result__,
  input echo256__vld__,
  input [255:0] echo256_value__,
  output [255:0] echo256_result__,
  input echo193__vld__,
  input [192:0] echo193_value__,
  output [192:0] echo193_result__,
  input echo128__vld__,
  input [127:0] echo128_value__,
  output [127:0] echo128_result__,
  input echo129__vld__,
  input [128:0] echo129_value__,
  output [128:0] echo129_result__,
  input combine__vld__,
  input [1033:0] combine_value__,
  output [4265:0] combine_result__,
  input push__vld__,
  input [1033:0] push_value__,
  input [0:0] push_valid__
);

reg [1033:0] __vul_pipeline_q_input;
wire [1033:0] resetvalue_input__;
wire wen_input__;
wire [1033:0] wdata_input__;
reg [0:0] __vul_pipeline_q_iv = 1'b0;
wire [0:0] resetvalue_iv__;
wire wen_iv__;
wire [0:0] wdata_iv__;
reg [4265:0] __vul_pipeline_q_output;
wire [4265:0] __vul_pipeline_d_output;
reg [0:0] __vul_pipeline_q_ov = 1'b0;
wire [0:0] __vul_pipeline_d_ov;

always @(posedge clk) begin
  if (rstn == 0) begin
    __vul_pipeline_q_input <= resetvalue_input__;
  end else begin
begin
    if (wen_input__) begin
      __vul_pipeline_q_input <= wdata_input__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    __vul_pipeline_q_iv <= resetvalue_iv__;
  end else begin
begin
    if (wen_iv__) begin
      __vul_pipeline_q_iv <= wdata_iv__;
    end
    end
  end
end
always @(posedge clk) begin
  if (!rstn) begin
    __vul_pipeline_q_output <= 4266'h3fffffffffffffffffffffffffffffff800000000000000000000000000000007fffffffffffffffffffffffffffffffc0000000000000000000000000000000200000000000000000000000000000003fffffffffffffffffffffffffffffffdffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff800000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffdfffffffffffffffffffffffffffffffc00000000000000000000000000000001fffffffffffffffffffffffffffffffc0000000000000000000000000000000200000000000000000000000000000001fffffffffffffffffffffffffffffffe000000000000000000000000000000010000000000000000c000000000000000000000000000000000000000000000007fffffffffffffffffffffffffffffffbfffffffffffffff80000000000000003fffffffffffffff800000000000000040000000000000003fffffffffffffffc000000000000000200000001800000000000000000000000ffffffffffffffff7fffffff000000007fffffff00000000800000007fffffff8000000040003000000000001fffffffefffe0000fffe00010000ffff0000806000003fffdfc01fc0201fe01;
  end else begin
  __vul_pipeline_q_output <= __vul_pipeline_d_output;
  end
end
always @(posedge clk) begin
  if (!rstn) begin
    __vul_pipeline_q_ov <= 1'h0;
  end else begin
  __vul_pipeline_q_ov <= __vul_pipeline_d_ov;
  end
end

if (1) begin : __vul_pipeline_calculate
  logic [1033:0] __vul_port_input;
  assign __vul_port_input = __vul_pipeline_q_input;
  logic __vul_port_iv;
  assign __vul_port_iv = __vul_pipeline_q_iv;
  logic __vul_pipeline_rstn;
  assign __vul_pipeline_rstn = rstn;
  logic __vul_pipeline_clk;
  assign __vul_pipeline_clk = clk;
  logic [4265:0] __vul_port_output;
  assign __vul_pipeline_d_output = __vul_port_output;
  logic __vul_port_ov;
  assign __vul_pipeline_d_ov = __vul_port_ov;


  reg          rtlzz_valid_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:464:21
  wire         _GEN = ~__vul_pipeline_rstn;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9
  reg  [127:0] rtlzz_pipe_2_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:7:22
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:7:22
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :7:22
      rtlzz_pipe_2_s1 <= 128'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:7:22
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :7:22
      rtlzz_pipe_2_s1 <= __vul_port_iv ? __vul_port_input[127:0] : rtlzz_pipe_2_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:5:9, :7:22
  end // always_ff @(posedge)
  reg  [127:0] rtlzz_pipe_3_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:10:22
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:10:22
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :10:22
      rtlzz_pipe_3_s1 <= 128'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:10:22
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :10:22
      rtlzz_pipe_3_s1 <= __vul_port_iv ? __vul_port_input[255:128] : rtlzz_pipe_3_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:8:9, :10:22
  end // always_ff @(posedge)
  reg  [255:0] rtlzz_pipe_6_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:13:22
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:13:22
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :13:22
      rtlzz_pipe_6_s1 <=
        256'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:12:9, :13:22
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :13:22
      rtlzz_pipe_6_s1 <= __vul_port_iv ? __vul_port_input[767:512] : rtlzz_pipe_6_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:11:9, :13:22
  end // always_ff @(posedge)
  reg  [256:0] rtlzz_pipe_7_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:16:22
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:16:22
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :16:22
      rtlzz_pipe_7_s1 <=
        257'h1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:16:22
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :16:22
      rtlzz_pipe_7_s1 <= __vul_port_iv ? __vul_port_input[1024:768] : rtlzz_pipe_7_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:14:9, :16:22
  end // always_ff @(posedge)
  reg  [256:0] rtlzz_pipe_7_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:18:22
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:18:22
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :18:22
      rtlzz_pipe_7_s2 <=
        257'h1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:18:22
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :18:22
      rtlzz_pipe_7_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_7_s1 : rtlzz_pipe_7_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:16:22, :18:22, :464:21
  end // always_ff @(posedge)
  reg          rtlzz_pipe_8_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:21:22
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:21:22
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :21:22
      rtlzz_pipe_8_s1 <= 1'h1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:21:22
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :21:22
      rtlzz_pipe_8_s1 <= __vul_port_iv ? __vul_port_input[1033] : rtlzz_pipe_8_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:19:10, :21:22
  end // always_ff @(posedge)
  reg  [7:0]   rtlzz_pipe_9_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:24:22
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:24:22
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :24:22
      rtlzz_pipe_9_s1 <= 8'hFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:24:22
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :24:22
      rtlzz_pipe_9_s1 <= __vul_port_iv ? __vul_port_input[7:0] : rtlzz_pipe_9_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:22:10, :24:22
  end // always_ff @(posedge)
  reg  [7:0]   rtlzz_pipe_10_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:27:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:27:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :27:23
      rtlzz_pipe_10_s1 <= 8'hFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:27:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :27:23
      rtlzz_pipe_10_s1 <= __vul_port_iv ? __vul_port_input[135:128] : rtlzz_pipe_10_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:25:10, :27:23
  end // always_ff @(posedge)
  reg  [7:0]   rtlzz_pipe_11_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:31:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:31:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :31:23
      rtlzz_pipe_11_s1 <= 8'hFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:31:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :31:23
      rtlzz_pipe_11_s1 <= __vul_port_iv ? __vul_port_input[263:256] : rtlzz_pipe_11_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:29:10, :31:23
  end // always_ff @(posedge)
  reg  [7:0]   rtlzz_pipe_12_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:35:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:35:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :35:23
      rtlzz_pipe_12_s1 <= 8'hFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:35:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :35:23
      rtlzz_pipe_12_s1 <= __vul_port_iv ? __vul_port_input[391:384] : rtlzz_pipe_12_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:33:10, :35:23
  end // always_ff @(posedge)
  wire [15:0]  _GEN_0 = {8'h0, rtlzz_pipe_9_s1} * {8'h0, rtlzz_pipe_10_s1};	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:24:22, :27:23, :37:10, :39:10, :40:10
  reg  [15:0]  rtlzz_pipe_13_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:42:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:42:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :42:23
      rtlzz_pipe_13_s2 <= 16'hFE01;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:42:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :42:23
      rtlzz_pipe_13_s2 <= rtlzz_valid_s1 ? _GEN_0 : rtlzz_pipe_13_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:40:10, :42:23, :464:21
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_14_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:49:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:49:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :49:23
      rtlzz_pipe_14_s2 <= 16'hFE01;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:49:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :49:23
      rtlzz_pipe_14_s2 <=
        rtlzz_valid_s1
          ? {8'h0, rtlzz_pipe_11_s1} * {8'h0, rtlzz_pipe_12_s1}
          : rtlzz_pipe_14_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:31:23, :35:23, :44:10, :46:10, :47:10, :49:23, :464:21
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_20_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:53:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:53:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :53:23
      rtlzz_pipe_20_s2 <= 16'hFE00;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:52:10, :53:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :53:23
      rtlzz_pipe_20_s2 <=
        rtlzz_valid_s1 ? _GEN_0 + rtlzz_pipe_6_s1[15:0] : rtlzz_pipe_20_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:13:22, :40:10, :50:10, :51:10, :53:23, :464:21
  end // always_ff @(posedge)
  reg  [7:0]   rtlzz_pipe_21_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:56:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:56:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :56:23
      rtlzz_pipe_21_s2 <= 8'hFE;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:55:10, :56:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :56:23
      rtlzz_pipe_21_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_9_s1 + rtlzz_pipe_10_s1 : rtlzz_pipe_21_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:24:22, :27:23, :54:10, :56:23, :464:21
  end // always_ff @(posedge)
  reg  [8:0]   rtlzz_pipe_22_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:66:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:66:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :66:23
      rtlzz_pipe_22_s2 <= 9'h1FF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:65:10, :66:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :66:23
      rtlzz_pipe_22_s2 <=
        rtlzz_valid_s1
          ? {1'h0, rtlzz_pipe_9_s1} + {1'h0, rtlzz_pipe_10_s1} + {8'h0, rtlzz_pipe_8_s1}
          : rtlzz_pipe_22_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:21:22, :24:22, :27:23, :58:10, :60:10, :62:10, :63:10, :64:10, :66:23, :464:21
  end // always_ff @(posedge)
  reg  [7:0]   rtlzz_pipe_23_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:69:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:69:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :69:23
      rtlzz_pipe_23_s2 <= 8'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:69:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :69:23
      rtlzz_pipe_23_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_9_s1 - rtlzz_pipe_10_s1 : rtlzz_pipe_23_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:24:22, :27:23, :67:10, :69:23, :464:21
  end // always_ff @(posedge)
  reg  [7:0]   rtlzz_pipe_26_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:74:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:74:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :74:23
      rtlzz_pipe_26_s1 <= 8'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:74:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :74:23
      rtlzz_pipe_26_s1 <=
        __vul_port_iv
          ? __vul_port_input[7:0] & __vul_port_input[135:128]
            ^ (__vul_port_input[263:256] | __vul_port_input[391:384])
          : rtlzz_pipe_26_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:22:10, :25:10, :29:10, :33:10, :70:10, :71:10, :72:10, :74:23
  end // always_ff @(posedge)
  reg  [7:0]   rtlzz_pipe_26_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:76:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:76:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :76:23
      rtlzz_pipe_26_s2 <= 8'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:76:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :76:23
      rtlzz_pipe_26_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_26_s1 : rtlzz_pipe_26_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:74:23, :76:23, :464:21
  end // always_ff @(posedge)
  reg          rtlzz_pipe_29_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:79:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:79:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :79:23
      rtlzz_pipe_29_s2 <= 1'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:79:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :79:23
      rtlzz_pipe_29_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_9_s1 < rtlzz_pipe_10_s1 : rtlzz_pipe_29_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:24:22, :27:23, :77:10, :79:23, :464:21
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_30_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:82:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:82:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :82:23
      rtlzz_pipe_30_s1 <= 16'hFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:82:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :82:23
      rtlzz_pipe_30_s1 <= __vul_port_iv ? __vul_port_input[15:0] : rtlzz_pipe_30_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:80:10, :82:23
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_31_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:85:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:85:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :85:23
      rtlzz_pipe_31_s1 <= 16'hFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:85:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :85:23
      rtlzz_pipe_31_s1 <= __vul_port_iv ? __vul_port_input[143:128] : rtlzz_pipe_31_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:83:10, :85:23
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_32_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:88:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:88:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :88:23
      rtlzz_pipe_32_s1 <= 16'hFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:88:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :88:23
      rtlzz_pipe_32_s1 <= __vul_port_iv ? __vul_port_input[271:256] : rtlzz_pipe_32_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:86:10, :88:23
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_33_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:91:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:91:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :91:23
      rtlzz_pipe_33_s1 <= 16'hFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:91:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :91:23
      rtlzz_pipe_33_s1 <= __vul_port_iv ? __vul_port_input[399:384] : rtlzz_pipe_33_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:89:10, :91:23
  end // always_ff @(posedge)
  wire [31:0]  _GEN_1 = {16'h0, rtlzz_pipe_30_s1} * {16'h0, rtlzz_pipe_31_s1};	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:82:23, :85:23, :93:10, :95:10, :96:10
  reg  [31:0]  rtlzz_pipe_34_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:98:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:98:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :98:23
      rtlzz_pipe_34_s2 <= 32'hFFFE0001;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:98:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :98:23
      rtlzz_pipe_34_s2 <= rtlzz_valid_s1 ? _GEN_1 : rtlzz_pipe_34_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:96:10, :98:23, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_35_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:105:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:105:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :105:23
      rtlzz_pipe_35_s2 <= 32'hFFFE0001;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:105:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :105:23
      rtlzz_pipe_35_s2 <=
        rtlzz_valid_s1
          ? {16'h0, rtlzz_pipe_32_s1} * {16'h0, rtlzz_pipe_33_s1}
          : rtlzz_pipe_35_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:88:23, :91:23, :100:10, :102:10, :103:10, :105:23, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_41_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:109:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:109:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :109:23
      rtlzz_pipe_41_s2 <= 32'hFFFE0000;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:108:10, :109:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :109:23
      rtlzz_pipe_41_s2 <=
        rtlzz_valid_s1 ? _GEN_1 + rtlzz_pipe_6_s1[31:0] : rtlzz_pipe_41_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:13:22, :96:10, :106:10, :107:10, :109:23, :464:21
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_42_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:112:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:112:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :112:23
      rtlzz_pipe_42_s2 <= 16'hFFFE;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:111:10, :112:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :112:23
      rtlzz_pipe_42_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_30_s1 + rtlzz_pipe_31_s1 : rtlzz_pipe_42_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:82:23, :85:23, :110:10, :112:23, :464:21
  end // always_ff @(posedge)
  reg  [16:0]  rtlzz_pipe_43_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:122:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:122:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :122:23
      rtlzz_pipe_43_s2 <= 17'h1FFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:121:10, :122:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :122:23
      rtlzz_pipe_43_s2 <=
        rtlzz_valid_s1
          ? {1'h0, rtlzz_pipe_30_s1} + {1'h0, rtlzz_pipe_31_s1} + {16'h0, rtlzz_pipe_8_s1}
          : rtlzz_pipe_43_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:21:22, :82:23, :85:23, :114:10, :116:10, :118:10, :119:10, :120:10, :122:23, :464:21
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_44_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:125:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:125:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :125:23
      rtlzz_pipe_44_s2 <= 16'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:125:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :125:23
      rtlzz_pipe_44_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_30_s1 - rtlzz_pipe_31_s1 : rtlzz_pipe_44_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:82:23, :85:23, :123:10, :125:23, :464:21
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_47_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:130:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:130:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :130:23
      rtlzz_pipe_47_s1 <= 16'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:130:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :130:23
      rtlzz_pipe_47_s1 <=
        __vul_port_iv
          ? __vul_port_input[15:0] & __vul_port_input[143:128]
            ^ (__vul_port_input[271:256] | __vul_port_input[399:384])
          : rtlzz_pipe_47_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:80:10, :83:10, :86:10, :89:10, :126:10, :127:10, :128:10, :130:23
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_47_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:132:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:132:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :132:23
      rtlzz_pipe_47_s2 <= 16'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:132:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :132:23
      rtlzz_pipe_47_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_47_s1 : rtlzz_pipe_47_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:130:23, :132:23, :464:21
  end // always_ff @(posedge)
  reg          rtlzz_pipe_50_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:135:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:135:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :135:23
      rtlzz_pipe_50_s2 <= 1'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:135:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :135:23
      rtlzz_pipe_50_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_30_s1 < rtlzz_pipe_31_s1 : rtlzz_pipe_50_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:82:23, :85:23, :133:11, :135:23, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_51_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:138:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:138:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :138:23
      rtlzz_pipe_51_s1 <= 32'hFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:138:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :138:23
      rtlzz_pipe_51_s1 <= __vul_port_iv ? __vul_port_input[31:0] : rtlzz_pipe_51_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:136:11, :138:23
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_52_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:141:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:141:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :141:23
      rtlzz_pipe_52_s1 <= 32'hFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:141:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :141:23
      rtlzz_pipe_52_s1 <= __vul_port_iv ? __vul_port_input[159:128] : rtlzz_pipe_52_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:139:11, :141:23
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_53_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:144:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:144:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :144:23
      rtlzz_pipe_53_s1 <= 32'hFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:144:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :144:23
      rtlzz_pipe_53_s1 <= __vul_port_iv ? __vul_port_input[287:256] : rtlzz_pipe_53_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:142:11, :144:23
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_54_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:147:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:147:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :147:23
      rtlzz_pipe_54_s1 <= 32'hFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:147:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :147:23
      rtlzz_pipe_54_s1 <= __vul_port_iv ? __vul_port_input[415:384] : rtlzz_pipe_54_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:145:11, :147:23
  end // always_ff @(posedge)
  wire [63:0]  _GEN_2 = {32'h0, rtlzz_pipe_51_s1} * {32'h0, rtlzz_pipe_52_s1};	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:138:23, :141:23, :149:11, :151:11, :152:11
  reg  [63:0]  rtlzz_pipe_55_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:154:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:154:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :154:23
      rtlzz_pipe_55_s2 <= 64'hFFFFFFFE00000001;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:154:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :154:23
      rtlzz_pipe_55_s2 <= rtlzz_valid_s1 ? _GEN_2 : rtlzz_pipe_55_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:152:11, :154:23, :464:21
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_56_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:161:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:161:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :161:23
      rtlzz_pipe_56_s2 <= 64'hFFFFFFFE00000001;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:161:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :161:23
      rtlzz_pipe_56_s2 <=
        rtlzz_valid_s1
          ? {32'h0, rtlzz_pipe_53_s1} * {32'h0, rtlzz_pipe_54_s1}
          : rtlzz_pipe_56_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:144:23, :147:23, :156:11, :158:11, :159:11, :161:23, :464:21
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_62_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:165:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:165:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :165:23
      rtlzz_pipe_62_s2 <= 64'hFFFFFFFE00000000;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:164:11, :165:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :165:23
      rtlzz_pipe_62_s2 <=
        rtlzz_valid_s1 ? _GEN_2 + rtlzz_pipe_6_s1[63:0] : rtlzz_pipe_62_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:13:22, :152:11, :162:11, :163:11, :165:23, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_63_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:168:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:168:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :168:23
      rtlzz_pipe_63_s2 <= 32'hFFFFFFFE;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:167:11, :168:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :168:23
      rtlzz_pipe_63_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_51_s1 + rtlzz_pipe_52_s1 : rtlzz_pipe_63_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:138:23, :141:23, :166:11, :168:23, :464:21
  end // always_ff @(posedge)
  reg  [32:0]  rtlzz_pipe_64_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:178:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:178:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :178:23
      rtlzz_pipe_64_s2 <= 33'h1FFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:177:11, :178:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :178:23
      rtlzz_pipe_64_s2 <=
        rtlzz_valid_s1
          ? {1'h0, rtlzz_pipe_51_s1} + {1'h0, rtlzz_pipe_52_s1} + {32'h0, rtlzz_pipe_8_s1}
          : rtlzz_pipe_64_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:21:22, :138:23, :141:23, :170:11, :172:11, :174:11, :175:11, :176:11, :178:23, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_65_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:181:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:181:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :181:23
      rtlzz_pipe_65_s2 <= 32'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:181:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :181:23
      rtlzz_pipe_65_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_51_s1 - rtlzz_pipe_52_s1 : rtlzz_pipe_65_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:138:23, :141:23, :179:11, :181:23, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_68_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:186:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:186:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :186:23
      rtlzz_pipe_68_s1 <= 32'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:186:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :186:23
      rtlzz_pipe_68_s1 <=
        __vul_port_iv
          ? __vul_port_input[31:0] & __vul_port_input[159:128]
            ^ (__vul_port_input[287:256] | __vul_port_input[415:384])
          : rtlzz_pipe_68_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:136:11, :139:11, :142:11, :145:11, :182:11, :183:11, :184:11, :186:23
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_68_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:188:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:188:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :188:23
      rtlzz_pipe_68_s2 <= 32'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:188:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :188:23
      rtlzz_pipe_68_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_68_s1 : rtlzz_pipe_68_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:186:23, :188:23, :464:21
  end // always_ff @(posedge)
  reg          rtlzz_pipe_71_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:191:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:191:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :191:23
      rtlzz_pipe_71_s2 <= 1'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:191:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :191:23
      rtlzz_pipe_71_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_51_s1 < rtlzz_pipe_52_s1 : rtlzz_pipe_71_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:138:23, :141:23, :189:11, :191:23, :464:21
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_72_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:194:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:194:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :194:23
      rtlzz_pipe_72_s1 <= 64'hFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:194:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :194:23
      rtlzz_pipe_72_s1 <= __vul_port_iv ? __vul_port_input[63:0] : rtlzz_pipe_72_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:192:11, :194:23
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_73_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:197:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:197:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :197:23
      rtlzz_pipe_73_s1 <= 64'hFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:197:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :197:23
      rtlzz_pipe_73_s1 <= __vul_port_iv ? __vul_port_input[191:128] : rtlzz_pipe_73_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:195:11, :197:23
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_74_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:200:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:200:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :200:23
      rtlzz_pipe_74_s1 <= 64'hFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:200:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :200:23
      rtlzz_pipe_74_s1 <= __vul_port_iv ? __vul_port_input[319:256] : rtlzz_pipe_74_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:198:11, :200:23
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_75_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:203:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:203:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :203:23
      rtlzz_pipe_75_s1 <= 64'hFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:203:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :203:23
      rtlzz_pipe_75_s1 <= __vul_port_iv ? __vul_port_input[447:384] : rtlzz_pipe_75_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:201:11, :203:23
  end // always_ff @(posedge)
  wire [127:0] _GEN_3 = {64'h0, rtlzz_pipe_72_s1} * {64'h0, rtlzz_pipe_73_s1};	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:194:23, :197:23, :205:11, :207:11, :208:11
  reg  [127:0] rtlzz_pipe_76_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:210:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:210:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :210:23
      rtlzz_pipe_76_s2 <= 128'hFFFFFFFFFFFFFFFE0000000000000001;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:210:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :210:23
      rtlzz_pipe_76_s2 <= rtlzz_valid_s1 ? _GEN_3 : rtlzz_pipe_76_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:208:11, :210:23, :464:21
  end // always_ff @(posedge)
  reg  [127:0] rtlzz_pipe_77_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:217:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:217:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :217:23
      rtlzz_pipe_77_s2 <= 128'hFFFFFFFFFFFFFFFE0000000000000001;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:217:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :217:23
      rtlzz_pipe_77_s2 <=
        rtlzz_valid_s1
          ? {64'h0, rtlzz_pipe_74_s1} * {64'h0, rtlzz_pipe_75_s1}
          : rtlzz_pipe_77_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:200:23, :203:23, :212:11, :214:11, :215:11, :217:23, :464:21
  end // always_ff @(posedge)
  reg  [127:0] rtlzz_pipe_83_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:221:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:221:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :221:23
      rtlzz_pipe_83_s2 <= 128'hFFFFFFFFFFFFFFFE0000000000000000;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:220:11, :221:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :221:23
      rtlzz_pipe_83_s2 <=
        rtlzz_valid_s1 ? _GEN_3 + rtlzz_pipe_6_s1[127:0] : rtlzz_pipe_83_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:13:22, :208:11, :218:11, :219:11, :221:23, :464:21
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_84_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:224:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:224:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :224:23
      rtlzz_pipe_84_s2 <= 64'hFFFFFFFFFFFFFFFE;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:223:11, :224:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :224:23
      rtlzz_pipe_84_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_72_s1 + rtlzz_pipe_73_s1 : rtlzz_pipe_84_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:194:23, :197:23, :222:11, :224:23, :464:21
  end // always_ff @(posedge)
  reg  [64:0]  rtlzz_pipe_85_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:234:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:234:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :234:23
      rtlzz_pipe_85_s2 <= 65'h1FFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:233:11, :234:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :234:23
      rtlzz_pipe_85_s2 <=
        rtlzz_valid_s1
          ? {1'h0, rtlzz_pipe_72_s1} + {1'h0, rtlzz_pipe_73_s1} + {64'h0, rtlzz_pipe_8_s1}
          : rtlzz_pipe_85_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:21:22, :194:23, :197:23, :226:11, :228:11, :230:11, :231:11, :232:11, :234:23, :464:21
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_86_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:237:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:237:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :237:23
      rtlzz_pipe_86_s2 <= 64'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:237:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :237:23
      rtlzz_pipe_86_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_72_s1 - rtlzz_pipe_73_s1 : rtlzz_pipe_86_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:194:23, :197:23, :235:11, :237:23, :464:21
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_89_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:242:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:242:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :242:23
      rtlzz_pipe_89_s1 <= 64'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:242:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :242:23
      rtlzz_pipe_89_s1 <=
        __vul_port_iv
          ? __vul_port_input[63:0] & __vul_port_input[191:128]
            ^ (__vul_port_input[319:256] | __vul_port_input[447:384])
          : rtlzz_pipe_89_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:192:11, :195:11, :198:11, :201:11, :238:11, :239:11, :240:11, :242:23
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_89_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:244:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:244:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :244:23
      rtlzz_pipe_89_s2 <= 64'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:244:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :244:23
      rtlzz_pipe_89_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_89_s1 : rtlzz_pipe_89_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:242:23, :244:23, :464:21
  end // always_ff @(posedge)
  reg          rtlzz_pipe_92_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:247:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:247:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :247:23
      rtlzz_pipe_92_s2 <= 1'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:247:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :247:23
      rtlzz_pipe_92_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_72_s1 < rtlzz_pipe_73_s1 : rtlzz_pipe_92_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:194:23, :197:23, :245:11, :247:23, :464:21
  end // always_ff @(posedge)
  reg  [255:0] rtlzz_pipe_93_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:254:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:254:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :254:23
      rtlzz_pipe_93_s1 <=
        256'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE00000000000000000000000000000001;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:254:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :254:23
      rtlzz_pipe_93_s1 <=
        __vul_port_iv
          ? {128'h0, __vul_port_input[127:0]} * {128'h0, __vul_port_input[255:128]}
          : rtlzz_pipe_93_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:5:9, :8:9, :249:11, :251:11, :252:11, :254:23
  end // always_ff @(posedge)
  reg  [255:0] rtlzz_pipe_93_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:256:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:256:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :256:23
      rtlzz_pipe_93_s2 <=
        256'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE00000000000000000000000000000001;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:256:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :256:23
      rtlzz_pipe_93_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_93_s1 : rtlzz_pipe_93_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:254:23, :256:23, :464:21
  end // always_ff @(posedge)
  reg  [255:0] rtlzz_pipe_94_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:263:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:263:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :263:23
      rtlzz_pipe_94_s1 <=
        256'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE00000000000000000000000000000001;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:263:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :263:23
      rtlzz_pipe_94_s1 <=
        __vul_port_iv
          ? {128'h0, __vul_port_input[383:256]} * {128'h0, __vul_port_input[511:384]}
          : rtlzz_pipe_94_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:28:10, :32:10, :258:11, :260:11, :261:11, :263:23
  end // always_ff @(posedge)
  reg  [256:0] rtlzz_pipe_98_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:270:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:270:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :270:23
      rtlzz_pipe_98_s2 <=
        257'h1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC00000000000000000000000000000002;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:269:11, :270:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :270:23
      rtlzz_pipe_98_s2 <=
        rtlzz_valid_s1
          ? {1'h0, rtlzz_pipe_93_s1} + {1'h0, rtlzz_pipe_94_s1}
          : rtlzz_pipe_98_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:254:23, :263:23, :265:11, :267:11, :268:11, :270:23, :464:21
  end // always_ff @(posedge)
  reg  [255:0] rtlzz_pipe_99_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:273:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:273:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :273:23
      rtlzz_pipe_99_s2 <=
        256'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE00000000000000000000000000000000;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:272:11, :273:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :273:23
      rtlzz_pipe_99_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_93_s1 + rtlzz_pipe_6_s1 : rtlzz_pipe_99_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:13:22, :254:23, :271:11, :273:23, :464:21
  end // always_ff @(posedge)
  reg  [127:0] rtlzz_pipe_100_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:276:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:276:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :276:24
      rtlzz_pipe_100_s2 <= 128'hFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:275:11, :276:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :276:24
      rtlzz_pipe_100_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_2_s1 + rtlzz_pipe_3_s1 : rtlzz_pipe_100_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:7:22, :10:22, :274:11, :276:24, :464:21
  end // always_ff @(posedge)
  reg  [128:0] rtlzz_pipe_101_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:286:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:286:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :286:24
      rtlzz_pipe_101_s2 <= 129'h1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:285:11, :286:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :286:24
      rtlzz_pipe_101_s2 <=
        rtlzz_valid_s1
          ? {1'h0, rtlzz_pipe_2_s1} + {1'h0, rtlzz_pipe_3_s1} + {128'h0, rtlzz_pipe_8_s1}
          : rtlzz_pipe_101_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:7:22, :10:22, :21:22, :278:11, :280:11, :282:11, :283:11, :284:11, :286:24, :464:21
  end // always_ff @(posedge)
  reg  [127:0] rtlzz_pipe_102_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:289:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:289:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :289:24
      rtlzz_pipe_102_s2 <= 128'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:289:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :289:24
      rtlzz_pipe_102_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_2_s1 - rtlzz_pipe_3_s1 : rtlzz_pipe_102_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:7:22, :10:22, :287:11, :289:24, :464:21
  end // always_ff @(posedge)
  reg  [127:0] rtlzz_pipe_105_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:294:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:294:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :294:24
      rtlzz_pipe_105_s1 <= 128'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:294:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :294:24
      rtlzz_pipe_105_s1 <=
        __vul_port_iv
          ? __vul_port_input[127:0] & __vul_port_input[255:128]
            ^ (__vul_port_input[383:256] | __vul_port_input[511:384])
          : rtlzz_pipe_105_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:5:9, :8:9, :28:10, :32:10, :290:11, :291:11, :292:11, :294:24
  end // always_ff @(posedge)
  reg  [127:0] rtlzz_pipe_105_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:296:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:296:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :296:24
      rtlzz_pipe_105_s2 <= 128'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:296:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :296:24
      rtlzz_pipe_105_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_105_s1 : rtlzz_pipe_105_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:294:24, :296:24, :464:21
  end // always_ff @(posedge)
  reg          rtlzz_pipe_108_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:299:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:299:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :299:24
      rtlzz_pipe_108_s2 <= 1'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:299:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :299:24
      rtlzz_pipe_108_s2 <=
        rtlzz_valid_s1 ? rtlzz_pipe_2_s1 < rtlzz_pipe_3_s1 : rtlzz_pipe_108_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:7:22, :10:22, :297:11, :299:24, :464:21
  end // always_ff @(posedge)
  wire [31:0]  _GEN_4 = {29'h0, __vul_port_input[1027:1025]};	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:306:11
  reg  [31:0]  rtlzz_pipe_123_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:308:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:308:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :308:24
      rtlzz_pipe_123_s1 <= 32'h7;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:308:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :308:24
      rtlzz_pipe_123_s1 <= __vul_port_iv ? _GEN_4 : rtlzz_pipe_123_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:306:11, :308:24
  end // always_ff @(posedge)
  reg  [7:0]   rtlzz_pipe_27_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:316:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:316:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :316:23
      rtlzz_pipe_27_s2 <= 8'h80;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:315:11, :316:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :316:23
      rtlzz_pipe_27_s2 <=
        rtlzz_valid_s1
          ? ((|(rtlzz_pipe_123_s1[31:3]))
               ? 8'h0
               : rtlzz_pipe_9_s1 << rtlzz_pipe_123_s1[7:0])
          : rtlzz_pipe_27_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:24:22, :308:24, :309:11, :310:11, :312:11, :314:11, :316:23, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_122_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:324:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:324:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :324:24
      rtlzz_pipe_122_s1 <= 32'h7;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:324:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :324:24
      rtlzz_pipe_122_s1 <= __vul_port_iv ? _GEN_4 : rtlzz_pipe_122_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:306:11, :324:24
  end // always_ff @(posedge)
  reg  [7:0]   rtlzz_pipe_28_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:332:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:332:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :332:23
      rtlzz_pipe_28_s2 <= 8'h1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:331:11, :332:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :332:23
      rtlzz_pipe_28_s2 <=
        rtlzz_valid_s1
          ? ((|(rtlzz_pipe_122_s1[31:3]))
               ? 8'h0
               : rtlzz_pipe_9_s1 >> rtlzz_pipe_122_s1[7:0])
          : rtlzz_pipe_28_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:24:22, :324:24, :325:11, :326:11, :328:11, :330:11, :332:23, :464:21
  end // always_ff @(posedge)
  wire [31:0]  _GEN_5 = {28'h0, __vul_port_input[1028:1025]};	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:338:11
  reg  [31:0]  rtlzz_pipe_121_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:340:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:340:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :340:24
      rtlzz_pipe_121_s1 <= 32'hF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:340:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :340:24
      rtlzz_pipe_121_s1 <= __vul_port_iv ? _GEN_5 : rtlzz_pipe_121_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:338:11, :340:24
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_48_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:348:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:348:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :348:23
      rtlzz_pipe_48_s2 <= 16'h8000;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:347:11, :348:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :348:23
      rtlzz_pipe_48_s2 <=
        rtlzz_valid_s1
          ? ((|(rtlzz_pipe_121_s1[31:4]))
               ? 16'h0
               : rtlzz_pipe_30_s1 << rtlzz_pipe_121_s1[15:0])
          : rtlzz_pipe_48_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:82:23, :340:24, :341:11, :342:11, :344:11, :346:11, :348:23, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_120_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:356:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:356:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :356:24
      rtlzz_pipe_120_s1 <= 32'hF;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:356:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :356:24
      rtlzz_pipe_120_s1 <= __vul_port_iv ? _GEN_5 : rtlzz_pipe_120_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:338:11, :356:24
  end // always_ff @(posedge)
  reg  [15:0]  rtlzz_pipe_49_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:364:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:364:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :364:23
      rtlzz_pipe_49_s2 <= 16'h1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:363:11, :364:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :364:23
      rtlzz_pipe_49_s2 <=
        rtlzz_valid_s1
          ? ((|(rtlzz_pipe_120_s1[31:4]))
               ? 16'h0
               : rtlzz_pipe_30_s1 >> rtlzz_pipe_120_s1[15:0])
          : rtlzz_pipe_49_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:82:23, :356:24, :357:11, :358:11, :360:11, :362:11, :364:23, :464:21
  end // always_ff @(posedge)
  wire [31:0]  _GEN_6 = {27'h0, __vul_port_input[1029:1025]};	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:370:11
  reg  [31:0]  rtlzz_pipe_119_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:372:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:372:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :372:24
      rtlzz_pipe_119_s1 <= 32'h1F;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:372:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :372:24
      rtlzz_pipe_119_s1 <= __vul_port_iv ? _GEN_6 : rtlzz_pipe_119_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:370:11, :372:24
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_69_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:379:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:379:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :379:23
      rtlzz_pipe_69_s2 <= 32'h80000000;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:378:11, :379:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :379:23
      rtlzz_pipe_69_s2 <=
        rtlzz_valid_s1
          ? ((|(rtlzz_pipe_119_s1[31:5])) ? 32'h0 : rtlzz_pipe_51_s1 << rtlzz_pipe_119_s1)
          : rtlzz_pipe_69_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:138:23, :372:24, :373:11, :375:11, :377:11, :379:23, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_118_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:387:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:387:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :387:24
      rtlzz_pipe_118_s1 <= 32'h1F;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:387:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :387:24
      rtlzz_pipe_118_s1 <= __vul_port_iv ? _GEN_6 : rtlzz_pipe_118_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:370:11, :387:24
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_70_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:394:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:394:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :394:23
      rtlzz_pipe_70_s2 <= 32'h1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:393:11, :394:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :394:23
      rtlzz_pipe_70_s2 <=
        rtlzz_valid_s1
          ? ((|(rtlzz_pipe_118_s1[31:5])) ? 32'h0 : rtlzz_pipe_51_s1 >> rtlzz_pipe_118_s1)
          : rtlzz_pipe_70_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:138:23, :387:24, :388:11, :390:11, :392:11, :394:23, :464:21
  end // always_ff @(posedge)
  wire [31:0]  _GEN_7 = {26'h0, __vul_port_input[1030:1025]};	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:400:11
  reg  [31:0]  rtlzz_pipe_117_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:402:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:402:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :402:24
      rtlzz_pipe_117_s1 <= 32'h3F;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:402:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :402:24
      rtlzz_pipe_117_s1 <= __vul_port_iv ? _GEN_7 : rtlzz_pipe_117_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:400:11, :402:24
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_90_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:411:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:411:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :411:23
      rtlzz_pipe_90_s2 <= 64'h8000000000000000;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:410:11, :411:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :411:23
      rtlzz_pipe_90_s2 <=
        rtlzz_valid_s1
          ? ((|(rtlzz_pipe_117_s1[31:6])) ? 64'h0 : rtlzz_pipe_72_s1 << rtlzz_pipe_117_s1)
          : rtlzz_pipe_90_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:194:23, :402:24, :405:11, :407:11, :409:11, :411:23, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_116_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:419:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:419:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :419:24
      rtlzz_pipe_116_s1 <= 32'h3F;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:419:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :419:24
      rtlzz_pipe_116_s1 <= __vul_port_iv ? _GEN_7 : rtlzz_pipe_116_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:400:11, :419:24
  end // always_ff @(posedge)
  reg  [63:0]  rtlzz_pipe_91_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:428:23
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:428:23
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :428:23
      rtlzz_pipe_91_s2 <= 64'h1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:427:11, :428:23
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :428:23
      rtlzz_pipe_91_s2 <=
        rtlzz_valid_s1
          ? ((|(rtlzz_pipe_116_s1[31:6])) ? 64'h0 : rtlzz_pipe_72_s1 >> rtlzz_pipe_116_s1)
          : rtlzz_pipe_91_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:194:23, :419:24, :422:11, :424:11, :426:11, :428:23, :464:21
  end // always_ff @(posedge)
  wire [31:0]  _GEN_8 = {25'h0, __vul_port_input[1031:1025]};	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:434:11
  reg  [31:0]  rtlzz_pipe_115_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:436:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:436:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :436:24
      rtlzz_pipe_115_s1 <= 32'h7F;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:436:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :436:24
      rtlzz_pipe_115_s1 <= __vul_port_iv ? _GEN_8 : rtlzz_pipe_115_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:434:11, :436:24
  end // always_ff @(posedge)
  reg  [127:0] rtlzz_pipe_106_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:445:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:445:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :445:24
      rtlzz_pipe_106_s2 <= 128'h80000000000000000000000000000000;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:444:11, :445:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :445:24
      rtlzz_pipe_106_s2 <=
        rtlzz_valid_s1
          ? ((|(rtlzz_pipe_115_s1[31:7])) ? 128'h0 : rtlzz_pipe_2_s1 << rtlzz_pipe_115_s1)
          : rtlzz_pipe_106_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:7:22, :436:24, :439:11, :441:11, :443:11, :445:24, :464:21
  end // always_ff @(posedge)
  reg  [31:0]  rtlzz_pipe_114_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:453:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:453:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :453:24
      rtlzz_pipe_114_s1 <= 32'h7F;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:453:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :453:24
      rtlzz_pipe_114_s1 <= __vul_port_iv ? _GEN_8 : rtlzz_pipe_114_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:434:11, :453:24
  end // always_ff @(posedge)
  reg  [127:0] rtlzz_pipe_107_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:462:24
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:462:24
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :462:24
      rtlzz_pipe_107_s2 <= 128'h1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:461:11, :462:24
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :462:24
      rtlzz_pipe_107_s2 <=
        rtlzz_valid_s1
          ? ((|(rtlzz_pipe_114_s1[31:7])) ? 128'h0 : rtlzz_pipe_2_s1 >> rtlzz_pipe_114_s1)
          : rtlzz_pipe_107_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:7:22, :453:24, :456:11, :458:11, :460:11, :462:24, :464:21
  end // always_ff @(posedge)
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:464:21
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :464:21
      rtlzz_valid_s1 <= 1'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:464:21
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :464:21
      rtlzz_valid_s1 <= __vul_port_iv;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:464:21
  end // always_ff @(posedge)
  reg          rtlzz_valid_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:466:21
  always_ff @(posedge __vul_pipeline_clk) begin	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:466:21
    if (_GEN)	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :466:21
      rtlzz_valid_s2 <= 1'h0;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:466:21
    else	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:4:9, :466:21
      rtlzz_valid_s2 <= rtlzz_valid_s1;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:464:21, :466:21
  end // always_ff @(posedge)
  assign __vul_port_output =
    {513'h1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC00000000000000000000000000000003FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE00000000000000000000000000000001,
     rtlzz_pipe_98_s2 ^ rtlzz_pipe_7_s2,
     rtlzz_pipe_7_s2,
     rtlzz_pipe_108_s2,
     rtlzz_pipe_107_s2,
     rtlzz_pipe_106_s2,
     rtlzz_pipe_105_s2,
     rtlzz_pipe_102_s2,
     rtlzz_pipe_101_s2,
     rtlzz_pipe_100_s2,
     rtlzz_pipe_99_s2,
     rtlzz_pipe_98_s2,
     rtlzz_pipe_93_s2[127:0],
     rtlzz_pipe_93_s2,
     rtlzz_pipe_92_s2,
     rtlzz_pipe_91_s2,
     rtlzz_pipe_90_s2,
     rtlzz_pipe_89_s2,
     rtlzz_pipe_86_s2,
     rtlzz_pipe_85_s2,
     rtlzz_pipe_84_s2,
     rtlzz_pipe_83_s2,
     {1'h0, rtlzz_pipe_76_s2} + {1'h0, rtlzz_pipe_77_s2},
     rtlzz_pipe_76_s2[63:0],
     rtlzz_pipe_76_s2,
     rtlzz_pipe_71_s2,
     rtlzz_pipe_70_s2,
     rtlzz_pipe_69_s2,
     rtlzz_pipe_68_s2,
     rtlzz_pipe_65_s2,
     rtlzz_pipe_64_s2,
     rtlzz_pipe_63_s2,
     rtlzz_pipe_62_s2,
     {1'h0, rtlzz_pipe_55_s2} + {1'h0, rtlzz_pipe_56_s2},
     rtlzz_pipe_55_s2[31:0],
     rtlzz_pipe_55_s2,
     rtlzz_pipe_50_s2,
     rtlzz_pipe_49_s2,
     rtlzz_pipe_48_s2,
     rtlzz_pipe_47_s2,
     rtlzz_pipe_44_s2,
     rtlzz_pipe_43_s2,
     rtlzz_pipe_42_s2,
     rtlzz_pipe_41_s2,
     {1'h0, rtlzz_pipe_34_s2} + {1'h0, rtlzz_pipe_35_s2},
     rtlzz_pipe_34_s2[15:0],
     rtlzz_pipe_34_s2,
     rtlzz_pipe_29_s2,
     rtlzz_pipe_28_s2,
     rtlzz_pipe_27_s2,
     rtlzz_pipe_26_s2,
     rtlzz_pipe_23_s2,
     rtlzz_pipe_22_s2,
     rtlzz_pipe_21_s2,
     rtlzz_pipe_20_s2,
     {1'h0, rtlzz_pipe_13_s2} + {1'h0, rtlzz_pipe_14_s2},
     rtlzz_pipe_13_s2[7:0],
     rtlzz_pipe_13_s2};	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:18:22, :42:23, :49:23, :53:23, :56:23, :66:23, :69:23, :76:23, :79:23, :98:23, :105:23, :109:23, :112:23, :122:23, :125:23, :132:23, :135:23, :154:23, :161:23, :165:23, :168:23, :178:23, :181:23, :188:23, :191:23, :210:23, :217:23, :221:23, :224:23, :234:23, :237:23, :244:23, :247:23, :256:23, :270:23, :273:23, :276:24, :286:24, :289:24, :296:24, :299:24, :316:23, :332:23, :348:23, :364:23, :379:23, :394:23, :411:23, :428:23, :445:24, :462:24, :469:11, :470:11, :482:11, :494:11, :496:11, :497:11, :499:11, :511:11, :513:11, :514:11, :516:11, :528:11, :530:11, :531:11, :533:11, :545:11, :547:11, :548:11, :550:11, :552:11, :553:3
  assign __vul_port_ov = rtlzz_valid_s2;	// /tmp/rtlzz-circt-361-1845730157191782/input.mlir:466:21, :553:3
end

  logic [4265:0] rdata_output__;
  assign rdata_output__ = __vul_pipeline_q_output;
  logic rdata_ov__;
  assign rdata_ov__ = __vul_pipeline_q_ov;


  wire [255:0] _GEN =
    {128'h0, combine_value__[127:0]} * {128'h0, combine_value__[255:128]};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:147:11, :149:11, :150:11, :152:11, :153:11
  wire [256:0] _GEN_0 =
    {1'h0, _GEN}
    + {1'h0, {128'h0, combine_value__[383:256]} * {128'h0, combine_value__[511:384]}};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:153:11, :155:11, :156:11, :158:11, :159:11, :161:11, :162:11, :164:11, :165:11
  wire [127:0] _GEN_1 = {121'h0, combine_value__[1031:1025]};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:178:11, :180:11
  wire [63:0]  _GEN_2 = {58'h0, combine_value__[1030:1025]};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:235:11, :237:11
  wire [127:0] _GEN_3 =
    {64'h0, combine_value__[63:0]} * {64'h0, combine_value__[191:128]};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:226:11, :227:11, :278:11, :280:11, :281:11
  wire [31:0]  _GEN_4 = {27'h0, combine_value__[1029:1025]};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:308:11
  wire [63:0]  _GEN_5 =
    {32'h0, combine_value__[31:0]} * {32'h0, combine_value__[159:128]};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:299:11, :300:11, :347:11, :349:11, :350:11
  wire [15:0]  _GEN_6 = {12'h0, combine_value__[1028:1025]};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:377:11, :378:11
  wire [31:0]  _GEN_7 =
    {16'h0, combine_value__[15:0]} * {16'h0, combine_value__[143:128]};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:368:11, :369:11, :418:11, :420:11, :421:11
  wire [7:0]   _GEN_8 = {5'h0, combine_value__[1027:1025]};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:448:11, :449:11
  wire [15:0]  _GEN_9 = {8'h0, combine_value__[7:0]} * {8'h0, combine_value__[135:128]};	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:439:11, :440:11, :489:11, :491:11, :492:11
  assign valid__query__ = rdata_ov__;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:533:3
  assign result__query__ = rdata_output__;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:533:3
  assign echo257_result__ = echo257__vld__ ? echo257_value__ : 257'h0;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:119:11, :123:11, :533:3
  assign echo256_result__ = echo256__vld__ ? echo256_value__ : 256'h0;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:124:11, :128:11, :533:3
  assign echo193_result__ = echo193__vld__ ? echo193_value__ : 193'h0;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:129:11, :133:11, :533:3
  assign echo128_result__ = echo128__vld__ ? echo128_value__ : 128'h0;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:138:11, :533:3
  assign echo129_result__ = echo129__vld__ ? echo129_value__ : 129'h0;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:139:11, :143:11, :533:3
  assign combine_result__ =
    combine__vld__
      ? {513'h1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC00000000000000000000000000000003FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE00000000000000000000000000000001,
         _GEN_0 ^ combine_value__[1024:768],
         combine_value__[1024:768],
         combine_value__[127:0] < combine_value__[255:128],
         combine_value__[127:0] >> _GEN_1,
         combine_value__[127:0] << _GEN_1,
         combine_value__[127:0] & combine_value__[255:128]
           ^ (combine_value__[383:256] | combine_value__[511:384]),
         combine_value__[127:0] - combine_value__[255:128],
         {1'h0, combine_value__[127:0]} + {1'h0, combine_value__[255:128]}
           + {128'h0, combine_value__[1033]},
         combine_value__[127:0] + combine_value__[255:128],
         _GEN + combine_value__[767:512],
         _GEN_0,
         _GEN[127:0],
         _GEN,
         combine_value__[63:0] < combine_value__[191:128],
         combine_value__[63:0] >> _GEN_2,
         combine_value__[63:0] << _GEN_2,
         combine_value__[63:0] & combine_value__[191:128]
           ^ (combine_value__[319:256] | combine_value__[447:384]),
         combine_value__[63:0] - combine_value__[191:128],
         {1'h0, combine_value__[63:0]} + {1'h0, combine_value__[191:128]}
           + {64'h0, combine_value__[1033]},
         combine_value__[63:0] + combine_value__[191:128],
         _GEN_3 + combine_value__[639:512],
         {1'h0, _GEN_3}
           + {1'h0,
              {64'h0, combine_value__[319:256]} * {64'h0, combine_value__[447:384]}},
         _GEN_3[63:0],
         _GEN_3,
         combine_value__[31:0] < combine_value__[159:128],
         combine_value__[31:0] >> _GEN_4,
         combine_value__[31:0] << _GEN_4,
         combine_value__[31:0] & combine_value__[159:128]
           ^ (combine_value__[287:256] | combine_value__[415:384]),
         combine_value__[31:0] - combine_value__[159:128],
         {1'h0, combine_value__[31:0]} + {1'h0, combine_value__[159:128]}
           + {32'h0, combine_value__[1033]},
         combine_value__[31:0] + combine_value__[159:128],
         _GEN_5 + combine_value__[575:512],
         {1'h0, _GEN_5}
           + {1'h0,
              {32'h0, combine_value__[287:256]} * {32'h0, combine_value__[415:384]}},
         _GEN_5[31:0],
         _GEN_5,
         combine_value__[15:0] < combine_value__[143:128],
         combine_value__[15:0] >> _GEN_6,
         combine_value__[15:0] << _GEN_6,
         combine_value__[15:0] & combine_value__[143:128]
           ^ (combine_value__[271:256] | combine_value__[399:384]),
         combine_value__[15:0] - combine_value__[143:128],
         {1'h0, combine_value__[15:0]} + {1'h0, combine_value__[143:128]}
           + {16'h0, combine_value__[1033]},
         combine_value__[15:0] + combine_value__[143:128],
         _GEN_7 + combine_value__[543:512],
         {1'h0, _GEN_7}
           + {1'h0,
              {16'h0, combine_value__[271:256]} * {16'h0, combine_value__[399:384]}},
         _GEN_7[15:0],
         _GEN_7,
         combine_value__[7:0] < combine_value__[135:128],
         combine_value__[7:0] >> _GEN_8,
         combine_value__[7:0] << _GEN_8,
         combine_value__[7:0] & combine_value__[135:128]
           ^ (combine_value__[263:256] | combine_value__[391:384]),
         combine_value__[7:0] - combine_value__[135:128],
         {1'h0, combine_value__[7:0]} + {1'h0, combine_value__[135:128]}
           + {8'h0, combine_value__[1033]},
         combine_value__[7:0] + combine_value__[135:128],
         _GEN_9 + combine_value__[527:512],
         {1'h0, _GEN_9}
           + {1'h0, {8'h0, combine_value__[263:256]} * {8'h0, combine_value__[391:384]}},
         _GEN_9[7:0],
         _GEN_9}
      : 4266'h0;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:146:11, :147:11, :150:11, :153:11, :156:11, :159:11, :165:11, :166:11, :167:11, :170:11, :180:11, :181:11, :195:11, :201:11, :202:11, :203:11, :205:11, :208:11, :210:11, :211:11, :213:11, :214:11, :215:11, :217:11, :219:11, :220:11, :223:11, :226:11, :227:11, :228:11, :237:11, :238:11, :252:11, :258:11, :259:11, :260:11, :261:11, :262:11, :264:11, :267:11, :269:11, :271:11, :272:11, :273:11, :275:11, :281:11, :282:11, :283:11, :286:11, :288:11, :290:11, :291:11, :293:11, :294:11, :296:11, :299:11, :300:11, :301:11, :308:11, :309:11, :321:11, :327:11, :328:11, :329:11, :330:11, :331:11, :333:11, :336:11, :338:11, :340:11, :341:11, :342:11, :344:11, :350:11, :351:11, :352:11, :355:11, :357:11, :359:11, :360:11, :362:11, :363:11, :365:11, :368:11, :369:11, :370:11, :378:11, :379:11, :392:11, :398:11, :399:11, :400:11, :401:11, :402:11, :404:11, :407:11, :409:11, :411:11, :412:11, :413:11, :415:11, :421:11, :422:11, :423:11, :426:11, :428:11, :430:11, :431:11, :433:11, :434:11, :436:11, :439:11, :440:11, :441:11, :449:11, :450:11, :463:11, :469:11, :470:11, :471:11, :472:11, :473:11, :475:11, :478:11, :480:11, :482:11, :483:11, :484:11, :486:11, :492:11, :493:11, :494:11, :497:11, :499:11, :501:11, :502:11, :504:11, :505:11, :507:11, :509:11, :510:11, :514:11, :533:3
  assign wen_input__ = push__vld__;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:533:3
  assign wdata_input__ = push_value__;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:533:3
  assign resetvalue_input__ =
    1034'h2FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:530:11, :533:3
  assign wen_iv__ = push__vld__;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:533:3
  assign wdata_iv__ = push__vld__ & push_valid__;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:531:11, :533:3
  assign resetvalue_iv__ = 1'h0;	// /tmp/rtlzz-circt-361-1845731508811604/input.mlir:533:3
endmodule

