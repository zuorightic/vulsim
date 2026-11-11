`timescale 1ns/1ps

module Top_sim_top(
  input clk,
  input rstn,
  output [0:0] valid__query__,
  output [63:0] result__query__,
  input write_c__vld__,
  input [63:0] write_c_value__,
  input write_valid__vld__,
  input [0:0] write_valid_value__,
  input write_b__vld__,
  input [31:0] write_b_value__,
  input write_a__vld__,
  input [31:0] write_a_value__
);

reg [31:0] a;
wire [31:0] resetvalue_a__;
wire wen_a__;
wire [31:0] wdata_a__;
reg [31:0] b;
wire [31:0] resetvalue_b__;
wire wen_b__;
wire [31:0] wdata_b__;
reg [63:0] c;
wire [63:0] resetvalue_c__;
wire wen_c__;
wire [63:0] wdata_c__;
reg [0:0] iv;
wire [0:0] resetvalue_iv__;
wire wen_iv__;
wire [0:0] wdata_iv__;
reg [31:0] p00;
wire [31:0] resetvalue_p00__;
wire wen_p00__;
wire [31:0] wdata_p00__;
reg [31:0] p01;
wire [31:0] resetvalue_p01__;
wire wen_p01__;
wire [31:0] wdata_p01__;
reg [31:0] p10;
wire [31:0] resetvalue_p10__;
wire wen_p10__;
wire [31:0] wdata_p10__;
reg [31:0] p11;
wire [31:0] resetvalue_p11__;
wire wen_p11__;
wire [31:0] wdata_p11__;
reg [63:0] c_s1;
wire [63:0] resetvalue_c_s1__;
wire wen_c_s1__;
wire [63:0] wdata_c_s1__;
reg [0:0] v_s1;
wire [0:0] resetvalue_v_s1__;
wire wen_v_s1__;
wire [0:0] wdata_v_s1__;
reg [63:0] y;
wire [63:0] resetvalue_y__;
wire wen_y__;
wire [63:0] wdata_y__;
reg [0:0] ov;
wire [0:0] resetvalue_ov__;
wire wen_ov__;
wire [0:0] wdata_ov__;

always @(posedge clk) begin
  if (rstn == 0) begin
    a <= resetvalue_a__;
  end else begin
begin
    if (wen_a__) begin
      a <= wdata_a__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    b <= resetvalue_b__;
  end else begin
begin
    if (wen_b__) begin
      b <= wdata_b__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    c <= resetvalue_c__;
  end else begin
begin
    if (wen_c__) begin
      c <= wdata_c__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    iv <= resetvalue_iv__;
  end else begin
begin
    if (wen_iv__) begin
      iv <= wdata_iv__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    p00 <= resetvalue_p00__;
  end else begin
begin
    if (wen_p00__) begin
      p00 <= wdata_p00__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    p01 <= resetvalue_p01__;
  end else begin
begin
    if (wen_p01__) begin
      p01 <= wdata_p01__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    p10 <= resetvalue_p10__;
  end else begin
begin
    if (wen_p10__) begin
      p10 <= wdata_p10__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    p11 <= resetvalue_p11__;
  end else begin
begin
    if (wen_p11__) begin
      p11 <= wdata_p11__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    c_s1 <= resetvalue_c_s1__;
  end else begin
begin
    if (wen_c_s1__) begin
      c_s1 <= wdata_c_s1__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    v_s1 <= resetvalue_v_s1__;
  end else begin
begin
    if (wen_v_s1__) begin
      v_s1 <= wdata_v_s1__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    y <= resetvalue_y__;
  end else begin
begin
    if (wen_y__) begin
      y <= wdata_y__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    ov <= resetvalue_ov__;
  end else begin
begin
    if (wen_ov__) begin
      ov <= wdata_ov__;
    end
    end
  end
end


    logic [31:0] rdata_a__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:39:1-39:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:39:1-39:18
    logic [31:0] rdata_b__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:47:1-47:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:47:1-47:18
    logic [63:0] rdata_c__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:55:1-55:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:55:1-55:18
    logic rdata_iv__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:63:1-63:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:63:1-63:18
    logic [31:0] rdata_p00__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:71:1-71:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:71:1-71:20
    logic [31:0] rdata_p01__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:79:1-79:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:79:1-79:20
    logic [31:0] rdata_p10__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:87:1-87:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:87:1-87:20
    logic [31:0] rdata_p11__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:95:1-95:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:95:1-95:20
    logic [63:0] rdata_c_s1__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:103:1-103:21; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:103:1-103:21
    logic rdata_v_s1__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:111:1-111:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:111:1-111:20
    logic [63:0] rdata_y__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:119:1-119:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:119:1-119:18
    logic rdata_ov__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:127:1-127:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:127:1-127:18

    logic write_c__vld; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:23:1-23:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:23:1-23:20
    logic [63:0] write_c_value; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:25:1-25:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:25:1-25:24
    logic write_valid__vld; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:27:1-27:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:27:1-27:24
    logic write_valid_value; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:29:1-29:27; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:29:1-29:27
    logic write_b__vld; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:31:1-31:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:31:1-31:20
    logic [31:0] write_b_value; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:33:1-33:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:33:1-33:24
    logic write_a__vld; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:35:1-35:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:35:1-35:20
    logic [31:0] write_a_value; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:37:1-37:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:37:1-37:24
    logic [31:0] rdata_a; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:39:1-39:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:39:1-39:18
    logic [31:0] rdata_b; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:47:1-47:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:47:1-47:18
    logic [63:0] rdata_c; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:55:1-55:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:55:1-55:18
    logic rdata_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:63:1-63:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:63:1-63:18
    logic [31:0] rdata_p00; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:71:1-71:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:71:1-71:20
    logic [31:0] rdata_p01; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:79:1-79:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:79:1-79:20
    logic [31:0] rdata_p10; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:87:1-87:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:87:1-87:20
    logic [31:0] rdata_p11; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:95:1-95:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:95:1-95:20
    logic [63:0] rdata_c_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:103:1-103:21; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:103:1-103:21
    logic rdata_v_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:111:1-111:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:111:1-111:20
    logic [63:0] rdata_y; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:119:1-119:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:119:1-119:18
    logic rdata_ov; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:127:1-127:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:127:1-127:18
    logic wdata_iv___v3; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:67:1-67:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:241:3-241:30
    logic [31:0] s8_norm_mul_70_v0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:439:42-439:49; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:435:22-435:40
    logic [31:0] s8_norm_mul_77_v0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:440:42-440:49; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:435:22-435:40
    logic [31:0] s8_norm_mul_82_v0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:441:42-441:49; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:436:22-436:40
    logic [31:0] s8_norm_mul_86_v0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:442:42-442:49; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:436:22-436:40
    logic [47:0] s8_norm_shift_58_v0; // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:251:10-251:15
    logic [48:0] s8_norm_add_59_v0; // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:223:10-223:15
    logic [47:0] s8_norm_shift_67_v0; // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:209:10-209:15
    logic [63:0] s8_norm_shift_73_v0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:446:62-446:98; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:195:10-195:15
    logic valid__query; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:19:1-19:22; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:455:3-455:26
    logic [63:0] result__query; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:21:1-21:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:461:3-461:27
    logic wen_a; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:41:1-41:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:41:1-41:13
    logic [31:0] wdata_a; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:43:1-43:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:43:1-43:18
    logic [31:0] resetvalue_a; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:45:1-45:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:333:3-333:37
    logic wen_b; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:49:1-49:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:49:1-49:13
    logic [31:0] wdata_b; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:51:1-51:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:51:1-51:18
    logic [31:0] resetvalue_b; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:53:1-53:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:340:3-340:37
    logic wen_c; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:57:1-57:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:57:1-57:13
    logic [63:0] wdata_c; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:59:1-59:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:59:1-59:18
    logic [63:0] resetvalue_c; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:61:1-61:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:347:3-347:37
    logic wen_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:65:1-65:14; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:65:1-65:14
    logic wdata_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:67:1-67:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:67:1-67:18
    logic resetvalue_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:69:1-69:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:354:3-354:37
    logic wen_p00; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:73:1-73:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:73:1-73:15
    logic [31:0] wdata_p00; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:75:1-75:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:75:1-75:20
    logic [31:0] resetvalue_p00; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:77:1-77:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:361:3-361:41
    logic wen_p01; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:81:1-81:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:81:1-81:15
    logic [31:0] wdata_p01; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:83:1-83:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:83:1-83:20
    logic [31:0] resetvalue_p01; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:85:1-85:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:368:3-368:41
    logic wen_p10; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:89:1-89:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:89:1-89:15
    logic [31:0] wdata_p10; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:91:1-91:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:91:1-91:20
    logic [31:0] resetvalue_p10; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:93:1-93:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:375:3-375:41
    logic wen_p11; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:97:1-97:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:97:1-97:15
    logic [31:0] wdata_p11; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:99:1-99:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:99:1-99:20
    logic [31:0] resetvalue_p11; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:101:1-101:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:382:3-382:41
    logic wen_c_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:105:1-105:16; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:105:1-105:16
    logic [63:0] wdata_c_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:107:1-107:21; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:107:1-107:21
    logic [63:0] resetvalue_c_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:109:1-109:26; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:389:3-389:43
    logic wen_v_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:113:1-113:16; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:160:3-160:20
    logic wdata_v_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:115:1-115:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:159:3-159:33
    logic resetvalue_v_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:117:1-117:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:396:3-396:41
    logic wen_y; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:121:1-121:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:146:3-146:17
    logic [63:0] wdata_y; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:123:1-123:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:145:3-145:30
    logic [63:0] resetvalue_y; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:125:1-125:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:403:3-403:37
    logic wen_ov; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:129:1-129:14; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:174:3-174:18
    logic wdata_ov; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:131:1-131:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:173:3-173:31
    logic resetvalue_ov; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:133:1-133:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:410:3-410:37
    logic [31:0] __beopt_width_107; // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:291:3-291:21
    logic [31:0] __beopt_width_108; // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:277:3-277:21
    logic [63:0] __beopt_width_115; // decl: <none>; prim: <none>
    logic [47:0] __beopt_width_116; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_117; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_118; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_119; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_120; // decl: <none>; prim: <none>
    logic [15:0] __beopt_width_121; // decl: <none>; prim: <none>
    logic [15:0] __beopt_width_123; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_92; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62
    logic [63:0] __beopt_width_93; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62
    logic [63:0] __beopt_width_94; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62
    logic [31:0] __beopt_width_86; // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:47:1-47:18
    logic [31:0] __beopt_width_89; // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:39:1-39:18
    logic [31:0] __beopt_width_88; // decl: <none>; prim: <none>
    logic [31:0] __beopt_width_91; // decl: <none>; prim: <none>

    assign rdata_a__ = a;
    assign rdata_b__ = b;
    assign rdata_c__ = c;
    assign rdata_iv__ = iv;
    assign rdata_p00__ = p00;
    assign rdata_p01__ = p01;
    assign rdata_p10__ = p10;
    assign rdata_p11__ = p11;
    assign rdata_c_s1__ = c_s1;
    assign rdata_v_s1__ = v_s1;
    assign rdata_y__ = y;
    assign rdata_ov__ = ov;

    assign valid__query__ = valid__query; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:19:1-19:22; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:455:3-455:26
    assign result__query__ = result__query; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:21:1-21:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:461:3-461:27
    assign write_c__vld = write_c__vld__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:23:1-23:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:23:1-23:20
    assign write_c_value = write_c_value__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:25:1-25:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:25:1-25:24
    assign write_valid__vld = write_valid__vld__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:27:1-27:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:27:1-27:24
    assign write_valid_value = write_valid_value__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:29:1-29:27; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:29:1-29:27
    assign write_b__vld = write_b__vld__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:31:1-31:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:31:1-31:20
    assign write_b_value = write_b_value__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:33:1-33:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:33:1-33:24
    assign write_a__vld = write_a__vld__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:35:1-35:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:35:1-35:20
    assign write_a_value = write_a_value__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:37:1-37:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:37:1-37:24
    assign rdata_a = rdata_a__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:39:1-39:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:39:1-39:18
    assign wen_a__ = wen_a; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:41:1-41:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:41:1-41:13
    assign wdata_a__ = wdata_a; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:43:1-43:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:43:1-43:18
    assign resetvalue_a__ = resetvalue_a; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:45:1-45:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:333:3-333:37
    assign rdata_b = rdata_b__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:47:1-47:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:47:1-47:18
    assign wen_b__ = wen_b; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:49:1-49:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:49:1-49:13
    assign wdata_b__ = wdata_b; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:51:1-51:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:51:1-51:18
    assign resetvalue_b__ = resetvalue_b; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:53:1-53:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:340:3-340:37
    assign rdata_c = rdata_c__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:55:1-55:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:55:1-55:18
    assign wen_c__ = wen_c; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:57:1-57:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:57:1-57:13
    assign wdata_c__ = wdata_c; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:59:1-59:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:59:1-59:18
    assign resetvalue_c__ = resetvalue_c; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:61:1-61:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:347:3-347:37
    assign rdata_iv = rdata_iv__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:63:1-63:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:63:1-63:18
    assign wen_iv__ = wen_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:65:1-65:14; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:65:1-65:14
    assign wdata_iv__ = wdata_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:67:1-67:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:67:1-67:18
    assign resetvalue_iv__ = resetvalue_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:69:1-69:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:354:3-354:37
    assign rdata_p00 = rdata_p00__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:71:1-71:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:71:1-71:20
    assign wen_p00__ = wen_p00; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:73:1-73:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:73:1-73:15
    assign wdata_p00__ = wdata_p00; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:75:1-75:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:75:1-75:20
    assign resetvalue_p00__ = resetvalue_p00; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:77:1-77:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:361:3-361:41
    assign rdata_p01 = rdata_p01__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:79:1-79:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:79:1-79:20
    assign wen_p01__ = wen_p01; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:81:1-81:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:81:1-81:15
    assign wdata_p01__ = wdata_p01; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:83:1-83:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:83:1-83:20
    assign resetvalue_p01__ = resetvalue_p01; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:85:1-85:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:368:3-368:41
    assign rdata_p10 = rdata_p10__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:87:1-87:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:87:1-87:20
    assign wen_p10__ = wen_p10; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:89:1-89:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:89:1-89:15
    assign wdata_p10__ = wdata_p10; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:91:1-91:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:91:1-91:20
    assign resetvalue_p10__ = resetvalue_p10; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:93:1-93:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:375:3-375:41
    assign rdata_p11 = rdata_p11__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:95:1-95:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:95:1-95:20
    assign wen_p11__ = wen_p11; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:97:1-97:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:97:1-97:15
    assign wdata_p11__ = wdata_p11; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:99:1-99:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:99:1-99:20
    assign resetvalue_p11__ = resetvalue_p11; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:101:1-101:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:382:3-382:41
    assign rdata_c_s1 = rdata_c_s1__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:103:1-103:21; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:103:1-103:21
    assign wen_c_s1__ = wen_c_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:105:1-105:16; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:105:1-105:16
    assign wdata_c_s1__ = wdata_c_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:107:1-107:21; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:107:1-107:21
    assign resetvalue_c_s1__ = resetvalue_c_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:109:1-109:26; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:389:3-389:43
    assign rdata_v_s1 = rdata_v_s1__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:111:1-111:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:111:1-111:20
    assign wen_v_s1__ = wen_v_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:113:1-113:16; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:160:3-160:20
    assign wdata_v_s1__ = wdata_v_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:115:1-115:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:159:3-159:33
    assign resetvalue_v_s1__ = resetvalue_v_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:117:1-117:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:396:3-396:41
    assign rdata_y = rdata_y__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:119:1-119:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:119:1-119:18
    assign wen_y__ = wen_y; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:121:1-121:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:146:3-146:17
    assign wdata_y__ = wdata_y; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:123:1-123:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:145:3-145:30
    assign resetvalue_y__ = resetvalue_y; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:125:1-125:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:403:3-403:37
    assign rdata_ov = rdata_ov__; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:127:1-127:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:127:1-127:18
    assign wen_ov__ = wen_ov; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:129:1-129:14; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:174:3-174:18
    assign wdata_ov__ = wdata_ov; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:131:1-131:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:173:3-173:31
    assign resetvalue_ov__ = resetvalue_ov; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:133:1-133:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:410:3-410:37

    assign wdata_iv___v3 = (write_valid__vld & write_valid_value); // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:67:1-67:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:241:3-241:30
    assign s8_norm_mul_70_v0 = 32'(($unsigned(32'($unsigned(__beopt_width_107))) * $unsigned(32'($unsigned(__beopt_width_108))))); // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:439:42-439:49; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:435:22-435:40
    assign s8_norm_mul_77_v0 = 32'(($unsigned(32'($unsigned(__beopt_width_107))) * $unsigned(32'($unsigned(__beopt_width_86))))); // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:440:42-440:49; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:435:22-435:40
    assign s8_norm_mul_82_v0 = 32'(($unsigned(32'($unsigned(__beopt_width_89))) * $unsigned(32'($unsigned(__beopt_width_108))))); // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:441:42-441:49; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:436:22-436:40
    assign s8_norm_mul_86_v0 = 32'(($unsigned(32'($unsigned(__beopt_width_89))) * $unsigned(32'($unsigned(__beopt_width_86))))); // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:442:42-442:49; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:436:22-436:40
    assign s8_norm_shift_58_v0 = 48'((__beopt_width_115 << 5'h10)); // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:251:10-251:15
    assign s8_norm_add_59_v0 = (__beopt_width_116 + s8_norm_shift_58_v0); // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:223:10-223:15
    assign s8_norm_shift_67_v0 = 48'((__beopt_width_117 << 5'h10)); // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:209:10-209:15
    assign s8_norm_shift_73_v0 = (__beopt_width_118 << 6'h20); // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:446:62-446:98; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:195:10-195:15
    assign valid__query = rdata_ov; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:19:1-19:22; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:455:3-455:26
    assign result__query = rdata_y; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:21:1-21:24; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:461:3-461:27
    assign wen_a = write_a__vld; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:41:1-41:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:41:1-41:13
    assign wdata_a = write_a_value; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:43:1-43:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:43:1-43:18
    assign resetvalue_a = 32'h80000035; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:45:1-45:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:333:3-333:37
    assign wen_b = write_b__vld; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:49:1-49:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:49:1-49:13
    assign wdata_b = write_b_value; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:51:1-51:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:51:1-51:18
    assign resetvalue_b = 32'h80000035; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:53:1-53:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:340:3-340:37
    assign wen_c = write_c__vld; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:57:1-57:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:57:1-57:13
    assign wdata_c = write_c_value; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:59:1-59:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:59:1-59:18
    assign resetvalue_c = 64'h8000000000000035; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:61:1-61:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:347:3-347:37
    assign wen_iv = write_valid__vld; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:65:1-65:14; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:65:1-65:14
    assign wdata_iv = wdata_iv___v3; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:67:1-67:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:67:1-67:18
    assign resetvalue_iv = 1'h0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:69:1-69:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:354:3-354:37
    assign wen_p00 = rdata_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:73:1-73:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:73:1-73:15
    assign wdata_p00 = s8_norm_mul_70_v0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:75:1-75:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:75:1-75:20
    assign resetvalue_p00 = 32'haf9; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:77:1-77:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:361:3-361:41
    assign wen_p01 = rdata_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:81:1-81:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:81:1-81:15
    assign wdata_p01 = s8_norm_mul_77_v0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:83:1-83:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:83:1-83:20
    assign resetvalue_p01 = 32'h1a8000; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:85:1-85:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:368:3-368:41
    assign wen_p10 = rdata_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:89:1-89:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:89:1-89:15
    assign wdata_p10 = s8_norm_mul_82_v0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:91:1-91:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:91:1-91:20
    assign resetvalue_p10 = 32'h1a8000; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:93:1-93:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:375:3-375:41
    assign wen_p11 = rdata_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:97:1-97:15; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:97:1-97:15
    assign wdata_p11 = s8_norm_mul_86_v0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:99:1-99:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:99:1-99:20
    assign resetvalue_p11 = 32'h40000000; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:101:1-101:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:382:3-382:41
    assign wen_c_s1 = rdata_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:105:1-105:16; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:105:1-105:16
    assign wdata_c_s1 = rdata_c; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:107:1-107:21; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:107:1-107:21
    assign resetvalue_c_s1 = 64'h8000000000000035; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:109:1-109:26; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:389:3-389:43
    assign wen_v_s1 = 1'h1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:113:1-113:16; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:160:3-160:20
    assign wdata_v_s1 = rdata_iv; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:115:1-115:20; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:159:3-159:33
    assign resetvalue_v_s1 = 1'h0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:117:1-117:25; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:396:3-396:41
    assign wen_y = 1'h1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:121:1-121:13; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:146:3-146:17
    assign wdata_y = __beopt_width_94; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:123:1-123:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:145:3-145:30
    assign resetvalue_y = 64'hc000003500000b2e; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:125:1-125:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:403:3-403:37
    assign wen_ov = 1'h1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:129:1-129:14; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:174:3-174:18
    assign wdata_ov = rdata_v_s1; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:131:1-131:18; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:173:3-173:31
    assign resetvalue_ov = 1'h0; // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:133:1-133:23; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:410:3-410:37
    assign __beopt_width_107 = (rdata_a & 32'hffff); // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:291:3-291:21
    assign __beopt_width_108 = (rdata_b & 32'hffff); // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:277:3-277:21
    assign __beopt_width_115 = ({32'h0, rdata_p01}); // decl: <none>; prim: <none>
    assign __beopt_width_116 = ({16'h0, rdata_p00}); // decl: <none>; prim: <none>
    assign __beopt_width_117 = ({32'h0, rdata_p10}); // decl: <none>; prim: <none>
    assign __beopt_width_118 = ({32'h0, rdata_p11}); // decl: <none>; prim: <none>
    assign __beopt_width_119 = ({16'h0, s8_norm_shift_67_v0}); // decl: <none>; prim: <none>
    assign __beopt_width_120 = ({15'h0, s8_norm_add_59_v0}); // decl: <none>; prim: <none>
    assign __beopt_width_121 = rdata_b[31:16]; // decl: <none>; prim: <none>
    assign __beopt_width_123 = rdata_a[31:16]; // decl: <none>; prim: <none>
    assign __beopt_width_92 = (rdata_c_s1 + s8_norm_shift_73_v0); // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62
    assign __beopt_width_93 = (__beopt_width_119 + __beopt_width_92); // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62
    assign __beopt_width_94 = (__beopt_width_120 + __beopt_width_93); // decl: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:447:28-447:62
    assign __beopt_width_86 = (__beopt_width_88 & 32'hffff); // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:47:1-47:18
    assign __beopt_width_89 = (__beopt_width_91 & 32'hffff); // decl: <none>; prim: /home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/generated/sim/top.logic.cpp:39:1-39:18
    assign __beopt_width_88 = ({16'h0, __beopt_width_121}); // decl: <none>; prim: <none>
    assign __beopt_width_91 = ({16'h0, __beopt_width_123}); // decl: <none>; prim: <none>
endmodule

