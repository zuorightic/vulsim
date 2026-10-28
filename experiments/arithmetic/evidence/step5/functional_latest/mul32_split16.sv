`timescale 1ns/1ps

module mul32_split16_core(
    input logic [31:0] a, // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:10; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:10
    input logic [31:0] b, // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:12; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:12
    output logic [63:0] y, // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:14-2:23; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:8:19-8:24
    input logic iv, // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:32; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:32
    output logic ov, // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:35; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:35
    input logic rstn, // decl: <none>; prim: <none>
    input logic clk // decl: <none>; prim: <none>
);

    logic [63:0] s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:8:21-8:24; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:12
    logic [31:0] __beopt_width_8; // decl: <none>; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:10
    logic [31:0] __beopt_width_9; // decl: <none>; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:12
    logic [63:0] __beopt_width_10; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_11; // decl: <none>; prim: <none>
    logic [15:0] mul_split_3_10; // decl: <none>; prim: <none>
    logic [15:0] mul_split_3_11; // decl: <none>; prim: <none>
    logic [15:0] mul_split_3_12; // decl: <none>; prim: <none>
    logic [15:0] mul_split_3_13; // decl: <none>; prim: <none>
    logic [31:0] mul_split_3_14; // decl: <none>; prim: <none>
    logic [31:0] mul_split_3_15; // decl: <none>; prim: <none>
    logic [31:0] mul_split_3_16; // decl: <none>; prim: <none>
    logic [31:0] mul_split_3_17; // decl: <none>; prim: <none>
    logic [15:0] mul_split_3_18; // decl: <none>; prim: <none>
    logic [15:0] mul_split_3_19; // decl: <none>; prim: <none>
    logic [31:0] mul_split_3_20; // decl: <none>; prim: <none>
    logic [32:0] mul_split_3_21; // decl: <none>; prim: <none>
    logic [32:0] mul_split_3_22; // decl: <none>; prim: <none>
    logic [33:0] mul_split_3_23; // decl: <none>; prim: <none>
    logic [17:0] mul_split_3_24; // decl: <none>; prim: <none>
    logic [31:0] mul_split_3_25; // decl: <none>; prim: <none>
    logic [32:0] mul_split_3_26; // decl: <none>; prim: <none>
    logic [31:0] mul_split_3_27; // decl: <none>; prim: <none>
    logic [15:0] mul_split_3_28; // decl: <none>; prim: <none>
    logic [63:0] mul_split_3_29; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_15_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_16_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_17_s1; // decl: <none>; prim: <none>
    logic [15:0] rtlzz_pipe_18_s1; // decl: <none>; prim: <none>
    logic [15:0] rtlzz_pipe_19_s1; // decl: <none>; prim: <none>
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:32; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:32


    assign s8_norm_mul_0_v0 = mul_split_3_29; // decl: <none>; prim: <none>
    assign y = s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:14-2:23; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:8:19-8:24
    assign ov = rtlzz_valid_s1; // decl: <none>; prim: <none>
    assign __beopt_width_8 = a; // decl: <none>; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:10
    assign __beopt_width_9 = b; // decl: <none>; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:12
    assign __beopt_width_10 = ({32'h0, __beopt_width_8}); // decl: <none>; prim: <none>
    assign __beopt_width_11 = ({32'h0, __beopt_width_9}); // decl: <none>; prim: <none>
    assign mul_split_3_10 = __beopt_width_10[15:0]; // decl: <none>; prim: <none>
    assign mul_split_3_11 = __beopt_width_10[31:16]; // decl: <none>; prim: <none>
    assign mul_split_3_12 = __beopt_width_11[15:0]; // decl: <none>; prim: <none>
    assign mul_split_3_13 = __beopt_width_11[31:16]; // decl: <none>; prim: <none>
    assign mul_split_3_14 = 32'(($unsigned(32'($unsigned(mul_split_3_10))) * $unsigned(32'($unsigned(mul_split_3_12))))); // decl: <none>; prim: <none>
    assign mul_split_3_15 = 32'(($unsigned(32'($unsigned(mul_split_3_10))) * $unsigned(32'($unsigned(mul_split_3_13))))); // decl: <none>; prim: <none>
    assign mul_split_3_16 = 32'(($unsigned(32'($unsigned(mul_split_3_11))) * $unsigned(32'($unsigned(mul_split_3_12))))); // decl: <none>; prim: <none>
    assign mul_split_3_17 = 32'(($unsigned(32'($unsigned(mul_split_3_11))) * $unsigned(32'($unsigned(mul_split_3_13))))); // decl: <none>; prim: <none>
    assign mul_split_3_18 = mul_split_3_14[15:0]; // decl: <none>; prim: <none>
    assign mul_split_3_19 = mul_split_3_14[31:16]; // decl: <none>; prim: <none>
    assign mul_split_3_20 = ({16'h0, rtlzz_pipe_19_s1}); // decl: <none>; prim: <none>
    assign mul_split_3_21 = 33'((({1'h0, mul_split_3_20}) + ({1'h0, rtlzz_pipe_15_s1}) + ({32'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_split_3_22 = ({1'h0, rtlzz_pipe_16_s1}); // decl: <none>; prim: <none>
    assign mul_split_3_23 = 34'((({1'h0, mul_split_3_21}) + ({1'h0, mul_split_3_22}) + ({33'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_split_3_24 = mul_split_3_23[33:16]; // decl: <none>; prim: <none>
    assign mul_split_3_25 = ({14'h0, mul_split_3_24}); // decl: <none>; prim: <none>
    assign mul_split_3_26 = 33'((({1'h0, rtlzz_pipe_17_s1}) + ({1'h0, mul_split_3_25}) + ({32'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_split_3_27 = mul_split_3_26[31:0]; // decl: <none>; prim: <none>
    assign mul_split_3_28 = mul_split_3_23[15:0]; // decl: <none>; prim: <none>
    assign mul_split_3_29 = {mul_split_3_27, mul_split_3_28, rtlzz_pipe_18_s1}; // decl: <none>; prim: <none>
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_15_s1 <= 32'h0;
            rtlzz_pipe_16_s1 <= 32'h0;
            rtlzz_pipe_17_s1 <= 32'h0;
            rtlzz_pipe_18_s1 <= 16'h0;
            rtlzz_pipe_19_s1 <= 16'h0;
            rtlzz_valid_s1 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_15_s1 <= mul_split_3_15; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_16_s1 <= mul_split_3_16; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_17_s1 <= mul_split_3_17; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_18_s1 <= mul_split_3_18; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_19_s1 <= mul_split_3_19; // decl: <none>; prim: <none>
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:32; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:32
        end
    end
endmodule

module mul32_split16(input logic clk,rstn,input logic [31:0] a,b,input logic iv,output logic [63:0] y,output logic ov);
logic [31:0] aq,bq;logic ivq,ovd;logic [63:0] yd;
mul32_split16_core core(.clk(clk),.rstn(rstn),.a(aq),.b(bq),.iv(ivq),.y(yd),.ov(ovd));
always_ff @(posedge clk) if(!rstn) begin aq<=0;bq<=0;ivq<=0;y<=0;ov<=0;end else begin aq<=a;bq<=b;ivq<=iv;ov<=ovd;if(ovd) y<=yd;end
endmodule
