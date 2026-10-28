`timescale 1ns/1ps
module MulSplitRegression(input logic clk,rstn,iv,input logic [31:0] a,b,
output logic [63:0] y0,y1,output logic ov0,ov1);
original u0(.clk(clk),.rstn(rstn),.a(a),.b(b),.iv(iv),.y(y0),.ov(ov0));
mul32_split16 u1(.clk(clk),.rstn(rstn),.a(a),.b(b),.iv(iv),.y(y1),.ov(ov1));
endmodule
