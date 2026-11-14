`timescale 1ns/1ps

module owner_edges(
    input logic [12:0] x, // decl: <none>; prim: <none>
    input logic [12:0] y, // decl: <none>; prim: <none>
    input logic iv, // decl: <none>; prim: <none>
    output logic [13:0] s, // decl: <none>; prim: <none>
    output logic [12:0] m0, // decl: <none>; prim: <none>
    output logic [12:0] m1, // decl: <none>; prim: <none>
    output logic ov // decl: <none>; prim: <none>
);

    logic n3; // decl: <none>; prim: <none>
    logic [13:0] n4; // decl: <none>; prim: <none>
    logic [12:0] n5; // decl: <none>; prim: <none>
    logic [12:0] n6; // decl: <none>; prim: <none>
    logic [13:0] n7; // decl: <none>; prim: <none>
    logic [12:0] n8; // decl: <none>; prim: <none>
    logic [12:0] n9; // decl: <none>; prim: <none>
    logic n10; // decl: <none>; prim: <none>

    assign s = n7; // decl: <none>; prim: <none>
    assign m0 = n8; // decl: <none>; prim: <none>
    assign m1 = n9; // decl: <none>; prim: <none>
    assign ov = n10; // decl: <none>; prim: <none>

    (* keep_hierarchy=1 *) owner_edges__rtlzz_arith_3Core rtlzz_owner_3(.a(13'(x)), .b(13'(y)), .cin(1'b0), .value(n3));
    (* keep_hierarchy=1 *) owner_edges__rtlzz_arith_4Core rtlzz_owner_4(.a(13'(x)), .b(13'(y)), .cin(n3), .value(n4));
    (* keep_hierarchy=1 *) owner_edges__rtlzz_arith_5Core rtlzz_owner_5(.a(13'(x)), .b(13'(13'h1555)), .cin(n3), .value(n5));
    (* keep_hierarchy=1 *) owner_edges__rtlzz_arith_6Core rtlzz_owner_6(.a(13'(13'haaa)), .b(13'(y)), .cin(n3), .value(n6));
    assign n7 = n4; // decl: <none>; prim: <none>
    assign n8 = n5; // decl: <none>; prim: <none>
    assign n9 = n6; // decl: <none>; prim: <none>
    assign n10 = iv; // decl: <none>; prim: <none>
endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module owner_edges__rtlzz_arith_3Core(input wire [12:0] a,input wire [12:0] b,input wire cin,output wire [0:0] value);
wire [12:0] masked_a=((a&13'h1fff)|13'h0);
wire [12:0] masked_b=((b&13'h1fff)|13'h0);
wire [12:0] aa=13'(masked_a);
wire [12:0] bb=13'(masked_b);
wire [12:0] native_value=13'(aa<bb);
assign value=native_value[0+:1];
endmodule
(* keep_hierarchy=1 *) module owner_edges__rtlzz_arith_3();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module owner_edges__rtlzz_arith_4Core(input wire [12:0] a,input wire [12:0] b,input wire cin,output wire [13:0] value);
wire [12:0] masked_a=((a&13'h1fff)|13'h0);
wire [12:0] masked_b=((b&13'h1fff)|13'h0);
wire [13:0] aa=14'(masked_a);
wire [13:0] bb=14'(masked_b);
wire [14:0] extended={1'b0,aa}+{1'b0,bb}+15'(cin);
wire [13:0] native_value=extended[13:0];
assign value=native_value[0+:14];
endmodule
(* keep_hierarchy=1 *) module owner_edges__rtlzz_arith_4();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module owner_edges__rtlzz_arith_5Core(input wire [12:0] a,input wire [12:0] b,input wire cin,output wire [12:0] value);
wire [12:0] masked_a=((a&13'h1fff)|13'h0);
wire [12:0] masked_b=((b&13'h0)|13'h1555);
wire [12:0] aa=13'(masked_a);
wire [12:0] bb=13'(masked_b);
wire [12:0] native_value=cin?bb:aa;
assign value=native_value[0+:13];
endmodule
(* keep_hierarchy=1 *) module owner_edges__rtlzz_arith_5();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module owner_edges__rtlzz_arith_6Core(input wire [12:0] a,input wire [12:0] b,input wire cin,output wire [12:0] value);
wire [12:0] masked_a=((a&13'h0)|13'haaa);
wire [12:0] masked_b=((b&13'h1fff)|13'h0);
wire [12:0] aa=13'(masked_a);
wire [12:0] bb=13'(masked_b);
wire [12:0] native_value=cin?bb:aa;
assign value=native_value[0+:13];
endmodule
(* keep_hierarchy=1 *) module owner_edges__rtlzz_arith_6();endmodule
