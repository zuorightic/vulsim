`timescale 1ns/1ps

module mul128(
    input logic [127:0] a, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    input logic [127:0] b, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:13; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:13
    input logic [127:0] c, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:15; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:15
    output logic [255:0] y, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:16-2:26; prim: /home/zyrv/vulsim/interface.logic.cpp:11:15-11:28
    output logic [255:0] z, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:16-2:28; prim: /home/zyrv/vulsim/interface.logic.cpp:11:29-11:42
    input logic iv, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:36; prim: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:36
    output logic ov, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:39; prim: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:39
    input logic rstn, // decl: <none>; prim: <none>
    input logic clk // decl: <none>; prim: <none>
);

    logic [255:0] s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    logic [255:0] s8_norm_mul_1_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    logic [127:0] __beopt_width_12; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    logic [127:0] __beopt_width_13; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:13
    logic [127:0] __beopt_width_17; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:15
    logic [255:0] __beopt_width_14; // decl: <none>; prim: <none>
    logic [255:0] __beopt_width_15; // decl: <none>; prim: <none>
    logic [255:0] __beopt_width_18; // decl: <none>; prim: <none>
    logic [255:0] arith_original_15; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    logic [255:0] arith_original_16; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    logic [255:0] rtlzz_pipe_4_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    logic [255:0] rtlzz_pipe_4_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    logic [255:0] rtlzz_pipe_5_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    logic [255:0] rtlzz_pipe_5_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:36; prim: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:36
    logic rtlzz_valid_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:36; prim: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:36


    assign s8_norm_mul_0_v0 = arith_original_15; // decl: <none>; prim: <none>
    assign s8_norm_mul_1_v0 = arith_original_16; // decl: <none>; prim: <none>
    assign y = rtlzz_pipe_4_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:16-2:26; prim: /home/zyrv/vulsim/interface.logic.cpp:11:15-11:28
    assign z = rtlzz_pipe_5_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:16-2:28; prim: /home/zyrv/vulsim/interface.logic.cpp:11:29-11:42
    assign ov = rtlzz_valid_s2; // decl: <none>; prim: <none>
    assign __beopt_width_12 = a; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    assign __beopt_width_13 = b; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:13
    assign __beopt_width_17 = c; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:15
    assign __beopt_width_14 = ({128'h0, __beopt_width_12}); // decl: <none>; prim: <none>
    assign __beopt_width_15 = ({128'h0, __beopt_width_13}); // decl: <none>; prim: <none>
    assign __beopt_width_18 = ({128'h0, __beopt_width_17}); // decl: <none>; prim: <none>
    assign arith_original_15 = 256'(($unsigned(256'($unsigned(__beopt_width_14))) * $unsigned(256'($unsigned(__beopt_width_15))))); // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    assign arith_original_16 = 256'(($unsigned(256'($unsigned(__beopt_width_14))) * $unsigned(256'($unsigned(__beopt_width_18))))); // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_4_s1 <= 256'h23;
            rtlzz_pipe_4_s2 <= 256'h23;
            rtlzz_pipe_5_s1 <= 256'h37;
            rtlzz_pipe_5_s2 <= 256'h37;
            rtlzz_valid_s1 <= 1'h0;
            rtlzz_valid_s2 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_4_s1 <= s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_4_s2 <= rtlzz_pipe_4_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
        end
        if (iv) begin
        rtlzz_pipe_5_s1 <= s8_norm_mul_1_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_5_s2 <= rtlzz_pipe_5_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:54-10:57; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:36; prim: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:36
        rtlzz_valid_s2 <= rtlzz_valid_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:36; prim: /home/zyrv/vulsim/interface.logic.cpp:2:29-2:36
        end
    end
endmodule
