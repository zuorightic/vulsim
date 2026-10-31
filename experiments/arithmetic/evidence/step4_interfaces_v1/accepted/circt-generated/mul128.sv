module mul128(	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:1:1
  input  [127:0] a,	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:1:22
                 b,	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:1:36
                 c,	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:1:50
  input          iv,	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:1:64
                 rstn,	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:1:77
                 clk,	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:1:92
  output [255:0] y,	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:1:107
                 z,	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:1:121
  output         ov	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:1:135
);

  reg          rtlzz_valid_s1;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:22:21
  wire         _GEN = ~rstn;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9
  wire [255:0] _GEN_0 = {128'h0, a};	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:6:9
  reg  [255:0] rtlzz_pipe_4_s1;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:11:22
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:11:22
    if (_GEN)	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :11:22
      rtlzz_pipe_4_s1 <= 256'h23;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:11:22
    else	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :11:22
      rtlzz_pipe_4_s1 <= iv ? _GEN_0 * {128'h0, b} : rtlzz_pipe_4_s1;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:6:9, :8:9, :9:9, :11:22
  end // always_ff @(posedge)
  reg  [255:0] rtlzz_pipe_4_s2;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:13:22
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:13:22
    if (_GEN)	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :13:22
      rtlzz_pipe_4_s2 <= 256'h23;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:13:22
    else	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :13:22
      rtlzz_pipe_4_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_4_s1 : rtlzz_pipe_4_s2;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:11:22, :13:22, :22:21
  end // always_ff @(posedge)
  reg  [255:0] rtlzz_pipe_5_s1;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:18:22
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:18:22
    if (_GEN)	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :18:22
      rtlzz_pipe_5_s1 <= 256'h37;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:18:22
    else	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :18:22
      rtlzz_pipe_5_s1 <= iv ? _GEN_0 * {128'h0, c} : rtlzz_pipe_5_s1;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:6:9, :15:10, :16:10, :18:22
  end // always_ff @(posedge)
  reg  [255:0] rtlzz_pipe_5_s2;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:20:22
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:20:22
    if (_GEN)	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :20:22
      rtlzz_pipe_5_s2 <= 256'h37;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:20:22
    else	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :20:22
      rtlzz_pipe_5_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_5_s1 : rtlzz_pipe_5_s2;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:18:22, :20:22, :22:21
  end // always_ff @(posedge)
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:22:21
    if (_GEN)	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :22:21
      rtlzz_valid_s1 <= 1'h0;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:22:21
    else	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :22:21
      rtlzz_valid_s1 <= iv;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:22:21
  end // always_ff @(posedge)
  reg          rtlzz_valid_s2;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:24:21
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:24:21
    if (_GEN)	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :24:21
      rtlzz_valid_s2 <= 1'h0;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:24:21
    else	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:4:9, :24:21
      rtlzz_valid_s2 <= rtlzz_valid_s1;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:22:21, :24:21
  end // always_ff @(posedge)
  assign y = rtlzz_pipe_4_s2;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:13:22, :25:3
  assign z = rtlzz_pipe_5_s2;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:20:22, :25:3
  assign ov = rtlzz_valid_s2;	// /tmp/rtlzz-circt-292-1949830101351056/input.mlir:24:21, :25:3
endmodule
