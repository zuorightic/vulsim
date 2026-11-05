`timescale 1ns/1ps

module top(
    input logic [7:0] a, // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:8; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:8
    input logic [7:0] b, // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:10; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:10
    input logic [7:0] c, // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:12; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:12
    input logic [7:0] d, // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:14; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:14
    output logic [7:0] y, // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:16; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:12-13:20
    output logic [7:0] z, // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:18; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:21-13:29
    input logic sa, // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:26; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:26
    input logic sb, // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:29; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:29
    input logic iv, // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:32; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:32
    output logic ov, // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:35; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:35
    input logic rstn, // decl: <none>; prim: <none>
    input logic clk // decl: <none>; prim: <none>
);

    logic [7:0] s8_norm_mux_0_v0; // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:14-13:20; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:14-13:20
    logic [7:0] s8_norm_mux_1_v0; // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:23-13:29; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:23-13:29
    logic [7:0] rtlzz_pipe_7_s1; // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:14-13:20; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:14-13:20
    logic [7:0] rtlzz_pipe_8_s1; // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:23-13:29; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:23-13:29
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:32; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:32


    assign s8_norm_mux_0_v0 = (sa ? a : b); // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:14-13:20; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:14-13:20
    assign s8_norm_mux_1_v0 = (sb ? c : d); // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:23-13:29; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:23-13:29
    assign y = rtlzz_pipe_7_s1; // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:16; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:12-13:20
    assign z = rtlzz_pipe_8_s1; // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:1-2:18; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:21-13:29
    assign ov = rtlzz_valid_s1; // decl: <none>; prim: <none>
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_7_s1 <= 8'h0;
            rtlzz_pipe_8_s1 <= 8'h0;
            rtlzz_valid_s1 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_7_s1 <= s8_norm_mux_0_v0; // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:14-13:20; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:14-13:20
        end
        if (iv) begin
        rtlzz_pipe_8_s1 <= s8_norm_mux_1_v0; // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:23-13:29; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:13:23-13:29
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:32; prim: /home/zyrv/vulsim/published-stage-binding.logic.cpp:2:19-2:32
        end
    end
endmodule
