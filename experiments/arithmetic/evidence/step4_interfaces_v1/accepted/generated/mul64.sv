`timescale 1ns/1ps

module mul64(
    input logic [63:0] a, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    input logic [63:0] b, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    input logic [63:0] c, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:14; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:14
    output logic [127:0] y, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:15-2:25; prim: /home/zyrv/vulsim/interface.logic.cpp:11:14-11:27
    output logic [127:0] z, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:15-2:27; prim: /home/zyrv/vulsim/interface.logic.cpp:11:28-11:41
    input logic iv, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:35; prim: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:35
    output logic ov, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:38; prim: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:38
    input logic rstn, // decl: <none>; prim: <none>
    input logic clk // decl: <none>; prim: <none>
);

    logic [127:0] s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [127:0] s8_norm_mul_1_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [63:0] __beopt_width_12; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [63:0] __beopt_width_13; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    logic [63:0] __beopt_width_17; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:14
    logic [127:0] __beopt_width_14; // decl: <none>; prim: <none>
    logic [127:0] __beopt_width_15; // decl: <none>; prim: <none>
    logic [127:0] __beopt_width_18; // decl: <none>; prim: <none>
    logic [127:0] arith_original_15; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [127:0] arith_original_16; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [127:0] rtlzz_pipe_4_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [127:0] rtlzz_pipe_4_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [127:0] rtlzz_pipe_5_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [127:0] rtlzz_pipe_5_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:35; prim: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:35
    logic rtlzz_valid_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:35; prim: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:35


    assign s8_norm_mul_0_v0 = arith_original_15; // decl: <none>; prim: <none>
    assign s8_norm_mul_1_v0 = arith_original_16; // decl: <none>; prim: <none>
    assign y = rtlzz_pipe_4_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:15-2:25; prim: /home/zyrv/vulsim/interface.logic.cpp:11:14-11:27
    assign z = rtlzz_pipe_5_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:15-2:27; prim: /home/zyrv/vulsim/interface.logic.cpp:11:28-11:41
    assign ov = rtlzz_valid_s2; // decl: <none>; prim: <none>
    assign __beopt_width_12 = a; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    assign __beopt_width_13 = b; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    assign __beopt_width_17 = c; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:14
    assign __beopt_width_14 = ({64'h0, __beopt_width_12}); // decl: <none>; prim: <none>
    assign __beopt_width_15 = ({64'h0, __beopt_width_13}); // decl: <none>; prim: <none>
    assign __beopt_width_18 = ({64'h0, __beopt_width_17}); // decl: <none>; prim: <none>
    assign arith_original_15 = 128'(($unsigned(128'($unsigned(__beopt_width_14))) * $unsigned(128'($unsigned(__beopt_width_15))))); // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    assign arith_original_16 = 128'(($unsigned(128'($unsigned(__beopt_width_14))) * $unsigned(128'($unsigned(__beopt_width_18))))); // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_4_s1 <= 128'h23;
            rtlzz_pipe_4_s2 <= 128'h23;
            rtlzz_pipe_5_s1 <= 128'h37;
            rtlzz_pipe_5_s2 <= 128'h37;
            rtlzz_valid_s1 <= 1'h0;
            rtlzz_valid_s2 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_4_s1 <= s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_4_s2 <= rtlzz_pipe_4_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
        end
        if (iv) begin
        rtlzz_pipe_5_s1 <= s8_norm_mul_1_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_5_s2 <= rtlzz_pipe_5_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:52-10:55; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:35; prim: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:35
        rtlzz_valid_s2 <= rtlzz_valid_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:35; prim: /home/zyrv/vulsim/interface.logic.cpp:2:28-2:35
        end
    end
endmodule
