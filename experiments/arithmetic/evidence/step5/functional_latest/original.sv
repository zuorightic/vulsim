`timescale 1ns/1ps

module original_core(
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
    logic [63:0] rtlzz_pipe_3_s1; // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:8:21-8:24; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:12
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:32; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:32


    assign s8_norm_mul_0_v0 = 64'(($unsigned(64'($unsigned(__beopt_width_10))) * $unsigned(64'($unsigned(__beopt_width_11))))); // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:8:21-8:24; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:12
    assign y = rtlzz_pipe_3_s1; // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:14-2:23; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:8:19-8:24
    assign ov = rtlzz_valid_s1; // decl: <none>; prim: <none>
    assign __beopt_width_8 = a; // decl: <none>; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:10
    assign __beopt_width_9 = b; // decl: <none>; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:12
    assign __beopt_width_10 = ({32'h0, __beopt_width_8}); // decl: <none>; prim: <none>
    assign __beopt_width_11 = ({32'h0, __beopt_width_9}); // decl: <none>; prim: <none>
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_3_s1 <= 64'h0;
            rtlzz_valid_s1 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_3_s1 <= s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:8:21-8:24; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:1-2:12
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:32; prim: /home/zyrv/vulsim/mul_kernel.logic.cpp:2:25-2:32
        end
    end
endmodule

module original(input logic clk,rstn,input logic [31:0] a,b,input logic iv,output logic [63:0] y,output logic ov);
logic [31:0] aq,bq;logic ivq,ovd;logic [63:0] yd;
original_core core(.clk(clk),.rstn(rstn),.a(aq),.b(bq),.iv(ivq),.y(yd),.ov(ovd));
always_ff @(posedge clk) if(!rstn) begin aq<=0;bq<=0;ivq<=0;y<=0;ov<=0;end else begin aq<=a;bq<=b;ivq<=iv;ov<=ovd;if(ovd) y<=yd;end
endmodule
