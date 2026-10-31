`timescale 1ns/1ps
module ArithmeticInterfaces(input logic clk,rstn,iv,input logic [127:0] a,b,c,
output logic [255:0] ys[0:8],zs[0:8],output logic [8:0] ovs,
output logic fov,output logic [36:0] fy,fz,fcy,fcz,output logic [63:0] fm,fcm);
wire [15:0] y0,z0;wire v0;
mul8 u0(.clk(clk),.rstn(rstn),.iv(iv),.ov(v0),.a(a[7:0]),.b(b[7:0]),.c(c[7:0]),.y(y0),.z(z0));
always_ff @(posedge clk) begin
if(!rstn) begin ovs[0]<=0;ys[0]<=256'd35;zs[0]<=256'd55;end
else begin ovs[0]<=v0;if(v0)begin ys[0]<=256'(y0);zs[0]<=256'(z0);end end
end
wire [31:0] y1,z1;wire v1;
mul16 u1(.clk(clk),.rstn(rstn),.iv(iv),.ov(v1),.a(a[15:0]),.b(b[15:0]),.c(c[15:0]),.y(y1),.z(z1));
always_ff @(posedge clk) begin
if(!rstn) begin ovs[1]<=0;ys[1]<=256'd35;zs[1]<=256'd55;end
else begin ovs[1]<=v1;if(v1)begin ys[1]<=256'(y1);zs[1]<=256'(z1);end end
end
wire [63:0] y2,z2;wire v2;
mul32 u2(.clk(clk),.rstn(rstn),.iv(iv),.ov(v2),.a(a[31:0]),.b(b[31:0]),.c(c[31:0]),.y(y2),.z(z2));
always_ff @(posedge clk) begin
if(!rstn) begin ovs[2]<=0;ys[2]<=256'd35;zs[2]<=256'd55;end
else begin ovs[2]<=v2;if(v2)begin ys[2]<=256'(y2);zs[2]<=256'(z2);end end
end
wire [127:0] y3,z3;wire v3;
mul64 u3(.clk(clk),.rstn(rstn),.iv(iv),.ov(v3),.a(a[63:0]),.b(b[63:0]),.c(c[63:0]),.y(y3),.z(z3));
always_ff @(posedge clk) begin
if(!rstn) begin ovs[3]<=0;ys[3]<=256'd35;zs[3]<=256'd55;end
else begin ovs[3]<=v3;if(v3)begin ys[3]<=256'(y3);zs[3]<=256'(z3);end end
end
wire [255:0] y4,z4;wire v4;
mul128 u4(.clk(clk),.rstn(rstn),.iv(iv),.ov(v4),.a(a[127:0]),.b(b[127:0]),.c(c[127:0]),.y(y4),.z(z4));
always_ff @(posedge clk) begin
if(!rstn) begin ovs[4]<=0;ys[4]<=256'd35;zs[4]<=256'd55;end
else begin ovs[4]<=v4;if(v4)begin ys[4]<=256'(y4);zs[4]<=256'(z4);end end
end
wire [23:0] y5,z5;wire v5;
mul12 u5(.clk(clk),.rstn(rstn),.iv(iv),.ov(v5),.a(a[11:0]),.b(b[11:0]),.c(c[11:0]),.y(y5),.z(z5));
always_ff @(posedge clk) begin
if(!rstn) begin ovs[5]<=0;ys[5]<=256'd35;zs[5]<=256'd55;end
else begin ovs[5]<=v5;if(v5)begin ys[5]<=256'(y5);zs[5]<=256'(z5);end end
end
wire [47:0] y6,z6;wire v6;
mul24 u6(.clk(clk),.rstn(rstn),.iv(iv),.ov(v6),.a(a[23:0]),.b(b[23:0]),.c(c[23:0]),.y(y6),.z(z6));
always_ff @(posedge clk) begin
if(!rstn) begin ovs[6]<=0;ys[6]<=256'd35;zs[6]<=256'd55;end
else begin ovs[6]<=v6;if(v6)begin ys[6]<=256'(y6);zs[6]<=256'(z6);end end
end
wire [95:0] y7,z7;wire v7;
mul48 u7(.clk(clk),.rstn(rstn),.iv(iv),.ov(v7),.a(a[47:0]),.b(b[47:0]),.c(c[47:0]),.y(y7),.z(z7));
always_ff @(posedge clk) begin
if(!rstn) begin ovs[7]<=0;ys[7]<=256'd35;zs[7]<=256'd55;end
else begin ovs[7]<=v7;if(v7)begin ys[7]<=256'(y7);zs[7]<=256'(z7);end end
end
wire [191:0] y8,z8;wire v8;
mul96 u8(.clk(clk),.rstn(rstn),.iv(iv),.ov(v8),.a(a[95:0]),.b(b[95:0]),.c(c[95:0]),.y(y8),.z(z8));
always_ff @(posedge clk) begin
if(!rstn) begin ovs[8]<=0;ys[8]<=256'd35;zs[8]<=256'd55;end
else begin ovs[8]<=v8;if(v8)begin ys[8]<=256'(y8);zs[8]<=256'(z8);end end
end
wire [36:0] fy0,fz0;wire [63:0] fm0;wire fv0;
top fp(.clk(clk),.rstn(rstn),.iv(iv),.ov(fv0),.a(a[31:0]),.b(b[31:0]),.c(c[31:0]),.y(fy0),.z(fz0),.m(fm0));
fp_comb comb(.iv(iv),.ov(),.a(a[31:0]),.b(b[31:0]),.c(c[31:0]),.y(fcy),.z(fcz),.m(fcm));
always_ff @(posedge clk) begin
if(!rstn)begin fov<=0;fy<=37'd70862766080;fz<=37'd2139095040;fm<=64'd0;end
else begin fov<=fv0;if(fv0)begin fy<=fy0;fz<=fz0;fm<=fm0;end end
end
endmodule
