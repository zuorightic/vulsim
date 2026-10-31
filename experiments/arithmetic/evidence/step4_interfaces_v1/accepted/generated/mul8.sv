`timescale 1ns/1ps

module mul8(
    input logic [7:0] a, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    input logic [7:0] b, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    input logic [7:0] c, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:13; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:13
    output logic [15:0] y, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:14-2:23; prim: /home/zyrv/vulsim/interface.logic.cpp:11:13-11:26
    output logic [15:0] z, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:14-2:25; prim: /home/zyrv/vulsim/interface.logic.cpp:11:27-11:40
    input logic iv, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:33; prim: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:33
    output logic ov, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:36; prim: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:36
    input logic rstn, // decl: <none>; prim: <none>
    input logic clk // decl: <none>; prim: <none>
);

    logic [15:0] s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    logic [15:0] s8_norm_mul_1_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    logic [7:0] __beopt_width_12; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    logic [7:0] __beopt_width_13; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    logic [7:0] __beopt_width_17; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:13
    logic [15:0] __beopt_width_14; // decl: <none>; prim: <none>
    logic [15:0] __beopt_width_15; // decl: <none>; prim: <none>
    logic [15:0] __beopt_width_18; // decl: <none>; prim: <none>
    logic [15:0] arith_original_15; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    logic [15:0] arith_original_16; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    logic [15:0] rtlzz_pipe_4_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    logic [15:0] rtlzz_pipe_4_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    logic [15:0] rtlzz_pipe_5_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    logic [15:0] rtlzz_pipe_5_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:33; prim: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:33
    logic rtlzz_valid_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:33; prim: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:33


    assign s8_norm_mul_0_v0 = arith_original_15; // decl: <none>; prim: <none>
    assign s8_norm_mul_1_v0 = arith_original_16; // decl: <none>; prim: <none>
    assign y = rtlzz_pipe_4_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:14-2:23; prim: /home/zyrv/vulsim/interface.logic.cpp:11:13-11:26
    assign z = rtlzz_pipe_5_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:14-2:25; prim: /home/zyrv/vulsim/interface.logic.cpp:11:27-11:40
    assign ov = rtlzz_valid_s2; // decl: <none>; prim: <none>
    assign __beopt_width_12 = a; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    assign __beopt_width_13 = b; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:11
    assign __beopt_width_17 = c; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:13
    assign __beopt_width_14 = ({8'h0, __beopt_width_12}); // decl: <none>; prim: <none>
    assign __beopt_width_15 = ({8'h0, __beopt_width_13}); // decl: <none>; prim: <none>
    assign __beopt_width_18 = ({8'h0, __beopt_width_17}); // decl: <none>; prim: <none>
    assign arith_original_15 = 16'(($unsigned(16'($unsigned(__beopt_width_14))) * $unsigned(16'($unsigned(__beopt_width_15))))); // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    assign arith_original_16 = 16'(($unsigned(16'($unsigned(__beopt_width_14))) * $unsigned(16'($unsigned(__beopt_width_18))))); // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_4_s1 <= 16'h23;
            rtlzz_pipe_4_s2 <= 16'h23;
            rtlzz_pipe_5_s1 <= 16'h37;
            rtlzz_pipe_5_s2 <= 16'h37;
            rtlzz_valid_s1 <= 1'h0;
            rtlzz_valid_s2 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_4_s1 <= s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_4_s2 <= rtlzz_pipe_4_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
        end
        if (iv) begin
        rtlzz_pipe_5_s1 <= s8_norm_mul_1_v0; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_5_s2 <= rtlzz_pipe_5_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:10:49-10:52; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:9
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:33; prim: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:33
        rtlzz_valid_s2 <= rtlzz_valid_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:33; prim: /home/zyrv/vulsim/interface.logic.cpp:2:26-2:33
        end
    end
endmodule
