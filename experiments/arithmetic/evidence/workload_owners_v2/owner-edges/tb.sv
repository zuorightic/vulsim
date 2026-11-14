module tb;
reg [12:0] x,y;reg iv;wire [13:0] s;wire [12:0] m0,m1;wire ov;
owner_edges dut(.x(x),.y(y),.iv(iv),.s(s),.m0(m0),.m1(m1),.ov(ov));
integer i;reg [13:0] expected;
initial begin
for(i=0;i<4096;i=i+1)begin
x=(i*997+8191)&8191;y=(i*617+1)&8191;iv=i&1;
#1;expected={1'b0,x}+{1'b0,y}+(x<y);
if(s!==expected||m0!==(x<y?13'h1555:x)||m1!==(x<y?y:13'haaa)||ov!==iv)begin
$display("FAIL %d %h %h",i,x,y);$fatal;end
end
$display("PASS owner_edges vectors=4096 L=1 carry_and_selector");$finish;
end
endmodule
