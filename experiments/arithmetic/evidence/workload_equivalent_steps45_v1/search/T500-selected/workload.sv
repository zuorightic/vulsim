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
    logic [63:0] rtlzz_pipe_2_s1; // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
    logic [63:0] rtlzz_pipe_2_s2; // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
    logic [15:0] rtlzz_pipe_15_s1; // decl: <none>; prim: <none>
    logic [23:0] rtlzz_pipe_19_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_23_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_27_s1; // decl: <none>; prim: <none>
    logic [23:0] rtlzz_pipe_31_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_35_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_39_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_43_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_47_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_51_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_55_s1; // decl: <none>; prim: <none>
    logic [55:0] rtlzz_pipe_59_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_63_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_67_s1; // decl: <none>; prim: <none>
    logic [55:0] rtlzz_pipe_71_s1; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_75_s1; // decl: <none>; prim: <none>
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
    assign arith_original_12 = mul_tree_12_121; // decl: <none>; prim: <none>
    assign mul_tree_12_13 = mul_precision_10[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_14 = mul_precision_11[7:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_15Core rtlzz_owner_15(.a(8'(mul_tree_12_13)), .b(8'(mul_tree_12_14)), .cin(1'b0), .value(mul_tree_12_15));
    assign mul_tree_12_16 = mul_precision_10[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_17 = mul_precision_11[15:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_18Core rtlzz_owner_18(.a(8'(mul_tree_12_16)), .b(8'(mul_tree_12_17)), .cin(1'b0), .value(mul_tree_12_18));
    assign mul_tree_12_19 = {mul_tree_12_18, 8'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_20 = mul_precision_10[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_21 = mul_precision_11[23:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_22Core rtlzz_owner_22(.a(8'(mul_tree_12_20)), .b(8'(mul_tree_12_21)), .cin(1'b0), .value(mul_tree_12_22));
    assign mul_tree_12_23 = {mul_tree_12_22, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_24 = mul_precision_10[7:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_25 = mul_precision_11[31:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_26Core rtlzz_owner_26(.a(8'(mul_tree_12_24)), .b(8'(mul_tree_12_25)), .cin(1'b0), .value(mul_tree_12_26));
    assign mul_tree_12_27 = {mul_tree_12_26, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_28 = mul_precision_10[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_29 = mul_precision_11[7:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_30Core rtlzz_owner_30(.a(8'(mul_tree_12_28)), .b(8'(mul_tree_12_29)), .cin(1'b0), .value(mul_tree_12_30));
    assign mul_tree_12_31 = {mul_tree_12_30, 8'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_32 = mul_precision_10[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_33 = mul_precision_11[15:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_34Core rtlzz_owner_34(.a(8'(mul_tree_12_32)), .b(8'(mul_tree_12_33)), .cin(1'b0), .value(mul_tree_12_34));
    assign mul_tree_12_35 = {mul_tree_12_34, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_36 = mul_precision_10[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_37 = mul_precision_11[23:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_38Core rtlzz_owner_38(.a(8'(mul_tree_12_36)), .b(8'(mul_tree_12_37)), .cin(1'b0), .value(mul_tree_12_38));
    assign mul_tree_12_39 = {mul_tree_12_38, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_40 = mul_precision_10[15:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_41 = mul_precision_11[31:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_42Core rtlzz_owner_42(.a(8'(mul_tree_12_40)), .b(8'(mul_tree_12_41)), .cin(1'b0), .value(mul_tree_12_42));
    assign mul_tree_12_43 = {mul_tree_12_42, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_44 = mul_precision_10[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_45 = mul_precision_11[7:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_46Core rtlzz_owner_46(.a(8'(mul_tree_12_44)), .b(8'(mul_tree_12_45)), .cin(1'b0), .value(mul_tree_12_46));
    assign mul_tree_12_47 = {mul_tree_12_46, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_48 = mul_precision_10[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_49 = mul_precision_11[15:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_50Core rtlzz_owner_50(.a(8'(mul_tree_12_48)), .b(8'(mul_tree_12_49)), .cin(1'b0), .value(mul_tree_12_50));
    assign mul_tree_12_51 = {mul_tree_12_50, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_52 = mul_precision_10[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_53 = mul_precision_11[23:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_54Core rtlzz_owner_54(.a(8'(mul_tree_12_52)), .b(8'(mul_tree_12_53)), .cin(1'b0), .value(mul_tree_12_54));
    assign mul_tree_12_55 = {mul_tree_12_54, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_56 = mul_precision_10[23:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_57 = mul_precision_11[31:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_58Core rtlzz_owner_58(.a(8'(mul_tree_12_56)), .b(8'(mul_tree_12_57)), .cin(1'b0), .value(mul_tree_12_58));
    assign mul_tree_12_59 = {mul_tree_12_58, 40'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_60 = mul_precision_10[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_61 = mul_precision_11[7:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_62Core rtlzz_owner_62(.a(8'(mul_tree_12_60)), .b(8'(mul_tree_12_61)), .cin(1'b0), .value(mul_tree_12_62));
    assign mul_tree_12_63 = {mul_tree_12_62, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_64 = mul_precision_10[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_65 = mul_precision_11[15:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_66Core rtlzz_owner_66(.a(8'(mul_tree_12_64)), .b(8'(mul_tree_12_65)), .cin(1'b0), .value(mul_tree_12_66));
    assign mul_tree_12_67 = {mul_tree_12_66, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_68 = mul_precision_10[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_69 = mul_precision_11[23:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_70Core rtlzz_owner_70(.a(8'(mul_tree_12_68)), .b(8'(mul_tree_12_69)), .cin(1'b0), .value(mul_tree_12_70));
    assign mul_tree_12_71 = {mul_tree_12_70, 40'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_72 = mul_precision_10[31:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_73 = mul_precision_11[31:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_74Core rtlzz_owner_74(.a(8'(mul_tree_12_72)), .b(8'(mul_tree_12_73)), .cin(1'b0), .value(mul_tree_12_74));
    assign mul_tree_12_75 = {mul_tree_12_74, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_76 = ({9'h0, rtlzz_pipe_15_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_77 = ({1'h0, rtlzz_pipe_19_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_79 = ({9'h0, rtlzz_pipe_23_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_80 = ({1'h0, rtlzz_pipe_27_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_82 = ({9'h0, rtlzz_pipe_31_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_83 = ({1'h0, rtlzz_pipe_35_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_85 = ({9'h0, rtlzz_pipe_39_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_86 = ({1'h0, rtlzz_pipe_43_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_88 = ({9'h0, rtlzz_pipe_47_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_89 = ({1'h0, rtlzz_pipe_51_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_91 = ({9'h0, rtlzz_pipe_55_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_92 = ({1'h0, rtlzz_pipe_59_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_94 = ({9'h0, rtlzz_pipe_63_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_95 = ({1'h0, rtlzz_pipe_67_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_97 = ({9'h0, rtlzz_pipe_71_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_98 = ({1'h0, rtlzz_pipe_75_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_100 = ({17'h0, mul_tree_12_78}); // decl: <none>; prim: <none>
    assign mul_tree_12_101 = ({1'h0, mul_tree_12_81}); // decl: <none>; prim: <none>
    assign mul_tree_12_103 = ({17'h0, mul_tree_12_84}); // decl: <none>; prim: <none>
    assign mul_tree_12_104 = ({1'h0, mul_tree_12_87}); // decl: <none>; prim: <none>
    assign mul_tree_12_106 = ({17'h0, mul_tree_12_90}); // decl: <none>; prim: <none>
    assign mul_tree_12_107 = ({1'h0, mul_tree_12_93}); // decl: <none>; prim: <none>
    assign mul_tree_12_109 = ({17'h0, mul_tree_12_96}); // decl: <none>; prim: <none>
    assign mul_tree_12_110 = ({1'h0, mul_tree_12_99}); // decl: <none>; prim: <none>
    assign mul_tree_12_112 = ({9'h0, mul_tree_12_102}); // decl: <none>; prim: <none>
    assign mul_tree_12_113 = ({1'h0, mul_tree_12_105}); // decl: <none>; prim: <none>
    assign mul_tree_12_115 = ({9'h0, mul_tree_12_108}); // decl: <none>; prim: <none>
    assign mul_tree_12_116 = ({1'h0, mul_tree_12_111}); // decl: <none>; prim: <none>
    assign mul_tree_12_118 = ({17'h0, mul_tree_12_114}); // decl: <none>; prim: <none>
    assign mul_tree_12_119 = ({1'h0, mul_tree_12_117}); // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_120_reduce rtlzz_reduce_120(.i124(rtlzz_pipe_15_s1), .i125(rtlzz_pipe_19_s1), .i126(rtlzz_pipe_23_s1), .i127(rtlzz_pipe_27_s1), .i128(rtlzz_pipe_31_s1), .i129(rtlzz_pipe_35_s1), .i130(rtlzz_pipe_39_s1), .i131(rtlzz_pipe_43_s1), .i132(rtlzz_pipe_47_s1), .i133(rtlzz_pipe_51_s1), .i134(rtlzz_pipe_55_s1), .i135(rtlzz_pipe_59_s1), .i136(rtlzz_pipe_63_s1), .i137(rtlzz_pipe_67_s1), .i138(rtlzz_pipe_71_s1), .i139(rtlzz_pipe_75_s1), .y(mul_tree_12_120));
    assign mul_tree_12_121 = mul_tree_12_120[63:0]; // decl: <none>; prim: <none>
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_2_s1 <= 64'h0;
            rtlzz_pipe_2_s2 <= 64'h0;
            rtlzz_pipe_15_s1 <= 16'h0;
            rtlzz_pipe_19_s1 <= 24'h0;
            rtlzz_pipe_23_s1 <= 32'h0;
            rtlzz_pipe_27_s1 <= 40'h0;
            rtlzz_pipe_31_s1 <= 24'h0;
            rtlzz_pipe_35_s1 <= 32'h0;
            rtlzz_pipe_39_s1 <= 40'h0;
            rtlzz_pipe_43_s1 <= 48'h0;
            rtlzz_pipe_47_s1 <= 32'h0;
            rtlzz_pipe_51_s1 <= 40'h0;
            rtlzz_pipe_55_s1 <= 48'h0;
            rtlzz_pipe_59_s1 <= 56'h0;
            rtlzz_pipe_63_s1 <= 40'h0;
            rtlzz_pipe_67_s1 <= 48'h0;
            rtlzz_pipe_71_s1 <= 56'h0;
            rtlzz_pipe_75_s1 <= 64'h0;
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
        if (iv) begin
        rtlzz_pipe_51_s1 <= mul_tree_12_51; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_55_s1 <= mul_tree_12_55; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_59_s1 <= mul_tree_12_59; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_63_s1 <= mul_tree_12_63; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_67_s1 <= mul_tree_12_67; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_71_s1 <= mul_tree_12_71; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_75_s1 <= mul_tree_12_75; // decl: <none>; prim: <none>
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_4_s2 <= s8_norm_mul_2_v0; // decl: <none>; prim: /home/zyrv/vulsim/workload.cpp:3:1-3:10
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8
        rtlzz_valid_s2 <= rtlzz_valid_s1; // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8
        end
    end
endmodule

(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_120_reduce(input wire [15:0] i124, input wire [23:0] i125, input wire [31:0] i126, input wire [39:0] i127, input wire [23:0] i128, input wire [31:0] i129, input wire [39:0] i130, input wire [47:0] i131, input wire [31:0] i132, input wire [39:0] i133, input wire [47:0] i134, input wire [55:0] i135, input wire [39:0] i136, input wire [47:0] i137, input wire [55:0] i138, input wire [63:0] i139, output wire [67:0] y);
wire [63:0] t0 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i124[15], i124[14], i124[13], i124[12], i124[11], i124[10], i124[9], i124[8], i124[7], i124[6], i124[5], i124[4], i124[3], i124[2], i124[1], i124[0]};
wire [63:0] t1 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i125[23], i125[22], i125[21], i125[20], i125[19], i125[18], i125[17], i125[16], i125[15], i125[14], i125[13], i125[12], i125[11], i125[10], i125[9], i125[8], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t2 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i126[31], i126[30], i126[29], i126[28], i126[27], i126[26], i126[25], i126[24], i126[23], i126[22], i126[21], i126[20], i126[19], i126[18], i126[17], i126[16], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t3 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i127[39], i127[38], i127[37], i127[36], i127[35], i127[34], i127[33], i127[32], i127[31], i127[30], i127[29], i127[28], i127[27], i127[26], i127[25], i127[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t4 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i128[23], i128[22], i128[21], i128[20], i128[19], i128[18], i128[17], i128[16], i128[15], i128[14], i128[13], i128[12], i128[11], i128[10], i128[9], i128[8], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t5 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i129[31], i129[30], i129[29], i129[28], i129[27], i129[26], i129[25], i129[24], i129[23], i129[22], i129[21], i129[20], i129[19], i129[18], i129[17], i129[16], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t6 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i130[39], i130[38], i130[37], i130[36], i130[35], i130[34], i130[33], i130[32], i130[31], i130[30], i130[29], i130[28], i130[27], i130[26], i130[25], i130[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t7 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i131[47], i131[46], i131[45], i131[44], i131[43], i131[42], i131[41], i131[40], i131[39], i131[38], i131[37], i131[36], i131[35], i131[34], i131[33], i131[32], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t8 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i132[31], i132[30], i132[29], i132[28], i132[27], i132[26], i132[25], i132[24], i132[23], i132[22], i132[21], i132[20], i132[19], i132[18], i132[17], i132[16], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t9 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i133[39], i133[38], i133[37], i133[36], i133[35], i133[34], i133[33], i133[32], i133[31], i133[30], i133[29], i133[28], i133[27], i133[26], i133[25], i133[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t10 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i134[47], i134[46], i134[45], i134[44], i134[43], i134[42], i134[41], i134[40], i134[39], i134[38], i134[37], i134[36], i134[35], i134[34], i134[33], i134[32], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t11 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i135[55], i135[54], i135[53], i135[52], i135[51], i135[50], i135[49], i135[48], i135[47], i135[46], i135[45], i135[44], i135[43], i135[42], i135[41], i135[40], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t12 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i136[39], i136[38], i136[37], i136[36], i136[35], i136[34], i136[33], i136[32], i136[31], i136[30], i136[29], i136[28], i136[27], i136[26], i136[25], i136[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t13 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i137[47], i137[46], i137[45], i137[44], i137[43], i137[42], i137[41], i137[40], i137[39], i137[38], i137[37], i137[36], i137[35], i137[34], i137[33], i137[32], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t14 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i138[55], i138[54], i138[53], i138[52], i138[51], i138[50], i138[49], i138[48], i138[47], i138[46], i138[45], i138[44], i138[43], i138[42], i138[41], i138[40], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t15 = {i139[63], i139[62], i139[61], i139[60], i139[59], i139[58], i139[57], i139[56], i139[55], i139[54], i139[53], i139[52], i139[51], i139[50], i139[49], i139[48], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] sum = t0 + t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8 + t9 + t10 + t11 + t12 + t13 + t14 + t15;
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
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_15Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_15();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_18Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_18();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_22Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_22();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_26Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_26();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_30Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_30();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_34Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_34();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_38Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_38();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_42Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
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
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_50Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_50();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_54Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_54();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_58Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_58();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_62Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_62();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_66Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_66();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_70Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_70();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_74Core(input wire [7:0] a,input wire [7:0] b,input wire cin,output wire [15:0] value);
wire [7:0] masked_a=((a&8'hff)|8'h0);
wire [7:0] masked_b=((b&8'hff)|8'h0);
wire [15:0] aa=16'(masked_a);
wire [15:0] bb=16'(masked_b);
wire [15:0] native_value=aa*bb;
assign value=native_value[0+:16];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_74();endmodule

module Workload(input wire clk,input wire rstn,input wire iv_data,input wire iv_wen,output reg ov,input wire [31:0] a_data,input wire a_wen,input wire [31:0] b_data,input wire b_wen,input wire [63:0] c_data,input wire c_wen,output reg [63:0] y);
reg liv;wire cov;
reg [31:0] l_a;
reg [31:0] l_b;
reg [63:0] l_c;
wire [63:0] c_y;
WorkloadCore core(.iv(liv),.ov(cov),.clk(clk),.rstn(rstn),.a(l_a),.b(l_b),.c(l_c),.y(c_y));
always @(posedge clk)if(!rstn)begin liv<=1'b0;ov<=1'b0;l_a<=32'h0;l_b<=32'h0;l_c<=64'h0;y<=64'h0;end else begin if(iv_wen)liv<=iv_data;ov<=cov;if(a_wen)l_a<=a_data;if(b_wen)l_b<=b_data;if(c_wen)l_c<=c_data;y<=c_y;end
endmodule
