`timescale 1ns/1ps

module Top_sim_top(
  input clk,
  input rstn,
  output [0:0] valid__query__,
  output [4265:0] result__query__,
  input echo257__vld__,
  input [256:0] echo257_value__,
  output [256:0] echo257_result__,
  input echo256__vld__,
  input [255:0] echo256_value__,
  output [255:0] echo256_result__,
  input echo193__vld__,
  input [192:0] echo193_value__,
  output [192:0] echo193_result__,
  input echo128__vld__,
  input [127:0] echo128_value__,
  output [127:0] echo128_result__,
  input echo129__vld__,
  input [128:0] echo129_value__,
  output [128:0] echo129_result__,
  input combine__vld__,
  input [1033:0] combine_value__,
  output [4265:0] combine_result__,
  input push__vld__,
  input [1033:0] push_value__,
  input [0:0] push_valid__
);

reg [1033:0] __vul_pipeline_q_input;
wire [1033:0] resetvalue_input__;
wire wen_input__;
wire [1033:0] wdata_input__;
reg [0:0] __vul_pipeline_q_iv = 1'b0;
wire [0:0] resetvalue_iv__;
wire wen_iv__;
wire [0:0] wdata_iv__;
reg [4265:0] __vul_pipeline_q_output;
wire [4265:0] __vul_pipeline_d_output;
reg [0:0] __vul_pipeline_q_ov = 1'b0;
wire [0:0] __vul_pipeline_d_ov;

always @(posedge clk) begin
  if (rstn == 0) begin
    __vul_pipeline_q_input <= resetvalue_input__;
  end else begin
begin
    if (wen_input__) begin
      __vul_pipeline_q_input <= wdata_input__;
    end
    end
  end
end
always @(posedge clk) begin
  if (rstn == 0) begin
    __vul_pipeline_q_iv <= resetvalue_iv__;
  end else begin
begin
    if (wen_iv__) begin
      __vul_pipeline_q_iv <= wdata_iv__;
    end
    end
  end
end
always @(posedge clk) begin
  if (!rstn) begin
    __vul_pipeline_q_output <= 4266'h3fffffffffffffffffffffffffffffff800000000000000000000000000000007fffffffffffffffffffffffffffffffc0000000000000000000000000000000200000000000000000000000000000003fffffffffffffffffffffffffffffffdffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff800000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffdfffffffffffffffffffffffffffffffc00000000000000000000000000000001fffffffffffffffffffffffffffffffc0000000000000000000000000000000200000000000000000000000000000001fffffffffffffffffffffffffffffffe000000000000000000000000000000010000000000000000c000000000000000000000000000000000000000000000007fffffffffffffffffffffffffffffffbfffffffffffffff80000000000000003fffffffffffffff800000000000000040000000000000003fffffffffffffffc000000000000000200000001800000000000000000000000ffffffffffffffff7fffffff000000007fffffff00000000800000007fffffff8000000040003000000000001fffffffefffe0000fffe00010000ffff0000806000003fffdfc01fc0201fe01;
  end else begin
  __vul_pipeline_q_output <= __vul_pipeline_d_output;
  end
end
always @(posedge clk) begin
  if (!rstn) begin
    __vul_pipeline_q_ov <= 1'h0;
  end else begin
  __vul_pipeline_q_ov <= __vul_pipeline_d_ov;
  end
end

if (1) begin : __vul_pipeline_calculate
  logic [1033:0] __vul_port_input;
  assign __vul_port_input = __vul_pipeline_q_input;
  logic __vul_port_iv;
  assign __vul_port_iv = __vul_pipeline_q_iv;
  logic [4265:0] __vul_port_output;
  assign __vul_pipeline_d_output = __vul_port_output;
  logic __vul_port_ov;
  assign __vul_pipeline_d_ov = __vul_port_ov;


  wire [255:0] _GEN =
    {128'h0, __vul_port_input[127:0]} * {128'h0, __vul_port_input[255:128]};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:5:9, :7:9, :8:9, :10:9, :11:9
  wire [256:0] _GEN_0 =
    {1'h0, _GEN}
    + {1'h0, {128'h0, __vul_port_input[383:256]} * {128'h0, __vul_port_input[511:384]}};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:11:9, :13:10, :14:10, :16:10, :17:10, :19:10, :20:10, :22:10, :23:10
  wire [127:0] _GEN_1 = {121'h0, __vul_port_input[1031:1025]};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:36:10, :38:10
  wire [63:0]  _GEN_2 = {58'h0, __vul_port_input[1030:1025]};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:93:10, :95:10
  wire [127:0] _GEN_3 =
    {64'h0, __vul_port_input[63:0]} * {64'h0, __vul_port_input[191:128]};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:84:10, :85:10, :136:11, :138:11, :139:11
  wire [31:0]  _GEN_4 = {27'h0, __vul_port_input[1029:1025]};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:166:11
  wire [63:0]  _GEN_5 =
    {32'h0, __vul_port_input[31:0]} * {32'h0, __vul_port_input[159:128]};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:157:11, :158:11, :205:11, :207:11, :208:11
  wire [15:0]  _GEN_6 = {12'h0, __vul_port_input[1028:1025]};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:235:11, :236:11
  wire [31:0]  _GEN_7 =
    {16'h0, __vul_port_input[15:0]} * {16'h0, __vul_port_input[143:128]};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:226:11, :227:11, :276:11, :278:11, :279:11
  wire [7:0]   _GEN_8 = {5'h0, __vul_port_input[1027:1025]};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:306:11, :307:11
  wire [15:0]  _GEN_9 = {8'h0, __vul_port_input[7:0]} * {8'h0, __vul_port_input[135:128]};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:297:11, :298:11, :347:11, :349:11, :350:11
  assign __vul_port_output =
    {513'h1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC00000000000000000000000000000003FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE00000000000000000000000000000001,
     _GEN_0 ^ __vul_port_input[1024:768],
     __vul_port_input[1024:768],
     __vul_port_input[127:0] < __vul_port_input[255:128],
     __vul_port_input[127:0] >> _GEN_1,
     __vul_port_input[127:0] << _GEN_1,
     __vul_port_input[127:0] & __vul_port_input[255:128]
       ^ (__vul_port_input[383:256] | __vul_port_input[511:384]),
     __vul_port_input[127:0] - __vul_port_input[255:128],
     {1'h0, __vul_port_input[127:0]} + {1'h0, __vul_port_input[255:128]}
       + {128'h0, __vul_port_input[1033]},
     __vul_port_input[127:0] + __vul_port_input[255:128],
     _GEN + __vul_port_input[767:512],
     _GEN_0,
     _GEN[127:0],
     _GEN,
     __vul_port_input[63:0] < __vul_port_input[191:128],
     __vul_port_input[63:0] >> _GEN_2,
     __vul_port_input[63:0] << _GEN_2,
     __vul_port_input[63:0] & __vul_port_input[191:128]
       ^ (__vul_port_input[319:256] | __vul_port_input[447:384]),
     __vul_port_input[63:0] - __vul_port_input[191:128],
     {1'h0, __vul_port_input[63:0]} + {1'h0, __vul_port_input[191:128]}
       + {64'h0, __vul_port_input[1033]},
     __vul_port_input[63:0] + __vul_port_input[191:128],
     _GEN_3 + __vul_port_input[639:512],
     {1'h0, _GEN_3}
       + {1'h0, {64'h0, __vul_port_input[319:256]} * {64'h0, __vul_port_input[447:384]}},
     _GEN_3[63:0],
     _GEN_3,
     __vul_port_input[31:0] < __vul_port_input[159:128],
     __vul_port_input[31:0] >> _GEN_4,
     __vul_port_input[31:0] << _GEN_4,
     __vul_port_input[31:0] & __vul_port_input[159:128]
       ^ (__vul_port_input[287:256] | __vul_port_input[415:384]),
     __vul_port_input[31:0] - __vul_port_input[159:128],
     {1'h0, __vul_port_input[31:0]} + {1'h0, __vul_port_input[159:128]}
       + {32'h0, __vul_port_input[1033]},
     __vul_port_input[31:0] + __vul_port_input[159:128],
     _GEN_5 + __vul_port_input[575:512],
     {1'h0, _GEN_5}
       + {1'h0, {32'h0, __vul_port_input[287:256]} * {32'h0, __vul_port_input[415:384]}},
     _GEN_5[31:0],
     _GEN_5,
     __vul_port_input[15:0] < __vul_port_input[143:128],
     __vul_port_input[15:0] >> _GEN_6,
     __vul_port_input[15:0] << _GEN_6,
     __vul_port_input[15:0] & __vul_port_input[143:128]
       ^ (__vul_port_input[271:256] | __vul_port_input[399:384]),
     __vul_port_input[15:0] - __vul_port_input[143:128],
     {1'h0, __vul_port_input[15:0]} + {1'h0, __vul_port_input[143:128]}
       + {16'h0, __vul_port_input[1033]},
     __vul_port_input[15:0] + __vul_port_input[143:128],
     _GEN_7 + __vul_port_input[543:512],
     {1'h0, _GEN_7}
       + {1'h0, {16'h0, __vul_port_input[271:256]} * {16'h0, __vul_port_input[399:384]}},
     _GEN_7[15:0],
     _GEN_7,
     __vul_port_input[7:0] < __vul_port_input[135:128],
     __vul_port_input[7:0] >> _GEN_8,
     __vul_port_input[7:0] << _GEN_8,
     __vul_port_input[7:0] & __vul_port_input[135:128]
       ^ (__vul_port_input[263:256] | __vul_port_input[391:384]),
     __vul_port_input[7:0] - __vul_port_input[135:128],
     {1'h0, __vul_port_input[7:0]} + {1'h0, __vul_port_input[135:128]}
       + {8'h0, __vul_port_input[1033]},
     __vul_port_input[7:0] + __vul_port_input[135:128],
     _GEN_9 + __vul_port_input[527:512],
     {1'h0, _GEN_9}
       + {1'h0, {8'h0, __vul_port_input[263:256]} * {8'h0, __vul_port_input[391:384]}},
     _GEN_9[7:0],
     _GEN_9};	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:4:9, :5:9, :8:9, :11:9, :14:10, :17:10, :23:10, :24:10, :25:10, :28:10, :38:10, :39:10, :53:10, :59:10, :60:10, :61:10, :63:10, :66:10, :68:10, :69:10, :71:10, :72:10, :73:10, :75:10, :77:10, :78:10, :81:10, :84:10, :85:10, :86:10, :95:10, :96:10, :110:11, :116:11, :117:11, :118:11, :119:11, :120:11, :122:11, :125:11, :127:11, :129:11, :130:11, :131:11, :133:11, :139:11, :140:11, :141:11, :144:11, :146:11, :148:11, :149:11, :151:11, :152:11, :154:11, :157:11, :158:11, :159:11, :166:11, :167:11, :179:11, :185:11, :186:11, :187:11, :188:11, :189:11, :191:11, :194:11, :196:11, :198:11, :199:11, :200:11, :202:11, :208:11, :209:11, :210:11, :213:11, :215:11, :217:11, :218:11, :220:11, :221:11, :223:11, :226:11, :227:11, :228:11, :236:11, :237:11, :250:11, :256:11, :257:11, :258:11, :259:11, :260:11, :262:11, :265:11, :267:11, :269:11, :270:11, :271:11, :273:11, :279:11, :280:11, :281:11, :284:11, :286:11, :288:11, :289:11, :291:11, :292:11, :294:11, :297:11, :298:11, :299:11, :307:11, :308:11, :321:11, :327:11, :328:11, :329:11, :330:11, :331:11, :333:11, :336:11, :338:11, :340:11, :341:11, :342:11, :344:11, :350:11, :351:11, :352:11, :355:11, :357:11, :359:11, :360:11, :362:11, :363:11, :365:11, :367:11, :368:3
  assign __vul_port_ov = __vul_port_iv;	// /tmp/rtlzz-circt-163-1845710876600551/input.mlir:368:3
end

  logic [4265:0] rdata_output__;
  assign rdata_output__ = __vul_pipeline_q_output;
  logic rdata_ov__;
  assign rdata_ov__ = __vul_pipeline_q_ov;


  wire [255:0] _GEN =
    {128'h0, combine_value__[127:0]} * {128'h0, combine_value__[255:128]};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:147:11, :149:11, :150:11, :152:11, :153:11
  wire [256:0] _GEN_0 =
    {1'h0, _GEN}
    + {1'h0, {128'h0, combine_value__[383:256]} * {128'h0, combine_value__[511:384]}};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:153:11, :155:11, :156:11, :158:11, :159:11, :161:11, :162:11, :164:11, :165:11
  wire [127:0] _GEN_1 = {121'h0, combine_value__[1031:1025]};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:178:11, :180:11
  wire [63:0]  _GEN_2 = {58'h0, combine_value__[1030:1025]};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:235:11, :237:11
  wire [127:0] _GEN_3 =
    {64'h0, combine_value__[63:0]} * {64'h0, combine_value__[191:128]};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:226:11, :227:11, :278:11, :280:11, :281:11
  wire [31:0]  _GEN_4 = {27'h0, combine_value__[1029:1025]};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:308:11
  wire [63:0]  _GEN_5 =
    {32'h0, combine_value__[31:0]} * {32'h0, combine_value__[159:128]};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:299:11, :300:11, :347:11, :349:11, :350:11
  wire [15:0]  _GEN_6 = {12'h0, combine_value__[1028:1025]};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:377:11, :378:11
  wire [31:0]  _GEN_7 =
    {16'h0, combine_value__[15:0]} * {16'h0, combine_value__[143:128]};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:368:11, :369:11, :418:11, :420:11, :421:11
  wire [7:0]   _GEN_8 = {5'h0, combine_value__[1027:1025]};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:448:11, :449:11
  wire [15:0]  _GEN_9 = {8'h0, combine_value__[7:0]} * {8'h0, combine_value__[135:128]};	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:439:11, :440:11, :489:11, :491:11, :492:11
  assign valid__query__ = rdata_ov__;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:533:3
  assign result__query__ = rdata_output__;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:533:3
  assign echo257_result__ = echo257__vld__ ? echo257_value__ : 257'h0;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:119:11, :123:11, :533:3
  assign echo256_result__ = echo256__vld__ ? echo256_value__ : 256'h0;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:124:11, :128:11, :533:3
  assign echo193_result__ = echo193__vld__ ? echo193_value__ : 193'h0;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:129:11, :133:11, :533:3
  assign echo128_result__ = echo128__vld__ ? echo128_value__ : 128'h0;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:138:11, :533:3
  assign echo129_result__ = echo129__vld__ ? echo129_value__ : 129'h0;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:139:11, :143:11, :533:3
  assign combine_result__ =
    combine__vld__
      ? {513'h1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC00000000000000000000000000000003FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE00000000000000000000000000000001,
         _GEN_0 ^ combine_value__[1024:768],
         combine_value__[1024:768],
         combine_value__[127:0] < combine_value__[255:128],
         combine_value__[127:0] >> _GEN_1,
         combine_value__[127:0] << _GEN_1,
         combine_value__[127:0] & combine_value__[255:128]
           ^ (combine_value__[383:256] | combine_value__[511:384]),
         combine_value__[127:0] - combine_value__[255:128],
         {1'h0, combine_value__[127:0]} + {1'h0, combine_value__[255:128]}
           + {128'h0, combine_value__[1033]},
         combine_value__[127:0] + combine_value__[255:128],
         _GEN + combine_value__[767:512],
         _GEN_0,
         _GEN[127:0],
         _GEN,
         combine_value__[63:0] < combine_value__[191:128],
         combine_value__[63:0] >> _GEN_2,
         combine_value__[63:0] << _GEN_2,
         combine_value__[63:0] & combine_value__[191:128]
           ^ (combine_value__[319:256] | combine_value__[447:384]),
         combine_value__[63:0] - combine_value__[191:128],
         {1'h0, combine_value__[63:0]} + {1'h0, combine_value__[191:128]}
           + {64'h0, combine_value__[1033]},
         combine_value__[63:0] + combine_value__[191:128],
         _GEN_3 + combine_value__[639:512],
         {1'h0, _GEN_3}
           + {1'h0,
              {64'h0, combine_value__[319:256]} * {64'h0, combine_value__[447:384]}},
         _GEN_3[63:0],
         _GEN_3,
         combine_value__[31:0] < combine_value__[159:128],
         combine_value__[31:0] >> _GEN_4,
         combine_value__[31:0] << _GEN_4,
         combine_value__[31:0] & combine_value__[159:128]
           ^ (combine_value__[287:256] | combine_value__[415:384]),
         combine_value__[31:0] - combine_value__[159:128],
         {1'h0, combine_value__[31:0]} + {1'h0, combine_value__[159:128]}
           + {32'h0, combine_value__[1033]},
         combine_value__[31:0] + combine_value__[159:128],
         _GEN_5 + combine_value__[575:512],
         {1'h0, _GEN_5}
           + {1'h0,
              {32'h0, combine_value__[287:256]} * {32'h0, combine_value__[415:384]}},
         _GEN_5[31:0],
         _GEN_5,
         combine_value__[15:0] < combine_value__[143:128],
         combine_value__[15:0] >> _GEN_6,
         combine_value__[15:0] << _GEN_6,
         combine_value__[15:0] & combine_value__[143:128]
           ^ (combine_value__[271:256] | combine_value__[399:384]),
         combine_value__[15:0] - combine_value__[143:128],
         {1'h0, combine_value__[15:0]} + {1'h0, combine_value__[143:128]}
           + {16'h0, combine_value__[1033]},
         combine_value__[15:0] + combine_value__[143:128],
         _GEN_7 + combine_value__[543:512],
         {1'h0, _GEN_7}
           + {1'h0,
              {16'h0, combine_value__[271:256]} * {16'h0, combine_value__[399:384]}},
         _GEN_7[15:0],
         _GEN_7,
         combine_value__[7:0] < combine_value__[135:128],
         combine_value__[7:0] >> _GEN_8,
         combine_value__[7:0] << _GEN_8,
         combine_value__[7:0] & combine_value__[135:128]
           ^ (combine_value__[263:256] | combine_value__[391:384]),
         combine_value__[7:0] - combine_value__[135:128],
         {1'h0, combine_value__[7:0]} + {1'h0, combine_value__[135:128]}
           + {8'h0, combine_value__[1033]},
         combine_value__[7:0] + combine_value__[135:128],
         _GEN_9 + combine_value__[527:512],
         {1'h0, _GEN_9}
           + {1'h0, {8'h0, combine_value__[263:256]} * {8'h0, combine_value__[391:384]}},
         _GEN_9[7:0],
         _GEN_9}
      : 4266'h0;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:146:11, :147:11, :150:11, :153:11, :156:11, :159:11, :165:11, :166:11, :167:11, :170:11, :180:11, :181:11, :195:11, :201:11, :202:11, :203:11, :205:11, :208:11, :210:11, :211:11, :213:11, :214:11, :215:11, :217:11, :219:11, :220:11, :223:11, :226:11, :227:11, :228:11, :237:11, :238:11, :252:11, :258:11, :259:11, :260:11, :261:11, :262:11, :264:11, :267:11, :269:11, :271:11, :272:11, :273:11, :275:11, :281:11, :282:11, :283:11, :286:11, :288:11, :290:11, :291:11, :293:11, :294:11, :296:11, :299:11, :300:11, :301:11, :308:11, :309:11, :321:11, :327:11, :328:11, :329:11, :330:11, :331:11, :333:11, :336:11, :338:11, :340:11, :341:11, :342:11, :344:11, :350:11, :351:11, :352:11, :355:11, :357:11, :359:11, :360:11, :362:11, :363:11, :365:11, :368:11, :369:11, :370:11, :378:11, :379:11, :392:11, :398:11, :399:11, :400:11, :401:11, :402:11, :404:11, :407:11, :409:11, :411:11, :412:11, :413:11, :415:11, :421:11, :422:11, :423:11, :426:11, :428:11, :430:11, :431:11, :433:11, :434:11, :436:11, :439:11, :440:11, :441:11, :449:11, :450:11, :463:11, :469:11, :470:11, :471:11, :472:11, :473:11, :475:11, :478:11, :480:11, :482:11, :483:11, :484:11, :486:11, :492:11, :493:11, :494:11, :497:11, :499:11, :501:11, :502:11, :504:11, :505:11, :507:11, :509:11, :510:11, :514:11, :533:3
  assign wen_input__ = push__vld__;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:533:3
  assign wdata_input__ = push_value__;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:533:3
  assign resetvalue_input__ =
    1034'h2FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:530:11, :533:3
  assign wen_iv__ = push__vld__;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:533:3
  assign wdata_iv__ = push__vld__ & push_valid__;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:531:11, :533:3
  assign resetvalue_iv__ = 1'h0;	// /tmp/rtlzz-circt-163-1845712209238975/input.mlir:533:3
endmodule

