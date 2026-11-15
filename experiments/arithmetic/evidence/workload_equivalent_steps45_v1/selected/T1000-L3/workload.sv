`timescale 1ns/1ps

module WorkloadCore(
    input logic [31:0] a, // decl: /home/zyrv/vulsim/workload.cpp:3:1-3:10; prim: /home/zyrv/vulsim/workload.cpp:3:1-3:10
    input logic [31:0] b, // decl: /home/zyrv/vulsim/workload.cpp:5:1-5:10; prim: /home/zyrv/vulsim/workload.cpp:5:1-5:10
    input logic [63:0] c, // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
    input logic iv, // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8
    output logic [63:0] y, // decl: /home/zyrv/vulsim/workload.cpp:11:1-11:10; prim: /home/zyrv/vulsim/workload.cpp:15:5-15:47
    output logic ov, // decl: /home/zyrv/vulsim/workload.cpp:13:1-13:8; prim: /home/zyrv/vulsim/workload.cpp:13:1-13:8
    input logic rstn, // decl: <none>; prim: <none>
    input logic clk // decl: <none>; prim: <none>
);

    logic [63:0] s8_norm_mul_2_v0; // decl: <none>; prim: /home/zyrv/vulsim/workload.cpp:3:1-3:10
    logic [63:0] s8_norm_add_4_v0; // decl: <none>; prim: /home/zyrv/vulsim/workload.cpp:15:23-15:33
    logic [63:0] __beopt_width_10; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_11; // decl: <none>; prim: <none>
    logic [31:0] mul_precision_10; // decl: <none>; prim: <none>
    logic [31:0] mul_precision_11; // decl: <none>; prim: <none>
    logic [63:0] arith_original_12; // decl: <none>; prim: /home/zyrv/vulsim/workload.cpp:3:1-3:10
    logic [11:0] mul_tree_12_13; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_14; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_15; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_16; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_17; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_18; // decl: <none>; prim: <none>
    logic [35:0] mul_tree_12_19; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_20; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_21; // decl: <none>; prim: <none>
    logic [19:0] mul_tree_12_22; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_23; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_24; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_25; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_26; // decl: <none>; prim: <none>
    logic [35:0] mul_tree_12_27; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_28; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_29; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_30; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_12_31; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_32; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_33; // decl: <none>; prim: <none>
    logic [19:0] mul_tree_12_34; // decl: <none>; prim: <none>
    logic [55:0] mul_tree_12_35; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_36; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_37; // decl: <none>; prim: <none>
    logic [19:0] mul_tree_12_38; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_39; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_40; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_41; // decl: <none>; prim: <none>
    logic [19:0] mul_tree_12_42; // decl: <none>; prim: <none>
    logic [55:0] mul_tree_12_43; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_44; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_45; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_46; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_12_47; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_48; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_49; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_50; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_51; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_52; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_53; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_54; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_55; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_56; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_57; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_58; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_59; // decl: <none>; prim: <none>
    logic [45:0] mul_tree_12_60; // decl: <none>; prim: <none>
    logic [45:0] mul_tree_12_61; // decl: <none>; prim: <none>
    logic [45:0] mul_tree_12_62; // decl: <none>; prim: <none>
    logic [57:0] mul_tree_12_63; // decl: <none>; prim: <none>
    logic [57:0] mul_tree_12_64; // decl: <none>; prim: <none>
    logic [57:0] mul_tree_12_65; // decl: <none>; prim: <none>
    logic [58:0] mul_tree_12_66; // decl: <none>; prim: <none>
    logic [58:0] mul_tree_12_67; // decl: <none>; prim: <none>
    logic [58:0] mul_tree_12_68; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_12_69; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_12_70; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_12_71; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_12_72; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_2_s1; // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
    logic [63:0] rtlzz_pipe_2_s2; // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
    logic [23:0] rtlzz_pipe_15_s1; // decl: <none>; prim: <none>
    logic [35:0] rtlzz_pipe_19_s1; // decl: <none>; prim: <none>
    logic [43:0] rtlzz_pipe_23_s1; // decl: <none>; prim: <none>
    logic [35:0] rtlzz_pipe_27_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_31_s1; // decl: <none>; prim: <none>
    logic [55:0] rtlzz_pipe_35_s1; // decl: <none>; prim: <none>
    logic [43:0] rtlzz_pipe_39_s1; // decl: <none>; prim: <none>
    logic [55:0] rtlzz_pipe_43_s1; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_47_s1; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_4_s2; // decl: <none>; prim: /home/zyrv/vulsim/workload.cpp:3:1-3:10
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8
    logic rtlzz_valid_s2; // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8


    assign s8_norm_mul_2_v0 = arith_original_12; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_5Core rtlzz_owner_5(.a(64'(rtlzz_pipe_4_s2)), .b(64'(rtlzz_pipe_2_s2)), .cin(1'b0), .value(s8_norm_add_4_v0));
    assign y = s8_norm_add_4_v0; // decl: /home/zyrv/vulsim/workload.cpp:11:1-11:10; prim: /home/zyrv/vulsim/workload.cpp:15:5-15:47
    assign ov = rtlzz_valid_s2; // decl: <none>; prim: <none>
    assign __beopt_width_10 = ({32'h0, a}); // decl: <none>; prim: <none>
    assign __beopt_width_11 = ({32'h0, b}); // decl: <none>; prim: <none>
    assign mul_precision_10 = __beopt_width_10[31:0]; // decl: <none>; prim: <none>
    assign mul_precision_11 = __beopt_width_11[31:0]; // decl: <none>; prim: <none>
    assign arith_original_12 = mul_tree_12_72; // decl: <none>; prim: <none>
    assign mul_tree_12_13 = mul_precision_10[11:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_14 = mul_precision_11[11:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_15Core rtlzz_owner_15(.a(12'(mul_tree_12_13)), .b(12'(mul_tree_12_14)), .cin(1'b0), .value(mul_tree_12_15));
    assign mul_tree_12_16 = mul_precision_10[11:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_17 = mul_precision_11[23:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_18Core rtlzz_owner_18(.a(12'(mul_tree_12_16)), .b(12'(mul_tree_12_17)), .cin(1'b0), .value(mul_tree_12_18));
    assign mul_tree_12_19 = {mul_tree_12_18, 12'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_20 = mul_precision_10[11:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_21 = mul_precision_11[31:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_22Core rtlzz_owner_22(.a(12'(mul_tree_12_20)), .b(8'(mul_tree_12_21)), .cin(1'b0), .value(mul_tree_12_22));
    assign mul_tree_12_23 = {mul_tree_12_22, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_24 = mul_precision_10[23:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_25 = mul_precision_11[11:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_26Core rtlzz_owner_26(.a(12'(mul_tree_12_24)), .b(12'(mul_tree_12_25)), .cin(1'b0), .value(mul_tree_12_26));
    assign mul_tree_12_27 = {mul_tree_12_26, 12'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_28 = mul_precision_10[23:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_29 = mul_precision_11[23:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_30Core rtlzz_owner_30(.a(12'(mul_tree_12_28)), .b(12'(mul_tree_12_29)), .cin(1'b0), .value(mul_tree_12_30));
    assign mul_tree_12_31 = {mul_tree_12_30, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_32 = mul_precision_10[23:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_33 = mul_precision_11[31:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_34Core rtlzz_owner_34(.a(12'(mul_tree_12_32)), .b(8'(mul_tree_12_33)), .cin(1'b0), .value(mul_tree_12_34));
    assign mul_tree_12_35 = {mul_tree_12_34, 36'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_36 = mul_precision_10[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_37 = mul_precision_11[11:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_38Core rtlzz_owner_38(.a(8'(mul_tree_12_36)), .b(12'(mul_tree_12_37)), .cin(1'b0), .value(mul_tree_12_38));
    assign mul_tree_12_39 = {mul_tree_12_38, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_40 = mul_precision_10[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_41 = mul_precision_11[23:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_42Core rtlzz_owner_42(.a(8'(mul_tree_12_40)), .b(12'(mul_tree_12_41)), .cin(1'b0), .value(mul_tree_12_42));
    assign mul_tree_12_43 = {mul_tree_12_42, 36'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_44 = mul_precision_10[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_45 = mul_precision_11[31:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_46Core rtlzz_owner_46(.a(8'(mul_tree_12_44)), .b(8'(mul_tree_12_45)), .cin(1'b0), .value(mul_tree_12_46));
    assign mul_tree_12_47 = {mul_tree_12_46, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_48 = ({13'h0, rtlzz_pipe_15_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_49 = ({1'h0, rtlzz_pipe_19_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_51 = ({1'h0, rtlzz_pipe_23_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_52 = ({9'h0, rtlzz_pipe_27_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_54 = ({9'h0, rtlzz_pipe_31_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_55 = ({1'h0, rtlzz_pipe_35_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_57 = ({13'h0, rtlzz_pipe_39_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_58 = ({1'h0, rtlzz_pipe_43_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_60 = ({9'h0, mul_tree_12_50}); // decl: <none>; prim: <none>
    assign mul_tree_12_61 = ({1'h0, mul_tree_12_53}); // decl: <none>; prim: <none>
    assign mul_tree_12_63 = ({1'h0, mul_tree_12_56}); // decl: <none>; prim: <none>
    assign mul_tree_12_64 = ({1'h0, mul_tree_12_59}); // decl: <none>; prim: <none>
    assign mul_tree_12_66 = ({13'h0, mul_tree_12_62}); // decl: <none>; prim: <none>
    assign mul_tree_12_67 = ({1'h0, mul_tree_12_65}); // decl: <none>; prim: <none>
    assign mul_tree_12_69 = ({6'h0, mul_tree_12_68}); // decl: <none>; prim: <none>
    assign mul_tree_12_70 = ({1'h0, rtlzz_pipe_47_s1}); // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_71_reduce rtlzz_reduce_71(.i75(rtlzz_pipe_15_s1), .i76(rtlzz_pipe_19_s1), .i77(rtlzz_pipe_23_s1), .i78(rtlzz_pipe_27_s1), .i79(rtlzz_pipe_31_s1), .i80(rtlzz_pipe_35_s1), .i81(rtlzz_pipe_39_s1), .i82(rtlzz_pipe_43_s1), .i83(rtlzz_pipe_47_s1), .y(mul_tree_12_71));
    assign mul_tree_12_72 = mul_tree_12_71[63:0]; // decl: <none>; prim: <none>
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_2_s1 <= 64'h0;
            rtlzz_pipe_2_s2 <= 64'h0;
            rtlzz_pipe_15_s1 <= 24'h0;
            rtlzz_pipe_19_s1 <= 36'h0;
            rtlzz_pipe_23_s1 <= 44'h0;
            rtlzz_pipe_27_s1 <= 36'h0;
            rtlzz_pipe_31_s1 <= 48'h0;
            rtlzz_pipe_35_s1 <= 56'h0;
            rtlzz_pipe_39_s1 <= 44'h0;
            rtlzz_pipe_43_s1 <= 56'h0;
            rtlzz_pipe_47_s1 <= 64'h0;
            rtlzz_pipe_4_s2 <= 64'h0;
            rtlzz_valid_s1 <= 1'h0;
            rtlzz_valid_s2 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_2_s1 <= c; // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_2_s2 <= rtlzz_pipe_2_s1; // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
        end
        if (iv) begin
        rtlzz_pipe_15_s1 <= mul_tree_12_15; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_19_s1 <= mul_tree_12_19; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_23_s1 <= mul_tree_12_23; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_27_s1 <= mul_tree_12_27; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_31_s1 <= mul_tree_12_31; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_35_s1 <= mul_tree_12_35; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_39_s1 <= mul_tree_12_39; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_43_s1 <= mul_tree_12_43; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_47_s1 <= mul_tree_12_47; // decl: <none>; prim: <none>
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_4_s2 <= s8_norm_mul_2_v0; // decl: <none>; prim: /home/zyrv/vulsim/workload.cpp:3:1-3:10
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8
        rtlzz_valid_s2 <= rtlzz_valid_s1; // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8
        end
    end
endmodule

(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_71_reduce(input wire [23:0] i75, input wire [35:0] i76, input wire [43:0] i77, input wire [35:0] i78, input wire [47:0] i79, input wire [55:0] i80, input wire [43:0] i81, input wire [55:0] i82, input wire [63:0] i83, output wire [64:0] y);
wire [63:0] t0 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i75[23], i75[22], i75[21], i75[20], i75[19], i75[18], i75[17], i75[16], i75[15], i75[14], i75[13], i75[12], i75[11], i75[10], i75[9], i75[8], i75[7], i75[6], i75[5], i75[4], i75[3], i75[2], i75[1], i75[0]};
wire [63:0] t1 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i76[35], i76[34], i76[33], i76[32], i76[31], i76[30], i76[29], i76[28], i76[27], i76[26], i76[25], i76[24], i76[23], i76[22], i76[21], i76[20], i76[19], i76[18], i76[17], i76[16], i76[15], i76[14], i76[13], i76[12], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t2 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i77[43], i77[42], i77[41], i77[40], i77[39], i77[38], i77[37], i77[36], i77[35], i77[34], i77[33], i77[32], i77[31], i77[30], i77[29], i77[28], i77[27], i77[26], i77[25], i77[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t3 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i78[35], i78[34], i78[33], i78[32], i78[31], i78[30], i78[29], i78[28], i78[27], i78[26], i78[25], i78[24], i78[23], i78[22], i78[21], i78[20], i78[19], i78[18], i78[17], i78[16], i78[15], i78[14], i78[13], i78[12], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t4 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i79[47], i79[46], i79[45], i79[44], i79[43], i79[42], i79[41], i79[40], i79[39], i79[38], i79[37], i79[36], i79[35], i79[34], i79[33], i79[32], i79[31], i79[30], i79[29], i79[28], i79[27], i79[26], i79[25], i79[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t5 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i80[55], i80[54], i80[53], i80[52], i80[51], i80[50], i80[49], i80[48], i80[47], i80[46], i80[45], i80[44], i80[43], i80[42], i80[41], i80[40], i80[39], i80[38], i80[37], i80[36], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t6 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i81[43], i81[42], i81[41], i81[40], i81[39], i81[38], i81[37], i81[36], i81[35], i81[34], i81[33], i81[32], i81[31], i81[30], i81[29], i81[28], i81[27], i81[26], i81[25], i81[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t7 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i82[55], i82[54], i82[53], i82[52], i82[51], i82[50], i82[49], i82[48], i82[47], i82[46], i82[45], i82[44], i82[43], i82[42], i82[41], i82[40], i82[39], i82[38], i82[37], i82[36], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t8 = {i83[63], i83[62], i83[61], i83[60], i83[59], i83[58], i83[57], i83[56], i83[55], i83[54], i83[53], i83[52], i83[51], i83[50], i83[49], i83[48], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] sum = t0 + t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8;
assign y=sum;
endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_5Core(input wire [63:0] a,input wire [63:0] b,input wire cin,output wire [63:0] value);
wire [63:0] masked_a=((a&64'hffffffffffffffff)|64'h0);
wire [63:0] masked_b=((b&64'hffffffffffffffff)|64'h0);
wire [63:0] aa=64'(masked_a);
wire [63:0] bb=64'(masked_b);
wire [64:0] extended={1'b0,aa}+{1'b0,bb}+65'(1'b0);
wire [63:0] native_value=extended[63:0];
assign value=native_value[0+:64];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_5();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_15Core(input wire [11:0] a,input wire [11:0] b,input wire cin,output wire [23:0] value);
wire [11:0] masked_a=((a&12'hfff)|12'h0);
wire [11:0] masked_b=((b&12'hfff)|12'h0);
wire [23:0] aa=24'(masked_a);
wire [23:0] bb=24'(masked_b);
wire [23:0] native_value=aa*bb;
assign value=native_value[0+:24];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_15();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_18Core(input wire [11:0] a,input wire [11:0] b,input wire cin,output wire [23:0] value);
wire [11:0] masked_a=((a&12'hfff)|12'h0);
wire [11:0] masked_b=((b&12'hfff)|12'h0);
wire [23:0] aa=24'(masked_a);
wire [23:0] bb=24'(masked_b);
wire [23:0] native_value=aa*bb;
assign value=native_value[0+:24];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_18();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_22Core(input wire [11:0] a,input wire [7:0] b,input wire cin,output wire [19:0] value);
wire [11:0] masked_a=((a&12'hfff)|12'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [19:0] aa=20'(masked_a);
wire [19:0] bb=20'(masked_b);
wire [19:0] native_value=aa*bb;
assign value=native_value[0+:20];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_22();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_26Core(input wire [11:0] a,input wire [11:0] b,input wire cin,output wire [23:0] value);
wire [11:0] masked_a=((a&12'hfff)|12'h0);
wire [11:0] masked_b=((b&12'hfff)|12'h0);
wire [23:0] aa=24'(masked_a);
wire [23:0] bb=24'(masked_b);
wire [23:0] native_value=aa*bb;
assign value=native_value[0+:24];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_26();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_30Core(input wire [11:0] a,input wire [11:0] b,input wire cin,output wire [23:0] value);
wire [11:0] masked_a=((a&12'hfff)|12'h0);
wire [11:0] masked_b=((b&12'hfff)|12'h0);
wire [23:0] aa=24'(masked_a);
wire [23:0] bb=24'(masked_b);
wire [23:0] native_value=aa*bb;
assign value=native_value[0+:24];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_30();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_34Core(input wire [11:0] a,input wire [7:0] b,input wire cin,output wire [19:0] value);
wire [11:0] masked_a=((a&12'hfff)|12'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [19:0] aa=20'(masked_a);
wire [19:0] bb=20'(masked_b);
wire [19:0] native_value=aa*bb;
assign value=native_value[0+:20];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_34();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_38Core(input wire [7:0] a,input wire [11:0] b,input wire cin,output wire [19:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [11:0] masked_b=((b&12'hfff)|12'h0);
wire [19:0] aa=20'(masked_a);
wire [19:0] bb=20'(masked_b);
wire [19:0] native_value=aa*bb;
assign value=native_value[0+:20];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_38();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_42Core(input wire [7:0] a,input wire [11:0] b,input wire cin,output wire [19:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [11:0] masked_b=((b&12'hfff)|12'h0);
wire [19:0] aa=20'(masked_a);
wire [19:0] bb=20'(masked_b);
wire [19:0] native_value=aa*bb;
assign value=native_value[0+:20];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_42();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_46Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_46();endmodule

module Workload(input wire clk,input wire rstn,input wire iv_data,input wire iv_wen,output reg ov,input wire [31:0] a_data,input wire a_wen,input wire [31:0] b_data,input wire b_wen,input wire [63:0] c_data,input wire c_wen,output reg [63:0] y);
reg liv;wire cov;
reg [31:0] l_a;
reg [31:0] l_b;
reg [63:0] l_c;
wire [63:0] c_y;
WorkloadCore core(.iv(liv),.ov(cov),.clk(clk),.rstn(rstn),.a(l_a),.b(l_b),.c(l_c),.y(c_y));
always @(posedge clk)if(!rstn)begin liv<=1'b0;ov<=1'b0;l_a<=32'h0;l_b<=32'h0;l_c<=64'h0;y<=64'h0;end else begin if(iv_wen)liv<=iv_data;ov<=cov;if(a_wen)l_a<=a_data;if(b_wen)l_b<=b_data;if(c_wen)l_c<=c_data;y<=c_y;end
endmodule
