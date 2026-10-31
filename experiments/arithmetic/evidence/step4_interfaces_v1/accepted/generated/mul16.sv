`timescale 1ns/1ps

module mul16(
    input logic [15:0] a, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    input logic [15:0] b, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    input logic [15:0] c, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:14; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:14
    output logic [31:0] y, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:15-2:24; prim: /home/zyrv/vulsim/interface.logic.cpp:11:14-11:27
    output logic [31:0] z, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:15-2:26; prim: /home/zyrv/vulsim/interface.logic.cpp:11:28-11:41
    input logic iv, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:34; prim: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:34
    output logic ov, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:37; prim: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:37
    input logic rstn, // decl: <none>; prim: <none>
    input logic clk // decl: <none>; prim: <none>
);

    logic [31:0] s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [31:0] s8_norm_mul_1_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [15:0] __beopt_width_12; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [15:0] __beopt_width_13; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    logic [15:0] __beopt_width_17; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:14
    logic [31:0] __beopt_width_14; // decl: <none>; prim: <none>
    logic [31:0] __beopt_width_15; // decl: <none>; prim: <none>
    logic [31:0] __beopt_width_18; // decl: <none>; prim: <none>
    logic [31:0] arith_original_15; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [31:0] arith_original_16; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [31:0] rtlzz_pipe_4_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [31:0] rtlzz_pipe_4_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [31:0] rtlzz_pipe_5_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [31:0] rtlzz_pipe_5_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:34; prim: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:34
    logic rtlzz_valid_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:34; prim: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:34


    assign s8_norm_mul_0_v0 = arith_original_15; // decl: <none>; prim: <none>
    assign s8_norm_mul_1_v0 = arith_original_16; // decl: <none>; prim: <none>
    assign y = rtlzz_pipe_4_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:15-2:24; prim: /home/zyrv/vulsim/interface.logic.cpp:11:14-11:27
    assign z = rtlzz_pipe_5_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:15-2:26; prim: /home/zyrv/vulsim/interface.logic.cpp:11:28-11:41
    assign ov = rtlzz_valid_s2; // decl: <none>; prim: <none>
    assign __beopt_width_12 = a; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    assign __beopt_width_13 = b; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    assign __beopt_width_17 = c; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:14
    assign __beopt_width_14 = ({16'h0, __beopt_width_12}); // decl: <none>; prim: <none>
    assign __beopt_width_15 = ({16'h0, __beopt_width_13}); // decl: <none>; prim: <none>
    assign __beopt_width_18 = ({16'h0, __beopt_width_17}); // decl: <none>; prim: <none>
    assign arith_original_15 = 32'(($unsigned(32'($unsigned(__beopt_width_14))) * $unsigned(32'($unsigned(__beopt_width_15))))); // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    assign arith_original_16 = 32'(($unsigned(32'($unsigned(__beopt_width_14))) * $unsigned(32'($unsigned(__beopt_width_18))))); // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_4_s1 <= 32'h23;
            rtlzz_pipe_4_s2 <= 32'h23;
            rtlzz_pipe_5_s1 <= 32'h37;
            rtlzz_pipe_5_s2 <= 32'h37;
            rtlzz_valid_s1 <= 1'h0;
            rtlzz_valid_s2 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_4_s1 <= s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_4_s2 <= rtlzz_pipe_4_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
        end
        if (iv) begin
        rtlzz_pipe_5_s1 <= s8_norm_mul_1_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_5_s2 <= rtlzz_pipe_5_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:51-10:54; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:34; prim: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:34
        rtlzz_valid_s2 <= rtlzz_valid_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:34; prim: /home/zyrv/vulsim/interface.logic.cpp:2:27-2:34
        end
    end
endmodule
