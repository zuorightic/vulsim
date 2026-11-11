`timescale 1ns/1ps

module Top_sim_top(
  input clk,
  input rstn,
  output [0:0] valid__query__,
  output [63:0] result__query__,
  input push__vld__,
  input [127:0] push_value__,
  input [0:0] push_v__
);

reg [31:0] __vul_pipeline_q_a;
wire [31:0] resetvalue_a__;
wire wen_a__;
wire [31:0] wdata_a__;
reg [31:0] __vul_pipeline_q_b;
wire [31:0] resetvalue_b__;
wire wen_b__;
wire [31:0] wdata_b__;
reg [63:0] __vul_pipeline_q_c;
wire [63:0] resetvalue_c__;
wire wen_c__;
wire [63:0] wdata_c__;
reg [0:0] __vul_pipeline_q_iv = 1'b0;
wire [0:0] resetvalue_iv__;
wire wen_iv__;
wire [0:0] wdata_iv__;
reg [63:0] __vul_pipeline_q_y;
wire [63:0] __vul_pipeline_d_y;
reg [0:0] __vul_pipeline_q_ov = 1'b0;
wire [0:0] __vul_pipeline_d_ov;

always @(posedge clk) begin
  if (rstn == 0) begin
    __vul_pipeline_q_a <= resetvalue_a__;
  end else begin
begin
    if (wen_a__) begin
      __vul_pipeline_q_a <= wdata_a__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    __vul_pipeline_q_b <= resetvalue_b__;
  end else begin
begin
    if (wen_b__) begin
      __vul_pipeline_q_b <= wdata_b__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    __vul_pipeline_q_c <= resetvalue_c__;
  end else begin
begin
    if (wen_c__) begin
      __vul_pipeline_q_c <= wdata_c__;
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
    __vul_pipeline_q_y <= 64'hc000003500000b2e;
  end else begin
  __vul_pipeline_q_y <= __vul_pipeline_d_y;
  end
end
always @(posedge clk) begin
  if (!rstn) begin
    __vul_pipeline_q_ov <= 1'h0;
  end else begin
  __vul_pipeline_q_ov <= __vul_pipeline_d_ov;
  end
end

if (1) begin : __vul_pipeline_core
    logic [31:0] __vul_port_a; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:19:1-19:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:19:1-19:21
    logic [31:0] __vul_port_b; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:21:1-21:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:21:1-21:21
    logic [63:0] __vul_port_c; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:23:1-23:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:23:1-23:21
    logic __vul_port_iv; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:25:1-25:19; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:25:1-25:19
    logic [63:0] __vul_port_y; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:27:1-27:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:47:1-47:50
    logic __vul_port_ov; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:29:1-29:19; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:29:1-29:19
    logic __vul_pipeline_rstn; // decl: <none>; prim: <none>
    logic __vul_pipeline_clk; // decl: <none>; prim: <none>

    logic [31:0] vul_port_a; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:19:1-19:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:19:1-19:21
    logic [31:0] vul_port_b; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:21:1-21:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:21:1-21:21
    logic [63:0] vul_port_c; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:23:1-23:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:23:1-23:21
    logic vul_port_iv; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:25:1-25:19; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:25:1-25:19
    logic [63:0] s8_norm_mul_5_v0; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:31:26-31:31; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:37:17-37:50
    logic [63:0] s8_norm_add_6_v0; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:32:22-32:53; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:32:22-32:53
    logic [63:0] vul_port_y; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:27:1-27:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:47:1-47:50
    logic vul_port_ov; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:29:1-29:19; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:29:1-29:19
    logic [31:0] __beopt_width_10; // decl: <none>; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:19:1-19:21
    logic [31:0] __beopt_width_11; // decl: <none>; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:21:1-21:21
    logic [63:0] __beopt_width_12; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_13; // decl: <none>; prim: <none>
    logic [63:0] arith_original_12; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:31:26-31:31; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:37:17-37:50
    logic [7:0] mul_tree_12_13; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_14; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_15; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_16; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_17; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_18; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_19; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_20; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_21; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_22; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_12_23; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_24; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_25; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_26; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_27; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_28; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_29; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_30; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_31; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_32; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_33; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_34; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_12_35; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_36; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_37; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_38; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_39; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_40; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_41; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_42; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_12_43; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_44; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_45; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_46; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_12_47; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_48; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_49; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_50; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_51; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_52; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_53; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_54; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_12_55; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_56; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_57; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_58; // decl: <none>; prim: <none>
    logic [55:0] mul_tree_12_59; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_60; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_61; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_62; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_63; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_64; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_65; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_66; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_12_67; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_68; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_69; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_70; // decl: <none>; prim: <none>
    logic [55:0] mul_tree_12_71; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_72; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_73; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_74; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_12_75; // decl: <none>; prim: <none>
    logic [24:0] mul_tree_12_76; // decl: <none>; prim: <none>
    logic [24:0] mul_tree_12_77; // decl: <none>; prim: <none>
    logic [24:0] mul_tree_12_78; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_79; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_80; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_81; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_82; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_83; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_84; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_85; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_86; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_87; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_88; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_89; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_90; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_91; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_92; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_93; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_94; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_95; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_96; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_12_97; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_12_98; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_12_99; // decl: <none>; prim: <none>
    logic [41:0] mul_tree_12_100; // decl: <none>; prim: <none>
    logic [41:0] mul_tree_12_101; // decl: <none>; prim: <none>
    logic [41:0] mul_tree_12_102; // decl: <none>; prim: <none>
    logic [49:0] mul_tree_12_103; // decl: <none>; prim: <none>
    logic [49:0] mul_tree_12_104; // decl: <none>; prim: <none>
    logic [49:0] mul_tree_12_105; // decl: <none>; prim: <none>
    logic [57:0] mul_tree_12_106; // decl: <none>; prim: <none>
    logic [57:0] mul_tree_12_107; // decl: <none>; prim: <none>
    logic [57:0] mul_tree_12_108; // decl: <none>; prim: <none>
    logic [65:0] mul_tree_12_109; // decl: <none>; prim: <none>
    logic [65:0] mul_tree_12_110; // decl: <none>; prim: <none>
    logic [65:0] mul_tree_12_111; // decl: <none>; prim: <none>
    logic [50:0] mul_tree_12_112; // decl: <none>; prim: <none>
    logic [50:0] mul_tree_12_113; // decl: <none>; prim: <none>
    logic [50:0] mul_tree_12_114; // decl: <none>; prim: <none>
    logic [66:0] mul_tree_12_115; // decl: <none>; prim: <none>
    logic [66:0] mul_tree_12_116; // decl: <none>; prim: <none>
    logic [66:0] mul_tree_12_117; // decl: <none>; prim: <none>
    logic [67:0] mul_tree_12_118; // decl: <none>; prim: <none>
    logic [67:0] mul_tree_12_119; // decl: <none>; prim: <none>
    logic [67:0] mul_tree_12_120; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_12_121; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_2_s1; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:23:1-23:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:23:1-23:21
    logic [24:0] rtlzz_pipe_78_s1; // decl: <none>; prim: <none>
    logic [40:0] rtlzz_pipe_81_s1; // decl: <none>; prim: <none>
    logic [32:0] rtlzz_pipe_84_s1; // decl: <none>; prim: <none>
    logic [48:0] rtlzz_pipe_87_s1; // decl: <none>; prim: <none>
    logic [40:0] rtlzz_pipe_90_s1; // decl: <none>; prim: <none>
    logic [56:0] rtlzz_pipe_93_s1; // decl: <none>; prim: <none>
    logic [48:0] rtlzz_pipe_96_s1; // decl: <none>; prim: <none>
    logic [64:0] rtlzz_pipe_99_s1; // decl: <none>; prim: <none>
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:25:1-25:19; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:25:1-25:19

    assign __vul_port_a = __vul_pipeline_q_a;
    assign __vul_port_b = __vul_pipeline_q_b;
    assign __vul_port_c = __vul_pipeline_q_c;
    assign __vul_port_iv = __vul_pipeline_q_iv;
    assign __vul_pipeline_d_y = __vul_port_y;
    assign __vul_pipeline_d_ov = __vul_port_ov;
    assign __vul_pipeline_rstn = rstn;
    assign __vul_pipeline_clk = clk;

    assign vul_port_a = __vul_port_a; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:19:1-19:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:19:1-19:21
    assign vul_port_b = __vul_port_b; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:21:1-21:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:21:1-21:21
    assign vul_port_c = __vul_port_c; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:23:1-23:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:23:1-23:21
    assign vul_port_iv = __vul_port_iv; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:25:1-25:19; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:25:1-25:19
    assign __vul_port_y = vul_port_y; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:27:1-27:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:47:1-47:50
    assign __vul_port_ov = vul_port_ov; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:29:1-29:19; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:29:1-29:19

    assign s8_norm_mul_5_v0 = arith_original_12; // decl: <none>; prim: <none>
    assign s8_norm_add_6_v0 = (s8_norm_mul_5_v0 + rtlzz_pipe_2_s1); // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:32:22-32:53; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:32:22-32:53
    assign vul_port_y = s8_norm_add_6_v0; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:27:1-27:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:47:1-47:50
    assign vul_port_ov = rtlzz_valid_s1; // decl: <none>; prim: <none>
    assign __beopt_width_10 = vul_port_a; // decl: <none>; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:19:1-19:21
    assign __beopt_width_11 = vul_port_b; // decl: <none>; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:21:1-21:21
    assign __beopt_width_12 = ({32'h0, __beopt_width_10}); // decl: <none>; prim: <none>
    assign __beopt_width_13 = ({32'h0, __beopt_width_11}); // decl: <none>; prim: <none>
    assign arith_original_12 = mul_tree_12_121; // decl: <none>; prim: <none>
    assign mul_tree_12_13 = __beopt_width_12[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_14 = __beopt_width_13[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_15 = 16'(($unsigned(16'($unsigned(mul_tree_12_13))) * $unsigned(16'($unsigned(mul_tree_12_14))))); // decl: <none>; prim: <none>
    assign mul_tree_12_16 = __beopt_width_12[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_17 = __beopt_width_13[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_18 = 16'(($unsigned(16'($unsigned(mul_tree_12_16))) * $unsigned(16'($unsigned(mul_tree_12_17))))); // decl: <none>; prim: <none>
    assign mul_tree_12_19 = {mul_tree_12_18, 8'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_20 = __beopt_width_12[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_21 = __beopt_width_13[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_22 = 16'(($unsigned(16'($unsigned(mul_tree_12_20))) * $unsigned(16'($unsigned(mul_tree_12_21))))); // decl: <none>; prim: <none>
    assign mul_tree_12_23 = {mul_tree_12_22, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_24 = __beopt_width_12[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_25 = __beopt_width_13[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_26 = 16'(($unsigned(16'($unsigned(mul_tree_12_24))) * $unsigned(16'($unsigned(mul_tree_12_25))))); // decl: <none>; prim: <none>
    assign mul_tree_12_27 = {mul_tree_12_26, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_28 = __beopt_width_12[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_29 = __beopt_width_13[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_30 = 16'(($unsigned(16'($unsigned(mul_tree_12_28))) * $unsigned(16'($unsigned(mul_tree_12_29))))); // decl: <none>; prim: <none>
    assign mul_tree_12_31 = {mul_tree_12_30, 8'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_32 = __beopt_width_12[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_33 = __beopt_width_13[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_34 = 16'(($unsigned(16'($unsigned(mul_tree_12_32))) * $unsigned(16'($unsigned(mul_tree_12_33))))); // decl: <none>; prim: <none>
    assign mul_tree_12_35 = {mul_tree_12_34, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_36 = __beopt_width_12[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_37 = __beopt_width_13[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_38 = 16'(($unsigned(16'($unsigned(mul_tree_12_36))) * $unsigned(16'($unsigned(mul_tree_12_37))))); // decl: <none>; prim: <none>
    assign mul_tree_12_39 = {mul_tree_12_38, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_40 = __beopt_width_12[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_41 = __beopt_width_13[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_42 = 16'(($unsigned(16'($unsigned(mul_tree_12_40))) * $unsigned(16'($unsigned(mul_tree_12_41))))); // decl: <none>; prim: <none>
    assign mul_tree_12_43 = {mul_tree_12_42, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_44 = __beopt_width_12[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_45 = __beopt_width_13[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_46 = 16'(($unsigned(16'($unsigned(mul_tree_12_44))) * $unsigned(16'($unsigned(mul_tree_12_45))))); // decl: <none>; prim: <none>
    assign mul_tree_12_47 = {mul_tree_12_46, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_48 = __beopt_width_12[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_49 = __beopt_width_13[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_50 = 16'(($unsigned(16'($unsigned(mul_tree_12_48))) * $unsigned(16'($unsigned(mul_tree_12_49))))); // decl: <none>; prim: <none>
    assign mul_tree_12_51 = {mul_tree_12_50, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_52 = __beopt_width_12[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_53 = __beopt_width_13[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_54 = 16'(($unsigned(16'($unsigned(mul_tree_12_52))) * $unsigned(16'($unsigned(mul_tree_12_53))))); // decl: <none>; prim: <none>
    assign mul_tree_12_55 = {mul_tree_12_54, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_56 = __beopt_width_12[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_57 = __beopt_width_13[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_58 = 16'(($unsigned(16'($unsigned(mul_tree_12_56))) * $unsigned(16'($unsigned(mul_tree_12_57))))); // decl: <none>; prim: <none>
    assign mul_tree_12_59 = {mul_tree_12_58, 40'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_60 = __beopt_width_12[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_61 = __beopt_width_13[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_62 = 16'(($unsigned(16'($unsigned(mul_tree_12_60))) * $unsigned(16'($unsigned(mul_tree_12_61))))); // decl: <none>; prim: <none>
    assign mul_tree_12_63 = {mul_tree_12_62, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_64 = __beopt_width_12[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_65 = __beopt_width_13[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_66 = 16'(($unsigned(16'($unsigned(mul_tree_12_64))) * $unsigned(16'($unsigned(mul_tree_12_65))))); // decl: <none>; prim: <none>
    assign mul_tree_12_67 = {mul_tree_12_66, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_68 = __beopt_width_12[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_69 = __beopt_width_13[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_70 = 16'(($unsigned(16'($unsigned(mul_tree_12_68))) * $unsigned(16'($unsigned(mul_tree_12_69))))); // decl: <none>; prim: <none>
    assign mul_tree_12_71 = {mul_tree_12_70, 40'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_72 = __beopt_width_12[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_73 = __beopt_width_13[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_74 = 16'(($unsigned(16'($unsigned(mul_tree_12_72))) * $unsigned(16'($unsigned(mul_tree_12_73))))); // decl: <none>; prim: <none>
    assign mul_tree_12_75 = {mul_tree_12_74, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_76 = ({9'h0, mul_tree_12_15}); // decl: <none>; prim: <none>
    assign mul_tree_12_77 = ({1'h0, mul_tree_12_19}); // decl: <none>; prim: <none>
    assign mul_tree_12_78 = 25'((mul_tree_12_76 + mul_tree_12_77 + ({24'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_79 = ({9'h0, mul_tree_12_23}); // decl: <none>; prim: <none>
    assign mul_tree_12_80 = ({1'h0, mul_tree_12_27}); // decl: <none>; prim: <none>
    assign mul_tree_12_81 = 41'((mul_tree_12_79 + mul_tree_12_80 + ({40'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_82 = ({9'h0, mul_tree_12_31}); // decl: <none>; prim: <none>
    assign mul_tree_12_83 = ({1'h0, mul_tree_12_35}); // decl: <none>; prim: <none>
    assign mul_tree_12_84 = 33'((mul_tree_12_82 + mul_tree_12_83 + ({32'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_85 = ({9'h0, mul_tree_12_39}); // decl: <none>; prim: <none>
    assign mul_tree_12_86 = ({1'h0, mul_tree_12_43}); // decl: <none>; prim: <none>
    assign mul_tree_12_87 = 49'((mul_tree_12_85 + mul_tree_12_86 + ({48'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_88 = ({9'h0, mul_tree_12_47}); // decl: <none>; prim: <none>
    assign mul_tree_12_89 = ({1'h0, mul_tree_12_51}); // decl: <none>; prim: <none>
    assign mul_tree_12_90 = 41'((mul_tree_12_88 + mul_tree_12_89 + ({40'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_91 = ({9'h0, mul_tree_12_55}); // decl: <none>; prim: <none>
    assign mul_tree_12_92 = ({1'h0, mul_tree_12_59}); // decl: <none>; prim: <none>
    assign mul_tree_12_93 = 57'((mul_tree_12_91 + mul_tree_12_92 + ({56'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_94 = ({9'h0, mul_tree_12_63}); // decl: <none>; prim: <none>
    assign mul_tree_12_95 = ({1'h0, mul_tree_12_67}); // decl: <none>; prim: <none>
    assign mul_tree_12_96 = 49'((mul_tree_12_94 + mul_tree_12_95 + ({48'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_97 = ({9'h0, mul_tree_12_71}); // decl: <none>; prim: <none>
    assign mul_tree_12_98 = ({1'h0, mul_tree_12_75}); // decl: <none>; prim: <none>
    assign mul_tree_12_99 = 65'((mul_tree_12_97 + mul_tree_12_98 + ({64'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_100 = ({17'h0, rtlzz_pipe_78_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_101 = ({1'h0, rtlzz_pipe_81_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_102 = 42'((mul_tree_12_100 + mul_tree_12_101 + ({41'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_103 = ({17'h0, rtlzz_pipe_84_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_104 = ({1'h0, rtlzz_pipe_87_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_105 = 50'((mul_tree_12_103 + mul_tree_12_104 + ({49'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_106 = ({17'h0, rtlzz_pipe_90_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_107 = ({1'h0, rtlzz_pipe_93_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_108 = 58'((mul_tree_12_106 + mul_tree_12_107 + ({57'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_109 = ({17'h0, rtlzz_pipe_96_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_110 = ({1'h0, rtlzz_pipe_99_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_111 = 66'((mul_tree_12_109 + mul_tree_12_110 + ({65'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_112 = ({9'h0, mul_tree_12_102}); // decl: <none>; prim: <none>
    assign mul_tree_12_113 = ({1'h0, mul_tree_12_105}); // decl: <none>; prim: <none>
    assign mul_tree_12_114 = 51'((mul_tree_12_112 + mul_tree_12_113 + ({50'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_115 = ({9'h0, mul_tree_12_108}); // decl: <none>; prim: <none>
    assign mul_tree_12_116 = ({1'h0, mul_tree_12_111}); // decl: <none>; prim: <none>
    assign mul_tree_12_117 = 67'((mul_tree_12_115 + mul_tree_12_116 + ({66'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_118 = ({17'h0, mul_tree_12_114}); // decl: <none>; prim: <none>
    assign mul_tree_12_119 = ({1'h0, mul_tree_12_117}); // decl: <none>; prim: <none>
    assign mul_tree_12_120 = 68'((mul_tree_12_118 + mul_tree_12_119 + ({67'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_12_121 = mul_tree_12_120[63:0]; // decl: <none>; prim: <none>
    always_ff @(posedge __vul_pipeline_clk) begin
        if (!__vul_pipeline_rstn) begin
            rtlzz_pipe_2_s1 <= 64'h8000000000000035;
            rtlzz_pipe_78_s1 <= 25'haf9;
            rtlzz_pipe_81_s1 <= 41'h1a80000000;
            rtlzz_pipe_84_s1 <= 33'h0;
            rtlzz_pipe_87_s1 <= 49'h0;
            rtlzz_pipe_90_s1 <= 41'h0;
            rtlzz_pipe_93_s1 <= 57'h0;
            rtlzz_pipe_96_s1 <= 49'h1a80000000;
            rtlzz_pipe_99_s1 <= 65'h4000000000000000;
            rtlzz_valid_s1 <= 1'h0;
        end else begin
        if (vul_port_iv) begin
        rtlzz_pipe_2_s1 <= vul_port_c; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:23:1-23:21; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:23:1-23:21
        end
        if (vul_port_iv) begin
        rtlzz_pipe_78_s1 <= mul_tree_12_78; // decl: <none>; prim: <none>
        end
        if (vul_port_iv) begin
        rtlzz_pipe_81_s1 <= mul_tree_12_81; // decl: <none>; prim: <none>
        end
        if (vul_port_iv) begin
        rtlzz_pipe_84_s1 <= mul_tree_12_84; // decl: <none>; prim: <none>
        end
        if (vul_port_iv) begin
        rtlzz_pipe_87_s1 <= mul_tree_12_87; // decl: <none>; prim: <none>
        end
        if (vul_port_iv) begin
        rtlzz_pipe_90_s1 <= mul_tree_12_90; // decl: <none>; prim: <none>
        end
        if (vul_port_iv) begin
        rtlzz_pipe_93_s1 <= mul_tree_12_93; // decl: <none>; prim: <none>
        end
        if (vul_port_iv) begin
        rtlzz_pipe_96_s1 <= mul_tree_12_96; // decl: <none>; prim: <none>
        end
        if (vul_port_iv) begin
        rtlzz_pipe_99_s1 <= mul_tree_12_99; // decl: <none>; prim: <none>
        end
        rtlzz_valid_s1 <= vul_port_iv; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:25:1-25:19; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp.pipeline_core.cpp:25:1-25:19
        end
    end
end

    logic [63:0] rdata_y__; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:64:1-64:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:64:1-64:18
    logic rdata_ov__; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:66:1-66:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:66:1-66:18

    logic push__vld; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:34:1-34:17; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:34:1-34:17
    logic [127:0] push_value; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:36:1-36:22; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:36:1-36:22
    logic push_v; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:38:1-38:16; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:38:1-38:16
    logic [63:0] rdata_y; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:64:1-64:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:64:1-64:18
    logic rdata_ov; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:66:1-66:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:66:1-66:18
    logic [31:0] s8_norm_hw_26_v0; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:176:21-176:33; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:176:21-176:33
    logic [31:0] s8_norm_hw_27_v0; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:177:21-177:33; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:177:21-177:33
    logic [63:0] s8_norm_hw_28_v0; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:178:21-178:33; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:178:21-178:33
    logic wdata_iv___v3; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:60:1-60:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:84:3-84:30
    logic valid__query; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:30:1-30:22; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:166:3-166:26
    logic [63:0] result__query; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:32:1-32:24; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:172:3-172:27
    logic wen_a; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:40:1-40:13; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:40:1-40:13
    logic [31:0] wdata_a; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:42:1-42:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:42:1-42:18
    logic [31:0] resetvalue_a; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:44:1-44:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:128:3-128:37
    logic wen_b; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:46:1-46:13; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:46:1-46:13
    logic [31:0] wdata_b; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:48:1-48:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:48:1-48:18
    logic [31:0] resetvalue_b; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:50:1-50:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:135:3-135:37
    logic wen_c; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:52:1-52:13; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:52:1-52:13
    logic [63:0] wdata_c; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:54:1-54:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:54:1-54:18
    logic [63:0] resetvalue_c; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:56:1-56:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:142:3-142:37
    logic wen_iv; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:58:1-58:14; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:58:1-58:14
    logic wdata_iv; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:60:1-60:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:60:1-60:18
    logic resetvalue_iv; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:62:1-62:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:148:3-148:37

    assign rdata_y__ = __vul_pipeline_q_y;
    assign rdata_ov__ = __vul_pipeline_q_ov;

    assign valid__query__ = valid__query; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:30:1-30:22; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:166:3-166:26
    assign result__query__ = result__query; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:32:1-32:24; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:172:3-172:27
    assign push__vld = push__vld__; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:34:1-34:17; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:34:1-34:17
    assign push_value = push_value__; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:36:1-36:22; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:36:1-36:22
    assign push_v = push_v__; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:38:1-38:16; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:38:1-38:16
    assign wen_a__ = wen_a; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:40:1-40:13; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:40:1-40:13
    assign wdata_a__ = wdata_a; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:42:1-42:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:42:1-42:18
    assign resetvalue_a__ = resetvalue_a; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:44:1-44:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:128:3-128:37
    assign wen_b__ = wen_b; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:46:1-46:13; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:46:1-46:13
    assign wdata_b__ = wdata_b; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:48:1-48:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:48:1-48:18
    assign resetvalue_b__ = resetvalue_b; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:50:1-50:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:135:3-135:37
    assign wen_c__ = wen_c; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:52:1-52:13; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:52:1-52:13
    assign wdata_c__ = wdata_c; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:54:1-54:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:54:1-54:18
    assign resetvalue_c__ = resetvalue_c; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:56:1-56:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:142:3-142:37
    assign wen_iv__ = wen_iv; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:58:1-58:14; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:58:1-58:14
    assign wdata_iv__ = wdata_iv; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:60:1-60:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:60:1-60:18
    assign resetvalue_iv__ = resetvalue_iv; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:62:1-62:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:148:3-148:37
    assign rdata_y = rdata_y__; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:64:1-64:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:64:1-64:18
    assign rdata_ov = rdata_ov__; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:66:1-66:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:66:1-66:18

    assign s8_norm_hw_26_v0 = push_value[31:0]; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:176:21-176:33; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:176:21-176:33
    assign s8_norm_hw_27_v0 = push_value[63:32]; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:177:21-177:33; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:177:21-177:33
    assign s8_norm_hw_28_v0 = push_value[127:64]; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:178:21-178:33; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:178:21-178:33
    assign wdata_iv___v3 = (push__vld & push_v); // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:60:1-60:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:84:3-84:30
    assign valid__query = rdata_ov; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:30:1-30:22; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:166:3-166:26
    assign result__query = rdata_y; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:32:1-32:24; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:172:3-172:27
    assign wen_a = push__vld; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:40:1-40:13; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:40:1-40:13
    assign wdata_a = s8_norm_hw_26_v0; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:42:1-42:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:42:1-42:18
    assign resetvalue_a = 32'h80000035; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:44:1-44:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:128:3-128:37
    assign wen_b = push__vld; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:46:1-46:13; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:46:1-46:13
    assign wdata_b = s8_norm_hw_27_v0; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:48:1-48:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:48:1-48:18
    assign resetvalue_b = 32'h80000035; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:50:1-50:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:135:3-135:37
    assign wen_c = push__vld; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:52:1-52:13; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:52:1-52:13
    assign wdata_c = s8_norm_hw_28_v0; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:54:1-54:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:54:1-54:18
    assign resetvalue_c = 64'h8000000000000035; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:56:1-56:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:142:3-142:37
    assign wen_iv = push__vld; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:58:1-58:14; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:58:1-58:14
    assign wdata_iv = wdata_iv___v3; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:60:1-60:18; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:60:1-60:18
    assign resetvalue_iv = 1'h0; // decl: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:62:1-62:23; prim: /home/zyrv/vulsim/build/step6-integration-20261031/public-final/MAC_32/sim/top.logic.cpp:148:3-148:37
endmodule

