`timescale 1ns/1ps

module top(
    input logic [31:0] a, // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:10; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:10
    input logic [31:0] b, // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12
    output logic [63:0] y, // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:13-2:22; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:6:12-6:17
    input logic clk // decl: <none>; prim: <none>
);

    logic [63:0] s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:6:14-6:17; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12
    logic [31:0] __beopt_width_6; // decl: <none>; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:10
    logic [31:0] __beopt_width_9; // decl: <none>; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12
    logic [63:0] __beopt_width_7; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_8; // decl: <none>; prim: <none>
    logic [63:0] arith_original_8; // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:6:14-6:17; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12
    logic [63:0] rtlzz_pipe_2_s1; // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:6:14-6:17; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12
    logic [63:0] rtlzz_pipe_2_s2; // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:6:14-6:17; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12


    assign s8_norm_mul_0_v0 = arith_original_8; // decl: <none>; prim: <none>
    assign y = rtlzz_pipe_2_s2; // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:13-2:22; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:6:12-6:17
    assign __beopt_width_6 = a; // decl: <none>; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:10
    assign __beopt_width_9 = b; // decl: <none>; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12
    assign __beopt_width_7 = ({32'h0, __beopt_width_6}); // decl: <none>; prim: <none>
    assign __beopt_width_8 = ({32'h0, __beopt_width_9}); // decl: <none>; prim: <none>
    assign arith_original_8 = 64'(($unsigned(64'($unsigned(__beopt_width_7))) * $unsigned(64'($unsigned(__beopt_width_8))))); // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:6:14-6:17; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12
    always_ff @(posedge clk) begin
        rtlzz_pipe_2_s1 <= s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:6:14-6:17; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12
        rtlzz_pipe_2_s2 <= rtlzz_pipe_2_s1; // decl: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:6:14-6:17; prim: /home/zyrv/vulsim/build/step4-interfaces-20261030/acceptance/cli.logic.cpp:2:1-2:12
    end
endmodule
