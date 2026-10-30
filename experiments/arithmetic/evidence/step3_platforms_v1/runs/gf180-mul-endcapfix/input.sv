`timescale 1ns/1ps

module MulProbe_sim_top(
  input clk,
  input rstn,
  output s3output__vld__,
  output [63:0] s3output_y__,
  input s0input__vld__,
  input [31:0] s0input_a__,
  input [31:0] s0input_b__
);

reg [63:0] __vul_pipeline_q_s1reg;
wire [63:0] resetvalue_s1reg__;
wire wen_s1reg__;
wire [63:0] wdata_s1reg__;
reg [0:0] __vul_pipeline_q_s1valid = 1'b0;
wire [0:0] resetvalue_s1valid__;
wire wen_s1valid__[2];
wire [0:0] wdata_s1valid__[2];
reg [63:0] __vul_pipeline_q_s3reg;
wire [63:0] __vul_pipeline_d_s3reg;
reg [0:0] __vul_pipeline_q_s3valid = 1'b0;
wire [0:0] __vul_pipeline_d_s3valid;

always @(posedge clk) begin
  if (rstn == 0) begin
    __vul_pipeline_q_s1reg <= resetvalue_s1reg__;
  end else begin
begin
    if (wen_s1reg__) begin
      __vul_pipeline_q_s1reg <= wdata_s1reg__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    __vul_pipeline_q_s1valid <= resetvalue_s1valid__;
  end else begin
begin
    if (wen_s1valid__[0]) begin
      __vul_pipeline_q_s1valid <= wdata_s1valid__[0];
    end
    else if (wen_s1valid__[1]) begin
      __vul_pipeline_q_s1valid <= wdata_s1valid__[1];
    end
    end
  end
end
always @(posedge clk) begin
  if (!rstn) begin
    __vul_pipeline_q_s3reg <= 64'h0;
  end else begin
  __vul_pipeline_q_s3reg <= __vul_pipeline_d_s3reg;
  end
end
always @(posedge clk) begin
  if (!rstn) begin
    __vul_pipeline_q_s3valid <= 1'h0;
  end else begin
  __vul_pipeline_q_s3valid <= __vul_pipeline_d_s3valid;
  end
end

if (1) begin : __vul_pipeline_multiply
    logic [63:0] __vul_port_s1reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    logic __vul_port_s1valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24
    logic [63:0] __vul_port_s3reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:18:1-18:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:36:1-36:58
    logic __vul_port_s3valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24
    logic __vul_pipeline_rstn; // decl: <none>; prim: <none>
    logic __vul_pipeline_clk; // decl: <none>; prim: <none>

    logic [63:0] vul_port_s1reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    logic vul_port_s1valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24
    logic [63:0] s6_helper___vul_compute_0_a__v0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:22:5-22:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:29:1-29:143
    logic [127:0] s8_norm_mul_6_v0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28
    logic [63:0] s6_helper___vul_compute_0_product__v0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:5-24:29; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28
    logic [63:0] vul_port_s3reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:18:1-18:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:36:1-36:58
    logic vul_port_s3valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24
    logic [31:0] __beopt_width_36; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_13; // decl: <none>; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    logic [63:0] __beopt_width_11; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_2_s1; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:22:5-22:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:29:1-29:143
    logic [63:0] rtlzz_pipe_8_s1; // decl: <none>; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24

    assign __vul_port_s1reg = __vul_pipeline_q_s1reg;
    assign __vul_port_s1valid = __vul_pipeline_q_s1valid;
    assign __vul_pipeline_d_s3reg = __vul_port_s3reg;
    assign __vul_pipeline_d_s3valid = __vul_port_s3valid;
    assign __vul_pipeline_rstn = rstn;
    assign __vul_pipeline_clk = clk;

    assign vul_port_s1reg = __vul_port_s1reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    assign vul_port_s1valid = __vul_port_s1valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24
    assign __vul_port_s3reg = vul_port_s3reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:18:1-18:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:36:1-36:58
    assign __vul_port_s3valid = vul_port_s3valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24

    assign s6_helper___vul_compute_0_a__v0 = (vul_port_s1reg & 64'hffffffff); // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:22:5-22:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:29:1-29:143
    assign s8_norm_mul_6_v0 = 128'(($unsigned(128'($unsigned(rtlzz_pipe_2_s1))) * $unsigned(128'($unsigned(rtlzz_pipe_8_s1))))); // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28
    assign s6_helper___vul_compute_0_product__v0 = s8_norm_mul_6_v0[63:0]; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:5-24:29; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28
    assign vul_port_s3reg = s6_helper___vul_compute_0_product__v0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:18:1-18:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:36:1-36:58
    assign vul_port_s3valid = rtlzz_valid_s1; // decl: <none>; prim: <none>
    assign __beopt_width_36 = vul_port_s1reg[63:32]; // decl: <none>; prim: <none>
    assign __beopt_width_13 = (__beopt_width_11 & 64'hffffffff); // decl: <none>; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    assign __beopt_width_11 = ({32'h0, __beopt_width_36}); // decl: <none>; prim: <none>
    always_ff @(posedge __vul_pipeline_clk) begin
        if (!__vul_pipeline_rstn) begin
            rtlzz_pipe_2_s1 <= 64'h0;
            rtlzz_pipe_8_s1 <= 64'h0;
            rtlzz_valid_s1 <= 1'h0;
        end else begin
        if (vul_port_s1valid) begin
        rtlzz_pipe_2_s1 <= s6_helper___vul_compute_0_a__v0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:22:5-22:25; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:29:1-29:143
        end
        if (vul_port_s1valid) begin
        rtlzz_pipe_8_s1 <= __beopt_width_13; // decl: <none>; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
        end
        rtlzz_valid_s1 <= vul_port_s1valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24
        end
    end
end

    logic [63:0] rdata_s3reg__; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:47:1-47:22; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:47:1-47:22
    logic rdata_s3valid__; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:49:1-49:23; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:49:1-49:23

    logic s0input__vld; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:29:1-29:20; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:29:1-29:20
    logic [31:0] s0input_a; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:31:1-31:20; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:31:1-31:20
    logic [31:0] s0input_b; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:33:1-33:20; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:33:1-33:20
    logic [63:0] rdata_s3reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:47:1-47:22; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:47:1-47:22
    logic rdata_s3valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:49:1-49:23; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:49:1-49:23
    logic [63:0] s8_norm_hw_20_v0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:77:3-77:18; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:77:3-77:18
    logic [63:0] s3output_y___v3; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:27:1-27:21; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:85:3-85:15
    logic s10_guard_not_3_v147; // decl: <none>; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:118:9-118:33
    logic s3output__vld; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:25:1-25:21; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:25:1-25:21
    logic [63:0] s3output_y; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:27:1-27:21; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:27:1-27:21
    logic wen_s1reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:35:1-35:17; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:35:1-35:17
    logic [63:0] wdata_s1reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:37:1-37:22; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:37:1-37:22
    logic [63:0] resetvalue_s1reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:39:1-39:27; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:102:3-102:48
    logic wen_s1valid___0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:41:1-41:34; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:41:1-41:34
    logic wen_s1valid___1; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:41:1-41:34; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:70:3-70:26
    logic wdata_s1valid___0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:43:1-43:38; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:43:1-43:38
    logic wdata_s1valid___1; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:43:1-43:38; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:68:3-68:45
    logic resetvalue_s1valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:45:1-45:28; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:108:3-108:47

    assign rdata_s3reg__ = __vul_pipeline_q_s3reg;
    assign rdata_s3valid__ = __vul_pipeline_q_s3valid;

    assign s3output__vld__ = s3output__vld; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:25:1-25:21; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:25:1-25:21
    assign s3output_y__ = s3output_y; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:27:1-27:21; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:27:1-27:21
    assign s0input__vld = s0input__vld__; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:29:1-29:20; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:29:1-29:20
    assign s0input_a = s0input_a__; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:31:1-31:20; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:31:1-31:20
    assign s0input_b = s0input_b__; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:33:1-33:20; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:33:1-33:20
    assign wen_s1reg__ = wen_s1reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:35:1-35:17; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:35:1-35:17
    assign wdata_s1reg__ = wdata_s1reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:37:1-37:22; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:37:1-37:22
    assign resetvalue_s1reg__ = resetvalue_s1reg; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:39:1-39:27; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:102:3-102:48
    assign wen_s1valid__[0] = wen_s1valid___0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:41:1-41:34; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:41:1-41:34
    assign wen_s1valid__[1] = wen_s1valid___1; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:41:1-41:34; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:70:3-70:26
    assign wdata_s1valid__[0] = wdata_s1valid___0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:43:1-43:38; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:43:1-43:38
    assign wdata_s1valid__[1] = wdata_s1valid___1; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:43:1-43:38; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:68:3-68:45
    assign resetvalue_s1valid__ = resetvalue_s1valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:45:1-45:28; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:108:3-108:47
    assign rdata_s3reg = rdata_s3reg__; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:47:1-47:22; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:47:1-47:22
    assign rdata_s3valid = rdata_s3valid__; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:49:1-49:23; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:49:1-49:23

    assign s8_norm_hw_20_v0 = {s0input_b, s0input_a}; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:77:3-77:18; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:77:3-77:18
    assign s3output_y___v3 = (s10_guard_not_3_v147 ? 64'h0 : rdata_s3reg); // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:27:1-27:21; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:85:3-85:15
    assign s10_guard_not_3_v147 = (!rdata_s3valid); // decl: <none>; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:118:9-118:33
    assign s3output__vld = rdata_s3valid; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:25:1-25:21; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:25:1-25:21
    assign s3output_y = s3output_y___v3; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:27:1-27:21; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:27:1-27:21
    assign wen_s1reg = s0input__vld; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:35:1-35:17; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:35:1-35:17
    assign wdata_s1reg = s8_norm_hw_20_v0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:37:1-37:22; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:37:1-37:22
    assign resetvalue_s1reg = 64'h0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:39:1-39:27; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:102:3-102:48
    assign wen_s1valid___0 = s0input__vld; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:41:1-41:34; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:41:1-41:34
    assign wen_s1valid___1 = 1'h1; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:41:1-41:34; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:70:3-70:26
    assign wdata_s1valid___0 = s0input__vld; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:43:1-43:38; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:43:1-43:38
    assign wdata_s1valid___1 = 1'h0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:43:1-43:38; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:68:3-68:45
    assign resetvalue_s1valid = 1'h0; // decl: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:45:1-45:28; prim: /home/zyrv/vulsim/build/step3-platforms-20261030/probes/mul-native/sim/top.logic.cpp:108:3-108:47
endmodule

