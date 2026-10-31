module top(	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:1
  input  [31:0] a,	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:19
                b,	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:32
                c,	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:45
  input         iv,	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:58
                rstn,	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:71
                clk,	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:86
  output [36:0] y,	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:101
                z,	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:114
  output [63:0] m,	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:127
  output        ov	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:140
);

  reg         rtlzz_valid_s1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1951:21
  wire        _GEN = ~rstn;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9
  wire        _GEN_0 = |(a[30:0]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:7:9, :9:9
  wire        _GEN_1 = &(a[30:23]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:23:10, :25:10
  wire        _GEN_2 = |(a[22:0]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:26:10, :28:10
  wire        _GEN_3 = _GEN_1 & _GEN_2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:25:10, :28:10, :29:10
  wire        _GEN_4 = |(a[30:23]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:23:10, :60:10
  wire [23:0] _GEN_5 = _GEN_4 ? {1'h1, a[22:0]} : {a[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:26:10, :60:10, :61:10, :65:10, :68:10
  wire [23:0] _GEN_6 = _GEN_5[23] ? _GEN_5 : {_GEN_5[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:68:10, :72:10, :74:10, :75:10
  wire [23:0] _GEN_7 = _GEN_6[23] ? _GEN_6 : {_GEN_6[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:75:10, :79:10, :81:10, :82:10
  wire [23:0] _GEN_8 = _GEN_7[23] ? _GEN_7 : {_GEN_7[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:82:10, :86:10, :88:10, :89:10
  wire [23:0] _GEN_9 = _GEN_8[23] ? _GEN_8 : {_GEN_8[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:89:10, :93:10, :95:10, :96:10
  wire [23:0] _GEN_10 = _GEN_9[23] ? _GEN_9 : {_GEN_9[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:96:10, :100:10, :102:11, :103:11
  wire [23:0] _GEN_11 = _GEN_10[23] ? _GEN_10 : {_GEN_10[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:103:11, :107:11, :109:11, :110:11
  wire [23:0] _GEN_12 = _GEN_11[23] ? _GEN_11 : {_GEN_11[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:110:11, :114:11, :116:11, :117:11
  wire [23:0] _GEN_13 = _GEN_12[23] ? _GEN_12 : {_GEN_12[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:117:11, :121:11, :123:11, :124:11
  wire [23:0] _GEN_14 = _GEN_13[23] ? _GEN_13 : {_GEN_13[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:124:11, :128:11, :130:11, :131:11
  wire [23:0] _GEN_15 = _GEN_14[23] ? _GEN_14 : {_GEN_14[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:131:11, :135:11, :137:11, :138:11
  wire [23:0] _GEN_16 = _GEN_15[23] ? _GEN_15 : {_GEN_15[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:138:11, :142:11, :144:11, :145:11
  wire [23:0] _GEN_17 = _GEN_16[23] ? _GEN_16 : {_GEN_16[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:145:11, :149:11, :151:11, :152:11
  wire [23:0] _GEN_18 = _GEN_17[23] ? _GEN_17 : {_GEN_17[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:152:11, :156:11, :158:11, :159:11
  wire [23:0] _GEN_19 = _GEN_18[23] ? _GEN_18 : {_GEN_18[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:159:11, :163:11, :165:11, :166:11
  wire [23:0] _GEN_20 = _GEN_19[23] ? _GEN_19 : {_GEN_19[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:166:11, :170:11, :172:11, :173:11
  wire [23:0] _GEN_21 = _GEN_20[23] ? _GEN_20 : {_GEN_20[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:173:11, :177:11, :179:11, :180:11
  wire [23:0] _GEN_22 = _GEN_21[23] ? _GEN_21 : {_GEN_21[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:180:11, :184:11, :186:11, :187:11
  wire [23:0] _GEN_23 = _GEN_22[23] ? _GEN_22 : {_GEN_22[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:187:11, :191:11, :193:11, :194:11
  wire [23:0] _GEN_24 = _GEN_23[23] ? _GEN_23 : {_GEN_23[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:194:11, :198:11, :200:11, :201:11
  wire [23:0] _GEN_25 = _GEN_24[23] ? _GEN_24 : {_GEN_24[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:201:11, :205:11, :207:11, :208:11
  wire [23:0] _GEN_26 = _GEN_25[23] ? _GEN_25 : {_GEN_25[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:208:11, :212:11, :214:11, :215:11
  wire [47:0] _GEN_27 = {24'h0, _GEN_26[23] ? _GEN_26 : {_GEN_26[22:0], 1'h0}};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:215:11, :219:11, :221:11, :222:11, :224:11
  wire [1:0]  _GEN_28 = {1'h0, ~_GEN_4};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:60:10, :67:10, :442:11
  wire [1:0]  _GEN_29 = _GEN_5[23] ? _GEN_28 : _GEN_28 + 2'h1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:68:10, :74:10, :442:11, :448:11, :449:11
  wire [1:0]  _GEN_30 = _GEN_6[23] ? _GEN_29 : _GEN_29 + 2'h1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:75:10, :81:10, :449:11, :457:11, :458:11
  wire [3:0]  _GEN_31 = _GEN_7[23] ? {2'h0, _GEN_30} : {1'h0, {1'h0, _GEN_30} + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:82:10, :88:10, :458:11, :460:11, :466:11, :467:11
  wire [4:0]  _GEN_32 = _GEN_8[23] ? {1'h0, _GEN_31} : {2'h0, _GEN_31[2:0] + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:89:10, :95:10, :467:11, :469:11, :475:11, :476:11
  wire [5:0]  _GEN_33 = _GEN_9[23] ? {1'h0, _GEN_32} : {3'h0, _GEN_32[2:0] + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:96:10, :102:11, :476:11, :478:11, :484:11, :485:11
  wire [6:0]  _GEN_34 = _GEN_10[23] ? {1'h0, _GEN_33} : {4'h0, _GEN_33[2:0] + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:103:11, :109:11, :485:11, :487:11, :493:11, :494:11
  wire [7:0]  _GEN_35 = _GEN_11[23] ? {1'h0, _GEN_34} : {4'h0, _GEN_34[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:110:11, :116:11, :494:11, :496:11, :502:11, :503:11
  wire [7:0]  _GEN_36 = _GEN_12[23] ? _GEN_35 : {4'h0, _GEN_35[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:117:11, :123:11, :503:11, :505:11, :506:11
  wire [7:0]  _GEN_37 = _GEN_13[23] ? _GEN_36 : {4'h0, _GEN_36[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:124:11, :130:11, :506:11, :508:11, :509:11
  wire [7:0]  _GEN_38 = _GEN_14[23] ? _GEN_37 : {4'h0, _GEN_37[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:131:11, :137:11, :509:11, :511:11, :512:11
  wire [7:0]  _GEN_39 = _GEN_15[23] ? _GEN_38 : {4'h0, _GEN_38[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:138:11, :144:11, :512:11, :514:11, :515:11
  wire [7:0]  _GEN_40 = _GEN_16[23] ? _GEN_39 : {4'h0, _GEN_39[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:145:11, :151:11, :515:11, :517:11, :518:11
  wire [7:0]  _GEN_41 = _GEN_17[23] ? _GEN_40 : {4'h0, _GEN_40[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:152:11, :158:11, :518:11, :520:11, :521:11
  wire [7:0]  _GEN_42 = _GEN_18[23] ? _GEN_41 : {4'h0, _GEN_41[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:159:11, :165:11, :521:11, :523:11, :524:11
  wire [7:0]  _GEN_43 = _GEN_19[23] ? _GEN_42 : {3'h0, _GEN_42[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:166:11, :172:11, :524:11, :526:11, :527:11
  wire [7:0]  _GEN_44 = _GEN_20[23] ? _GEN_43 : {3'h0, _GEN_43[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:173:11, :179:11, :527:11, :529:11, :530:11
  wire [7:0]  _GEN_45 = _GEN_21[23] ? _GEN_44 : {3'h0, _GEN_44[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:180:11, :186:11, :530:11, :532:11, :533:11
  wire [7:0]  _GEN_46 = _GEN_22[23] ? _GEN_45 : {3'h0, _GEN_45[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:187:11, :193:11, :533:11, :535:11, :536:11
  wire [7:0]  _GEN_47 = _GEN_23[23] ? _GEN_46 : {3'h0, _GEN_46[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:194:11, :200:11, :536:11, :538:11, :539:11
  wire [7:0]  _GEN_48 = _GEN_24[23] ? _GEN_47 : {3'h0, _GEN_47[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:201:11, :207:11, :539:11, :541:11, :542:11
  wire [7:0]  _GEN_49 = _GEN_25[23] ? _GEN_48 : {3'h0, _GEN_48[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:208:11, :214:11, :542:11, :544:11, :545:11
  wire [11:0] _GEN_50 =
    {2'h0,
     {2'h0, _GEN_4 ? a[30:23] : 8'h1} - 10'h200
       - {2'h0, _GEN_26[23] ? _GEN_49 : {3'h0, _GEN_49[4:0] + 5'h1}}};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:23:10, :60:10, :215:11, :221:11, :425:11, :433:11, :545:11, :547:11, :548:11, :553:11
  wire        _GEN_51 = a[23] & a[24] & a[25] & a[26] & a[27] & a[28] & a[29] & a[30];	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:791:11, :792:11, :793:11, :794:11, :795:11, :796:11, :797:11, :798:11, :799:11, :800:11, :801:11, :802:11, :803:11, :804:11, :805:11
  wire        _GEN_52 = _GEN_51 & _GEN_2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:28:10, :793:11, :796:11, :797:11, :800:11, :803:11, :804:11, :805:11, :806:11
  wire        _GEN_53 = _GEN_52 & ~(a[22]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:806:11, :808:11, :810:11, :811:11
  reg  [36:0] rtlzz_pipe_8_s1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:970:22
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:970:22
    if (_GEN)	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :970:22
      rtlzz_pipe_8_s1 <= 37'h107FC00000;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:970:22
    else begin	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :970:22
      automatic logic        _GEN_54 = _GEN_0 & (|(b[30:0]));	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:9:9, :13:10, :15:10, :19:10
      automatic logic        _GEN_55 = &(b[30:23]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:33:10, :35:10
      automatic logic        _GEN_56 = |(b[22:0]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:36:10, :38:10
      automatic logic        _GEN_57 = |(b[30:23]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:33:10, :233:11
      automatic logic [23:0] _GEN_58 = _GEN_57 ? {1'h1, b[22:0]} : {b[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:36:10, :233:11, :234:11, :238:11, :241:11
      automatic logic [23:0] _GEN_59 = _GEN_58[23] ? _GEN_58 : {_GEN_58[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:241:11, :245:11, :247:11, :248:11
      automatic logic [23:0] _GEN_60 = _GEN_59[23] ? _GEN_59 : {_GEN_59[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:248:11, :252:11, :254:11, :255:11
      automatic logic [23:0] _GEN_61 = _GEN_60[23] ? _GEN_60 : {_GEN_60[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:255:11, :259:11, :261:11, :262:11
      automatic logic [23:0] _GEN_62 = _GEN_61[23] ? _GEN_61 : {_GEN_61[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:262:11, :266:11, :268:11, :269:11
      automatic logic [23:0] _GEN_63 = _GEN_62[23] ? _GEN_62 : {_GEN_62[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:269:11, :273:11, :275:11, :276:11
      automatic logic [23:0] _GEN_64 = _GEN_63[23] ? _GEN_63 : {_GEN_63[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:276:11, :280:11, :282:11, :283:11
      automatic logic [23:0] _GEN_65 = _GEN_64[23] ? _GEN_64 : {_GEN_64[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:283:11, :287:11, :289:11, :290:11
      automatic logic [23:0] _GEN_66 = _GEN_65[23] ? _GEN_65 : {_GEN_65[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:290:11, :294:11, :296:11, :297:11
      automatic logic [23:0] _GEN_67 = _GEN_66[23] ? _GEN_66 : {_GEN_66[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:297:11, :301:11, :303:11, :304:11
      automatic logic [23:0] _GEN_68 = _GEN_67[23] ? _GEN_67 : {_GEN_67[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:304:11, :308:11, :310:11, :311:11
      automatic logic [23:0] _GEN_69 = _GEN_68[23] ? _GEN_68 : {_GEN_68[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:311:11, :315:11, :317:11, :318:11
      automatic logic [23:0] _GEN_70 = _GEN_69[23] ? _GEN_69 : {_GEN_69[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:318:11, :322:11, :324:11, :325:11
      automatic logic [23:0] _GEN_71 = _GEN_70[23] ? _GEN_70 : {_GEN_70[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:325:11, :329:11, :331:11, :332:11
      automatic logic [23:0] _GEN_72 = _GEN_71[23] ? _GEN_71 : {_GEN_71[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:332:11, :336:11, :338:11, :339:11
      automatic logic [23:0] _GEN_73 = _GEN_72[23] ? _GEN_72 : {_GEN_72[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:339:11, :343:11, :345:11, :346:11
      automatic logic [23:0] _GEN_74 = _GEN_73[23] ? _GEN_73 : {_GEN_73[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:346:11, :350:11, :352:11, :353:11
      automatic logic [23:0] _GEN_75 = _GEN_74[23] ? _GEN_74 : {_GEN_74[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:353:11, :357:11, :359:11, :360:11
      automatic logic [23:0] _GEN_76 = _GEN_75[23] ? _GEN_75 : {_GEN_75[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:360:11, :364:11, :366:11, :367:11
      automatic logic [23:0] _GEN_77 = _GEN_76[23] ? _GEN_76 : {_GEN_76[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:367:11, :371:11, :373:11, :374:11
      automatic logic [23:0] _GEN_78 = _GEN_77[23] ? _GEN_77 : {_GEN_77[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:374:11, :378:11, :380:11, :381:11
      automatic logic [23:0] _GEN_79 = _GEN_78[23] ? _GEN_78 : {_GEN_78[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:381:11, :385:11, :387:11, :388:11
      automatic logic [47:0] _GEN_80 =
        _GEN_27 * {24'h0, _GEN_79[23] ? _GEN_79 : {_GEN_79[22:0], 1'h0}};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:224:11, :388:11, :392:11, :394:11, :395:11, :397:11, :398:11
      automatic logic [30:0] _GEN_81 = {30'h0, |(_GEN_80[16:0])} | _GEN_80[47:17];	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:398:11, :399:11, :402:11, :404:11, :405:11
      automatic logic [31:0] _GEN_82 = {1'h0, _GEN_81};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:405:11, :407:11
      automatic logic        _GEN_83 = _GEN_82 < 32'h40000000;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:407:11, :415:11
      automatic logic [31:0] _GEN_84 = _GEN_83 ? {_GEN_81, 1'h0} : _GEN_82;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:405:11, :407:11, :413:11, :415:11, :416:11
      automatic logic [31:0] _GEN_85 = _GEN_84 + 32'h40;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:416:11, :418:11
      automatic logic [1:0]  _GEN_86 = {1'h0, ~_GEN_57};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:233:11, :240:11, :572:11
      automatic logic [1:0]  _GEN_87 = _GEN_58[23] ? _GEN_86 : _GEN_86 + 2'h1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:241:11, :247:11, :572:11, :578:11, :579:11
      automatic logic [1:0]  _GEN_88 = _GEN_59[23] ? _GEN_87 : _GEN_87 + 2'h1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:248:11, :254:11, :579:11, :587:11, :588:11
      automatic logic [3:0]  _GEN_89 =
        _GEN_60[23] ? {2'h0, _GEN_88} : {1'h0, {1'h0, _GEN_88} + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:255:11, :261:11, :588:11, :590:11, :596:11, :597:11
      automatic logic [4:0]  _GEN_90 =
        _GEN_61[23] ? {1'h0, _GEN_89} : {2'h0, _GEN_89[2:0] + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:262:11, :268:11, :597:11, :599:11, :605:11, :606:11
      automatic logic [5:0]  _GEN_91 =
        _GEN_62[23] ? {1'h0, _GEN_90} : {3'h0, _GEN_90[2:0] + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:269:11, :275:11, :606:11, :608:11, :614:11, :615:11
      automatic logic [6:0]  _GEN_92 =
        _GEN_63[23] ? {1'h0, _GEN_91} : {4'h0, _GEN_91[2:0] + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:276:11, :282:11, :615:11, :617:11, :623:11, :624:11
      automatic logic [7:0]  _GEN_93 =
        _GEN_64[23] ? {1'h0, _GEN_92} : {4'h0, _GEN_92[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:283:11, :289:11, :624:11, :626:11, :632:11, :633:11
      automatic logic [7:0]  _GEN_94 =
        _GEN_65[23] ? _GEN_93 : {4'h0, _GEN_93[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:290:11, :296:11, :633:11, :635:11, :636:11
      automatic logic [7:0]  _GEN_95 =
        _GEN_66[23] ? _GEN_94 : {4'h0, _GEN_94[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:297:11, :303:11, :636:11, :638:11, :639:11
      automatic logic [7:0]  _GEN_96 =
        _GEN_67[23] ? _GEN_95 : {4'h0, _GEN_95[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:304:11, :310:11, :639:11, :641:11, :642:11
      automatic logic [7:0]  _GEN_97 =
        _GEN_68[23] ? _GEN_96 : {4'h0, _GEN_96[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:311:11, :317:11, :642:11, :644:11, :645:11
      automatic logic [7:0]  _GEN_98 =
        _GEN_69[23] ? _GEN_97 : {4'h0, _GEN_97[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:318:11, :324:11, :645:11, :647:11, :648:11
      automatic logic [7:0]  _GEN_99 =
        _GEN_70[23] ? _GEN_98 : {4'h0, _GEN_98[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:325:11, :331:11, :648:11, :650:11, :651:11
      automatic logic [7:0]  _GEN_100 =
        _GEN_71[23] ? _GEN_99 : {4'h0, _GEN_99[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:332:11, :338:11, :651:11, :653:11, :654:11
      automatic logic [7:0]  _GEN_101 =
        _GEN_72[23] ? _GEN_100 : {3'h0, _GEN_100[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:339:11, :345:11, :654:11, :656:11, :657:11
      automatic logic [7:0]  _GEN_102 =
        _GEN_73[23] ? _GEN_101 : {3'h0, _GEN_101[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:346:11, :352:11, :657:11, :659:11, :660:11
      automatic logic [7:0]  _GEN_103 =
        _GEN_74[23] ? _GEN_102 : {3'h0, _GEN_102[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:353:11, :359:11, :660:11, :662:11, :663:11
      automatic logic [7:0]  _GEN_104 =
        _GEN_75[23] ? _GEN_103 : {3'h0, _GEN_103[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:360:11, :366:11, :663:11, :665:11, :666:11
      automatic logic [7:0]  _GEN_105 =
        _GEN_76[23] ? _GEN_104 : {3'h0, _GEN_104[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:367:11, :373:11, :666:11, :668:11, :669:11
      automatic logic [7:0]  _GEN_106 =
        _GEN_77[23] ? _GEN_105 : {3'h0, _GEN_105[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:374:11, :380:11, :669:11, :671:11, :672:11
      automatic logic [7:0]  _GEN_107 =
        _GEN_78[23] ? _GEN_106 : {3'h0, _GEN_106[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:381:11, :387:11, :672:11, :674:11, :675:11
      automatic logic [11:0] _GEN_108 =
        _GEN_50
        + {2'h0,
           {2'h0, _GEN_57 ? b[30:23] : 8'h1} - 10'h200
             - {2'h0, _GEN_79[23] ? _GEN_107 : {3'h0, _GEN_107[4:0] + 5'h1}}} - 12'h27F;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:33:10, :233:11, :388:11, :394:11, :553:11, :555:11, :563:11, :675:11, :677:11, :678:11, :683:11, :684:11, :686:11
      automatic logic [11:0] _GEN_109 = _GEN_83 ? _GEN_108 - 12'h1 : _GEN_108;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:415:11, :684:11, :686:11, :688:11, :689:11
      automatic logic [11:0] _GEN_110 = 12'h200 - _GEN_109;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:689:11, :700:11
      automatic logic [31:0] _GEN_111 = {20'h0, _GEN_110};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:700:11, :702:11
      automatic logic        _GEN_112 = |(_GEN_110[11:5]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:700:11, :705:11
      automatic logic        _GEN_113 = _GEN_109 < 12'h200;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:689:11, :724:11
      automatic logic [31:0] _GEN_114 =
        _GEN_113 & _GEN_112
          ? {31'h0, |_GEN_84}
          : {31'h0,
             (|(_GEN_84 & (_GEN_112 ? 32'h0 : 32'h1 << _GEN_111) - 32'h1)) & _GEN_113
               & ~_GEN_112} | (_GEN_112 ? 32'h0 : _GEN_84 >> _GEN_111);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:416:11, :702:11, :703:11, :705:11, :707:11, :713:11, :717:11, :719:11, :720:11, :722:11, :724:11, :729:11, :730:11, :731:11, :732:11, :738:11, :741:11, :742:11, :743:11
      automatic logic [31:0] _GEN_115 = _GEN_113 ? _GEN_114 : _GEN_84;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:416:11, :724:11, :743:11, :752:11
      automatic logic        _GEN_116 = _GEN_109 < 12'h2FE;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:689:11, :762:11
      automatic logic        _GEN_117 = _GEN_116 & ~(_GEN_85[31] & _GEN_109 == 12'h2FD);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:418:11, :420:11, :689:11, :762:11, :767:11, :768:11, :771:11, :772:11
      automatic logic        _GEN_118 =
        b[23] & b[24] & b[25] & b[26] & b[27] & b[28] & b[29] & b[30];	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:815:11, :816:11, :817:11, :818:11, :819:11, :820:11, :821:11, :822:11, :823:11, :824:11, :825:11, :826:11, :827:11, :828:11, :829:11
      automatic logic        _GEN_119 = _GEN_118 & _GEN_56;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:38:10, :817:11, :820:11, :821:11, :824:11, :827:11, :828:11, :829:11, :830:11
      automatic logic        _GEN_120 = ~_GEN_53 & ~(_GEN_119 & ~(b[22]));	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:811:11, :814:11, :830:11, :832:11, :834:11, :835:11, :838:11, :839:11
      automatic logic        _GEN_121 = ~_GEN_52 & ~_GEN_119;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:806:11, :830:11, :842:11, :845:11, :846:11
      automatic logic        _GEN_122 = a[31] ^ b[31];	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:{19,32}, :857:11
      automatic logic [31:0] _GEN_123 = {_GEN_122, 31'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:857:11, :866:11
      automatic logic [31:0] _GEN_124 = {_GEN_122, 31'h7F800000};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:857:11, :866:11
      automatic logic        _GEN_125 = ~_GEN_51 & ~_GEN_118;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:793:11, :796:11, :797:11, :800:11, :803:11, :804:11, :805:11, :817:11, :820:11, :821:11, :824:11, :827:11, :828:11, :829:11, :872:11, :875:11, :876:11
      automatic logic [31:0] _GEN_126 = _GEN_115 + 32'h40;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:752:11, :896:11
      automatic logic [24:0] _GEN_127 =
        _GEN_115[6:0] == 7'h40 ? {_GEN_126[31:8], 1'h0} : _GEN_126[31:7];	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:752:11, :753:11, :896:11, :897:11, :899:11, :901:11, :902:11
      automatic logic        _GEN_128 = _GEN_54 & _GEN_125;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:19:10, :876:11, :916:11
      rtlzz_pipe_8_s1 <=
        iv
          ? {_GEN_120
               ? (_GEN_120 & ~_GEN_121
                    ? 5'h0
                    : _GEN_1 | _GEN_55
                        ? {~_GEN_54 & ~_GEN_3 & ~(_GEN_55 & _GEN_56), 4'h0}
                        : {2'h0,
                           _GEN_54
                             ? (_GEN_117
                                  ? {1'h0,
                                     {1'h0, |(_GEN_115[6:0])}
                                       | (_GEN_113
                                            ? {~(_GEN_85[31] & _GEN_109 > 12'h1FE)
                                                 & (|(_GEN_114[6:0])),
                                               1'h0}
                                            : 2'h0)}
                                  : 3'h5)
                             : 3'h0})
               : 5'h10,
             _GEN_121
               ? (~_GEN_54 & _GEN_125
                    ? _GEN_123
                    : _GEN_128
                      & ~(_GEN_116
                          & ~(_GEN_109[6] & _GEN_109[7] & _GEN_109[9] & ~(_GEN_109[1])
                              & ~(_GEN_109[8]) & _GEN_109[2] & _GEN_109[3] & _GEN_109[4]
                              & _GEN_109[5] & ~(_GEN_109[10]) & ~(_GEN_109[11])
                              & _GEN_85[31] & _GEN_109[0]))
                        ? _GEN_124
                        : _GEN_117 & _GEN_128
                            ? _GEN_123
                              | {_GEN_127 == 25'h0 | _GEN_113 ? 9'h0 : _GEN_109[8:0],
                                 23'h0} + {7'h0, _GEN_127}
                            : _GEN_121 & ~_GEN_54 & ~_GEN_125 ? 32'h7FC00000 : _GEN_124)
               : 32'h7FC00000}
          : rtlzz_pipe_8_s1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:19:10, :22:10, :25:10, :29:10, :32:10, :35:10, :38:10, :39:10, :42:10, :43:10, :44:10, :45:10, :418:11, :420:11, :689:11, :691:11, :695:11, :698:11, :724:11, :743:11, :744:11, :746:11, :747:11, :748:11, :749:11, :752:11, :753:11, :755:11, :756:11, :758:11, :762:11, :772:11, :776:11, :779:11, :781:11, :789:11, :839:11, :846:11, :849:11, :850:11, :851:11, :856:11, :866:11, :876:11, :879:11, :880:11, :881:11, :882:11, :883:11, :902:11, :904:11, :905:11, :911:11, :913:11, :914:11, :915:11, :916:11, :917:11, :918:11, :919:11, :920:11, :921:11, :922:11, :923:11, :926:11, :927:11, :930:11, :931:11, :932:11, :933:11, :934:11, :935:11, :936:11, :937:11, :938:11, :939:11, :940:11, :941:11, :944:11, :945:11, :948:11, :949:11, :950:11, :951:11, :952:11, :953:11, :954:11, :957:11, :958:11, :961:11, :962:11, :963:11, :964:11, :965:11, :967:11, :968:11, :970:22
    end
  end // always_ff @(posedge)
  reg  [36:0] rtlzz_pipe_8_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:972:22
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:972:22
    if (_GEN)	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :972:22
      rtlzz_pipe_8_s2 <= 37'h107FC00000;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:972:22
    else	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :972:22
      rtlzz_pipe_8_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_8_s1 : rtlzz_pipe_8_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:970:22, :972:22, :1951:21
  end // always_ff @(posedge)
  reg  [36:0] rtlzz_pipe_9_s1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1938:22
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1938:22
    if (_GEN)	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1938:22
      rtlzz_pipe_9_s1 <= 37'h7F800000;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1938:22
    else begin	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1938:22
      automatic logic        _GEN_129 = _GEN_0 & (|(c[30:0]));	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:9:9, :981:11, :983:11, :987:11
      automatic logic        _GEN_130 = &(c[30:23]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1001:11, :1003:11
      automatic logic        _GEN_131 = |(c[22:0]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1004:12, :1006:12
      automatic logic        _GEN_132 = |(c[30:23]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1001:11, :1201:12
      automatic logic [23:0] _GEN_133 = _GEN_132 ? {1'h1, c[22:0]} : {c[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1004:12, :1201:12, :1202:12, :1206:12, :1209:12
      automatic logic [23:0] _GEN_134 = _GEN_133[23] ? _GEN_133 : {_GEN_133[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1209:12, :1213:12, :1215:12, :1216:12
      automatic logic [23:0] _GEN_135 = _GEN_134[23] ? _GEN_134 : {_GEN_134[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1216:12, :1220:12, :1222:12, :1223:12
      automatic logic [23:0] _GEN_136 = _GEN_135[23] ? _GEN_135 : {_GEN_135[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1223:12, :1227:12, :1229:12, :1230:12
      automatic logic [23:0] _GEN_137 = _GEN_136[23] ? _GEN_136 : {_GEN_136[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1230:12, :1234:12, :1236:12, :1237:12
      automatic logic [23:0] _GEN_138 = _GEN_137[23] ? _GEN_137 : {_GEN_137[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1237:12, :1241:12, :1243:12, :1244:12
      automatic logic [23:0] _GEN_139 = _GEN_138[23] ? _GEN_138 : {_GEN_138[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1244:12, :1248:12, :1250:12, :1251:12
      automatic logic [23:0] _GEN_140 = _GEN_139[23] ? _GEN_139 : {_GEN_139[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1251:12, :1255:12, :1257:12, :1258:12
      automatic logic [23:0] _GEN_141 = _GEN_140[23] ? _GEN_140 : {_GEN_140[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1258:12, :1262:12, :1264:12, :1265:12
      automatic logic [23:0] _GEN_142 = _GEN_141[23] ? _GEN_141 : {_GEN_141[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1265:12, :1269:12, :1271:12, :1272:12
      automatic logic [23:0] _GEN_143 = _GEN_142[23] ? _GEN_142 : {_GEN_142[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1272:12, :1276:12, :1278:12, :1279:12
      automatic logic [23:0] _GEN_144 = _GEN_143[23] ? _GEN_143 : {_GEN_143[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1279:12, :1283:12, :1285:12, :1286:12
      automatic logic [23:0] _GEN_145 = _GEN_144[23] ? _GEN_144 : {_GEN_144[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1286:12, :1290:12, :1292:12, :1293:12
      automatic logic [23:0] _GEN_146 = _GEN_145[23] ? _GEN_145 : {_GEN_145[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1293:12, :1297:12, :1299:12, :1300:12
      automatic logic [23:0] _GEN_147 = _GEN_146[23] ? _GEN_146 : {_GEN_146[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1300:12, :1304:12, :1306:12, :1307:12
      automatic logic [23:0] _GEN_148 = _GEN_147[23] ? _GEN_147 : {_GEN_147[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1307:12, :1311:12, :1313:12, :1314:12
      automatic logic [23:0] _GEN_149 = _GEN_148[23] ? _GEN_148 : {_GEN_148[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1314:12, :1318:12, :1320:12, :1321:12
      automatic logic [23:0] _GEN_150 = _GEN_149[23] ? _GEN_149 : {_GEN_149[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1321:12, :1325:12, :1327:12, :1328:12
      automatic logic [23:0] _GEN_151 = _GEN_150[23] ? _GEN_150 : {_GEN_150[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1328:12, :1332:12, :1334:12, :1335:12
      automatic logic [23:0] _GEN_152 = _GEN_151[23] ? _GEN_151 : {_GEN_151[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1335:12, :1339:12, :1341:12, :1342:12
      automatic logic [23:0] _GEN_153 = _GEN_152[23] ? _GEN_152 : {_GEN_152[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1342:12, :1346:12, :1348:12, :1349:12
      automatic logic [23:0] _GEN_154 = _GEN_153[23] ? _GEN_153 : {_GEN_153[22:0], 1'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1349:12, :1353:12, :1355:12, :1356:12
      automatic logic [47:0] _GEN_155 =
        _GEN_27 * {24'h0, _GEN_154[23] ? _GEN_154 : {_GEN_154[22:0], 1'h0}};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:224:11, :1356:12, :1360:12, :1362:12, :1363:12, :1365:12, :1366:12
      automatic logic [30:0] _GEN_156 = {30'h0, |(_GEN_155[16:0])} | _GEN_155[47:17];	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1366:12, :1367:12, :1370:12, :1372:12, :1373:12
      automatic logic [31:0] _GEN_157 = {1'h0, _GEN_156};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1373:12, :1375:12
      automatic logic        _GEN_158 = _GEN_157 < 32'h40000000;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1375:12, :1383:12
      automatic logic [31:0] _GEN_159 = _GEN_158 ? {_GEN_156, 1'h0} : _GEN_157;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1373:12, :1375:12, :1381:12, :1383:12, :1384:12
      automatic logic [31:0] _GEN_160 = _GEN_159 + 32'h40;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1384:12, :1386:12
      automatic logic [1:0]  _GEN_161 = {1'h0, ~_GEN_132};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1201:12, :1208:12, :1540:12
      automatic logic [1:0]  _GEN_162 = _GEN_133[23] ? _GEN_161 : _GEN_161 + 2'h1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1209:12, :1215:12, :1540:12, :1546:12, :1547:12
      automatic logic [1:0]  _GEN_163 = _GEN_134[23] ? _GEN_162 : _GEN_162 + 2'h1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1216:12, :1222:12, :1547:12, :1555:12, :1556:12
      automatic logic [3:0]  _GEN_164 =
        _GEN_135[23] ? {2'h0, _GEN_163} : {1'h0, {1'h0, _GEN_163} + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1223:12, :1229:12, :1556:12, :1558:12, :1564:12, :1565:12
      automatic logic [4:0]  _GEN_165 =
        _GEN_136[23] ? {1'h0, _GEN_164} : {2'h0, _GEN_164[2:0] + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1230:12, :1236:12, :1565:12, :1567:12, :1573:12, :1574:12
      automatic logic [5:0]  _GEN_166 =
        _GEN_137[23] ? {1'h0, _GEN_165} : {3'h0, _GEN_165[2:0] + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1237:12, :1243:12, :1574:12, :1576:12, :1582:12, :1583:12
      automatic logic [6:0]  _GEN_167 =
        _GEN_138[23] ? {1'h0, _GEN_166} : {4'h0, _GEN_166[2:0] + 3'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1244:12, :1250:12, :1583:12, :1585:12, :1591:12, :1592:12
      automatic logic [7:0]  _GEN_168 =
        _GEN_139[23] ? {1'h0, _GEN_167} : {4'h0, _GEN_167[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1251:12, :1257:12, :1592:12, :1594:12, :1600:12, :1601:12
      automatic logic [7:0]  _GEN_169 =
        _GEN_140[23] ? _GEN_168 : {4'h0, _GEN_168[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1258:12, :1264:12, :1601:12, :1603:12, :1604:12
      automatic logic [7:0]  _GEN_170 =
        _GEN_141[23] ? _GEN_169 : {4'h0, _GEN_169[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1265:12, :1271:12, :1604:12, :1606:12, :1607:12
      automatic logic [7:0]  _GEN_171 =
        _GEN_142[23] ? _GEN_170 : {4'h0, _GEN_170[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1272:12, :1278:12, :1607:12, :1609:12, :1610:12
      automatic logic [7:0]  _GEN_172 =
        _GEN_143[23] ? _GEN_171 : {4'h0, _GEN_171[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1279:12, :1285:12, :1610:12, :1612:12, :1613:12
      automatic logic [7:0]  _GEN_173 =
        _GEN_144[23] ? _GEN_172 : {4'h0, _GEN_172[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1286:12, :1292:12, :1613:12, :1615:12, :1616:12
      automatic logic [7:0]  _GEN_174 =
        _GEN_145[23] ? _GEN_173 : {4'h0, _GEN_173[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1293:12, :1299:12, :1616:12, :1618:12, :1619:12
      automatic logic [7:0]  _GEN_175 =
        _GEN_146[23] ? _GEN_174 : {4'h0, _GEN_174[3:0] + 4'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1300:12, :1306:12, :1619:12, :1621:12, :1622:12
      automatic logic [7:0]  _GEN_176 =
        _GEN_147[23] ? _GEN_175 : {3'h0, _GEN_175[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1307:12, :1313:12, :1622:12, :1624:12, :1625:12
      automatic logic [7:0]  _GEN_177 =
        _GEN_148[23] ? _GEN_176 : {3'h0, _GEN_176[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1314:12, :1320:12, :1625:12, :1627:12, :1628:12
      automatic logic [7:0]  _GEN_178 =
        _GEN_149[23] ? _GEN_177 : {3'h0, _GEN_177[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1321:12, :1327:12, :1628:12, :1630:12, :1631:12
      automatic logic [7:0]  _GEN_179 =
        _GEN_150[23] ? _GEN_178 : {3'h0, _GEN_178[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1328:12, :1334:12, :1631:12, :1633:12, :1634:12
      automatic logic [7:0]  _GEN_180 =
        _GEN_151[23] ? _GEN_179 : {3'h0, _GEN_179[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1335:12, :1341:12, :1634:12, :1636:12, :1637:12
      automatic logic [7:0]  _GEN_181 =
        _GEN_152[23] ? _GEN_180 : {3'h0, _GEN_180[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1342:12, :1348:12, :1637:12, :1639:12, :1640:12
      automatic logic [7:0]  _GEN_182 =
        _GEN_153[23] ? _GEN_181 : {3'h0, _GEN_181[4:0] + 5'h1};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1349:12, :1355:12, :1640:12, :1642:12, :1643:12
      automatic logic [11:0] _GEN_183 =
        _GEN_50
        + {2'h0,
           {2'h0, _GEN_132 ? c[30:23] : 8'h1} - 10'h200
             - {2'h0, _GEN_154[23] ? _GEN_182 : {3'h0, _GEN_182[4:0] + 5'h1}}} - 12'h27F;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:553:11, :1001:11, :1201:12, :1356:12, :1362:12, :1523:12, :1531:12, :1643:12, :1645:12, :1646:12, :1651:12, :1652:12, :1654:12
      automatic logic [11:0] _GEN_184 = _GEN_158 ? _GEN_183 - 12'h1 : _GEN_183;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1383:12, :1652:12, :1654:12, :1656:12, :1657:12
      automatic logic [11:0] _GEN_185 = 12'h200 - _GEN_184;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1657:12, :1668:12
      automatic logic [31:0] _GEN_186 = {20'h0, _GEN_185};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1668:12, :1670:12
      automatic logic        _GEN_187 = |(_GEN_185[11:5]);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1668:12, :1673:12
      automatic logic        _GEN_188 = _GEN_184 < 12'h200;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1657:12, :1692:12
      automatic logic [31:0] _GEN_189 =
        _GEN_188 & _GEN_187
          ? {31'h0, |_GEN_159}
          : {31'h0,
             (|(_GEN_159 & (_GEN_187 ? 32'h0 : 32'h1 << _GEN_186) - 32'h1)) & _GEN_188
               & ~_GEN_187} | (_GEN_187 ? 32'h0 : _GEN_159 >> _GEN_186);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1384:12, :1670:12, :1671:12, :1673:12, :1675:12, :1681:12, :1685:12, :1687:12, :1688:12, :1690:12, :1692:12, :1697:12, :1698:12, :1699:12, :1700:12, :1706:12, :1709:12, :1710:12, :1711:12
      automatic logic [31:0] _GEN_190 = _GEN_188 ? _GEN_189 : _GEN_159;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1384:12, :1692:12, :1711:12, :1720:12
      automatic logic        _GEN_191 = _GEN_184 < 12'h2FE;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1657:12, :1730:12
      automatic logic        _GEN_192 = _GEN_191 & ~(_GEN_160[31] & _GEN_184 == 12'h2FD);	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1386:12, :1388:12, :1657:12, :1730:12, :1735:12, :1736:12, :1739:12, :1740:12
      automatic logic        _GEN_193 =
        c[23] & c[24] & c[25] & c[26] & c[27] & c[28] & c[29] & c[30];	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1783:12, :1784:12, :1785:12, :1786:12, :1787:12, :1788:12, :1789:12, :1790:12, :1791:12, :1792:12, :1793:12, :1794:12, :1795:12, :1796:12, :1797:12
      automatic logic        _GEN_194 = _GEN_193 & _GEN_131;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1006:12, :1785:12, :1788:12, :1789:12, :1792:12, :1795:12, :1796:12, :1797:12, :1798:12
      automatic logic        _GEN_195 = ~_GEN_53 & ~(_GEN_194 & ~(c[22]));	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:811:11, :814:11, :1798:12, :1800:12, :1802:12, :1803:12, :1806:12, :1807:12
      automatic logic        _GEN_196 = ~_GEN_52 & ~_GEN_194;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:806:11, :842:11, :1798:12, :1813:12, :1814:12
      automatic logic        _GEN_197 = a[31] ^ c[31];	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1:{19,45}, :1825:12
      automatic logic [31:0] _GEN_198 = {_GEN_197, 31'h0};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1825:12, :1834:12
      automatic logic [31:0] _GEN_199 = {_GEN_197, 31'h7F800000};	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1825:12, :1834:12
      automatic logic        _GEN_200 = ~_GEN_51 & ~_GEN_193;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:793:11, :796:11, :797:11, :800:11, :803:11, :804:11, :805:11, :872:11, :1785:12, :1788:12, :1789:12, :1792:12, :1795:12, :1796:12, :1797:12, :1843:12, :1844:12
      automatic logic [31:0] _GEN_201 = _GEN_190 + 32'h40;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1720:12, :1864:12
      automatic logic [24:0] _GEN_202 =
        _GEN_190[6:0] == 7'h40 ? {_GEN_201[31:8], 1'h0} : _GEN_201[31:7];	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1720:12, :1721:12, :1864:12, :1865:12, :1867:12, :1869:12, :1870:12
      automatic logic        _GEN_203 = _GEN_129 & _GEN_200;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:987:11, :1844:12, :1884:12
      rtlzz_pipe_9_s1 <=
        iv
          ? {_GEN_195
               ? (_GEN_195 & ~_GEN_196
                    ? 5'h0
                    : _GEN_1 | _GEN_130
                        ? {~_GEN_129 & ~_GEN_3 & ~(_GEN_130 & _GEN_131), 4'h0}
                        : {2'h0,
                           _GEN_129
                             ? (_GEN_192
                                  ? {1'h0,
                                     {1'h0, |(_GEN_190[6:0])}
                                       | (_GEN_188
                                            ? {~(_GEN_160[31] & _GEN_184 > 12'h1FE)
                                                 & (|(_GEN_189[6:0])),
                                               1'h0}
                                            : 2'h0)}
                                  : 3'h5)
                             : 3'h0})
               : 5'h10,
             _GEN_196
               ? (~_GEN_129 & _GEN_200
                    ? _GEN_198
                    : _GEN_203
                      & ~(_GEN_191
                          & ~(_GEN_184[6] & _GEN_184[7] & _GEN_184[9] & ~(_GEN_184[1])
                              & ~(_GEN_184[8]) & _GEN_184[2] & _GEN_184[3] & _GEN_184[4]
                              & _GEN_184[5] & ~(_GEN_184[10]) & ~(_GEN_184[11])
                              & _GEN_160[31] & _GEN_184[0]))
                        ? _GEN_199
                        : _GEN_192 & _GEN_203
                            ? _GEN_198
                              | {_GEN_202 == 25'h0 | _GEN_188 ? 9'h0 : _GEN_184[8:0],
                                 23'h0} + {7'h0, _GEN_202}
                            : _GEN_196 & ~_GEN_129 & ~_GEN_200 ? 32'h7FC00000 : _GEN_199)
               : 32'h7FC00000}
          : rtlzz_pipe_9_s1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:25:10, :29:10, :32:10, :987:11, :990:11, :1003:11, :1006:12, :1007:12, :1010:12, :1011:12, :1012:12, :1013:12, :1386:12, :1388:12, :1657:12, :1659:12, :1663:12, :1666:12, :1692:12, :1711:12, :1712:12, :1714:12, :1715:12, :1716:12, :1717:12, :1720:12, :1721:12, :1723:12, :1724:12, :1726:12, :1730:12, :1740:12, :1744:12, :1747:12, :1749:12, :1757:12, :1807:12, :1814:12, :1817:12, :1818:12, :1819:12, :1824:12, :1834:12, :1844:12, :1847:12, :1848:12, :1849:12, :1850:12, :1851:12, :1870:12, :1872:12, :1873:12, :1879:12, :1881:12, :1882:12, :1883:12, :1884:12, :1885:12, :1886:12, :1887:12, :1888:12, :1889:12, :1890:12, :1891:12, :1894:12, :1895:12, :1898:12, :1899:12, :1900:12, :1901:12, :1902:12, :1903:12, :1904:12, :1905:12, :1906:12, :1907:12, :1908:12, :1909:12, :1912:12, :1913:12, :1916:12, :1917:12, :1918:12, :1919:12, :1920:12, :1921:12, :1922:12, :1925:12, :1926:12, :1929:12, :1930:12, :1931:12, :1932:12, :1933:12, :1935:12, :1936:12, :1938:22
    end
  end // always_ff @(posedge)
  reg  [36:0] rtlzz_pipe_9_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1940:22
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1940:22
    if (_GEN)	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1940:22
      rtlzz_pipe_9_s2 <= 37'h7F800000;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1940:22
    else	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1940:22
      rtlzz_pipe_9_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_9_s1 : rtlzz_pipe_9_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1938:22, :1940:22, :1951:21
  end // always_ff @(posedge)
  reg  [63:0] rtlzz_pipe_10_s1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1947:23
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1947:23
    if (_GEN)	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1947:23
      rtlzz_pipe_10_s1 <= 64'h0;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1947:23
    else	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1947:23
      rtlzz_pipe_10_s1 <= iv ? {32'h0, a} * {32'h0, b} : rtlzz_pipe_10_s1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1942:12, :1944:12, :1945:12, :1947:23
  end // always_ff @(posedge)
  reg  [63:0] rtlzz_pipe_10_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1949:23
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1949:23
    if (_GEN)	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1949:23
      rtlzz_pipe_10_s2 <= 64'h0;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1949:23
    else	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1949:23
      rtlzz_pipe_10_s2 <= rtlzz_valid_s1 ? rtlzz_pipe_10_s1 : rtlzz_pipe_10_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1947:23, :1949:23, :1951:21
  end // always_ff @(posedge)
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1951:21
    if (_GEN)	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1951:21
      rtlzz_valid_s1 <= 1'h0;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1951:21
    else	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1951:21
      rtlzz_valid_s1 <= iv;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1951:21
  end // always_ff @(posedge)
  reg         rtlzz_valid_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1953:21
  always_ff @(posedge clk) begin	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1953:21
    if (_GEN)	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1953:21
      rtlzz_valid_s2 <= 1'h0;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1953:21
    else	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:4:9, :1953:21
      rtlzz_valid_s2 <= rtlzz_valid_s1;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1951:21, :1953:21
  end // always_ff @(posedge)
  assign y = rtlzz_pipe_8_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:972:22, :1954:3
  assign z = rtlzz_pipe_9_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1940:22, :1954:3
  assign m = rtlzz_pipe_10_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1949:23, :1954:3
  assign ov = rtlzz_valid_s2;	// /tmp/rtlzz-circt-292-1949832432964060/input.mlir:1953:21, :1954:3
endmodule
