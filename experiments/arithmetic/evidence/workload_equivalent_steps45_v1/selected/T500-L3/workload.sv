`timescale 1ns/1ps

module WorkloadCore(
    input logic [31:0] a, // decl: /home/zyrv/vulsim/workload.cpp:3:1-3:10; prim: /home/zyrv/vulsim/workload.cpp:3:1-3:10
    input logic [31:0] b, // decl: /home/zyrv/vulsim/workload.cpp:5:1-5:10; prim: /home/zyrv/vulsim/workload.cpp:5:1-5:10
    input logic [63:0] c, // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
    input logic iv, // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8
    output logic [63:0] y, // decl: /home/zyrv/vulsim/workload.cpp:11:1-11:10; prim: /home/zyrv/vulsim/workload.cpp:15:5-15:47
    output logic ov, // decl: /home/zyrv/vulsim/workload.cpp:13:1-13:8; prim: /home/zyrv/vulsim/workload.cpp:13:1-13:8
    input logic rstn, // decl: <none>; prim: <none>
    input logic clk // decl: <none>; prim: <none>
);

    logic [63:0] s8_norm_mul_2_v0; // decl: <none>; prim: /home/zyrv/vulsim/workload.cpp:3:1-3:10
    logic [63:0] s8_norm_add_4_v0; // decl: <none>; prim: /home/zyrv/vulsim/workload.cpp:15:23-15:33
    logic [63:0] __beopt_width_10; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_11; // decl: <none>; prim: <none>
    logic [31:0] mul_precision_10; // decl: <none>; prim: <none>
    logic [31:0] mul_precision_11; // decl: <none>; prim: <none>
    logic [63:0] arith_original_12; // decl: <none>; prim: /home/zyrv/vulsim/workload.cpp:3:1-3:10
    logic [3:0] mul_tree_12_13; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_14; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_15; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_16; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_17; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_18; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_19; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_20; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_21; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_22; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_23; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_24; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_25; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_26; // decl: <none>; prim: <none>
    logic [19:0] mul_tree_12_27; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_28; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_29; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_30; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_31; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_32; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_33; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_34; // decl: <none>; prim: <none>
    logic [27:0] mul_tree_12_35; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_36; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_37; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_38; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_12_39; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_40; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_41; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_42; // decl: <none>; prim: <none>
    logic [35:0] mul_tree_12_43; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_44; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_45; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_46; // decl: <none>; prim: <none>
    logic [11:0] mul_tree_12_47; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_48; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_49; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_50; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_51; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_52; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_53; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_54; // decl: <none>; prim: <none>
    logic [19:0] mul_tree_12_55; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_56; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_57; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_58; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_59; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_60; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_61; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_62; // decl: <none>; prim: <none>
    logic [27:0] mul_tree_12_63; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_64; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_65; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_66; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_12_67; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_68; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_69; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_70; // decl: <none>; prim: <none>
    logic [35:0] mul_tree_12_71; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_72; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_73; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_74; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_75; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_76; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_77; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_78; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_12_79; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_80; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_81; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_82; // decl: <none>; prim: <none>
    logic [19:0] mul_tree_12_83; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_84; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_85; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_86; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_87; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_88; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_89; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_90; // decl: <none>; prim: <none>
    logic [27:0] mul_tree_12_91; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_92; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_93; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_94; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_12_95; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_96; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_97; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_98; // decl: <none>; prim: <none>
    logic [35:0] mul_tree_12_99; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_100; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_101; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_102; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_103; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_104; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_105; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_106; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_107; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_108; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_109; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_110; // decl: <none>; prim: <none>
    logic [19:0] mul_tree_12_111; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_112; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_113; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_114; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_115; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_116; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_117; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_118; // decl: <none>; prim: <none>
    logic [27:0] mul_tree_12_119; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_120; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_121; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_122; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_12_123; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_124; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_125; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_126; // decl: <none>; prim: <none>
    logic [35:0] mul_tree_12_127; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_128; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_129; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_130; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_131; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_132; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_133; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_134; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_135; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_136; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_137; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_138; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_12_139; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_140; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_141; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_142; // decl: <none>; prim: <none>
    logic [23:0] mul_tree_12_143; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_144; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_145; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_146; // decl: <none>; prim: <none>
    logic [27:0] mul_tree_12_147; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_148; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_149; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_150; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_12_151; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_152; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_153; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_154; // decl: <none>; prim: <none>
    logic [35:0] mul_tree_12_155; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_156; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_157; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_158; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_159; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_160; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_161; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_162; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_163; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_164; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_165; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_166; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_12_167; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_168; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_169; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_170; // decl: <none>; prim: <none>
    logic [51:0] mul_tree_12_171; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_172; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_173; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_174; // decl: <none>; prim: <none>
    logic [27:0] mul_tree_12_175; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_176; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_177; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_178; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_12_179; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_180; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_181; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_182; // decl: <none>; prim: <none>
    logic [35:0] mul_tree_12_183; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_184; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_185; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_186; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_187; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_188; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_189; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_190; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_191; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_192; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_193; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_194; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_12_195; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_196; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_197; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_198; // decl: <none>; prim: <none>
    logic [51:0] mul_tree_12_199; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_200; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_201; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_202; // decl: <none>; prim: <none>
    logic [55:0] mul_tree_12_203; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_204; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_205; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_206; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_12_207; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_208; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_209; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_210; // decl: <none>; prim: <none>
    logic [35:0] mul_tree_12_211; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_212; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_213; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_214; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_215; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_216; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_217; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_218; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_219; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_220; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_221; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_222; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_12_223; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_224; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_225; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_226; // decl: <none>; prim: <none>
    logic [51:0] mul_tree_12_227; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_228; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_229; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_230; // decl: <none>; prim: <none>
    logic [55:0] mul_tree_12_231; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_232; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_233; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_234; // decl: <none>; prim: <none>
    logic [59:0] mul_tree_12_235; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_236; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_237; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_238; // decl: <none>; prim: <none>
    logic [35:0] mul_tree_12_239; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_240; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_241; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_242; // decl: <none>; prim: <none>
    logic [39:0] mul_tree_12_243; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_244; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_245; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_246; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_247; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_248; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_249; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_250; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_12_251; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_252; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_253; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_254; // decl: <none>; prim: <none>
    logic [51:0] mul_tree_12_255; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_256; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_257; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_258; // decl: <none>; prim: <none>
    logic [55:0] mul_tree_12_259; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_260; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_261; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_262; // decl: <none>; prim: <none>
    logic [59:0] mul_tree_12_263; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_264; // decl: <none>; prim: <none>
    logic [3:0] mul_tree_12_265; // decl: <none>; prim: <none>
    logic [7:0] mul_tree_12_266; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_12_267; // decl: <none>; prim: <none>
    logic [12:0] mul_tree_12_268; // decl: <none>; prim: <none>
    logic [12:0] mul_tree_12_269; // decl: <none>; prim: <none>
    logic [12:0] mul_tree_12_270; // decl: <none>; prim: <none>
    logic [20:0] mul_tree_12_271; // decl: <none>; prim: <none>
    logic [20:0] mul_tree_12_272; // decl: <none>; prim: <none>
    logic [20:0] mul_tree_12_273; // decl: <none>; prim: <none>
    logic [28:0] mul_tree_12_274; // decl: <none>; prim: <none>
    logic [28:0] mul_tree_12_275; // decl: <none>; prim: <none>
    logic [28:0] mul_tree_12_276; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_277; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_278; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_279; // decl: <none>; prim: <none>
    logic [16:0] mul_tree_12_280; // decl: <none>; prim: <none>
    logic [16:0] mul_tree_12_281; // decl: <none>; prim: <none>
    logic [16:0] mul_tree_12_282; // decl: <none>; prim: <none>
    logic [24:0] mul_tree_12_283; // decl: <none>; prim: <none>
    logic [24:0] mul_tree_12_284; // decl: <none>; prim: <none>
    logic [24:0] mul_tree_12_285; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_286; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_287; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_288; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_289; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_290; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_291; // decl: <none>; prim: <none>
    logic [20:0] mul_tree_12_292; // decl: <none>; prim: <none>
    logic [20:0] mul_tree_12_293; // decl: <none>; prim: <none>
    logic [20:0] mul_tree_12_294; // decl: <none>; prim: <none>
    logic [28:0] mul_tree_12_295; // decl: <none>; prim: <none>
    logic [28:0] mul_tree_12_296; // decl: <none>; prim: <none>
    logic [28:0] mul_tree_12_297; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_298; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_299; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_300; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_301; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_302; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_303; // decl: <none>; prim: <none>
    logic [24:0] mul_tree_12_304; // decl: <none>; prim: <none>
    logic [24:0] mul_tree_12_305; // decl: <none>; prim: <none>
    logic [24:0] mul_tree_12_306; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_307; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_308; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_309; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_310; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_311; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_312; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_313; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_314; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_315; // decl: <none>; prim: <none>
    logic [28:0] mul_tree_12_316; // decl: <none>; prim: <none>
    logic [28:0] mul_tree_12_317; // decl: <none>; prim: <none>
    logic [28:0] mul_tree_12_318; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_319; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_320; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_321; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_322; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_323; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_324; // decl: <none>; prim: <none>
    logic [52:0] mul_tree_12_325; // decl: <none>; prim: <none>
    logic [52:0] mul_tree_12_326; // decl: <none>; prim: <none>
    logic [52:0] mul_tree_12_327; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_328; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_329; // decl: <none>; prim: <none>
    logic [32:0] mul_tree_12_330; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_331; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_332; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_333; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_334; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_335; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_336; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_337; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_338; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_339; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_340; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_341; // decl: <none>; prim: <none>
    logic [36:0] mul_tree_12_342; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_343; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_344; // decl: <none>; prim: <none>
    logic [44:0] mul_tree_12_345; // decl: <none>; prim: <none>
    logic [52:0] mul_tree_12_346; // decl: <none>; prim: <none>
    logic [52:0] mul_tree_12_347; // decl: <none>; prim: <none>
    logic [52:0] mul_tree_12_348; // decl: <none>; prim: <none>
    logic [60:0] mul_tree_12_349; // decl: <none>; prim: <none>
    logic [60:0] mul_tree_12_350; // decl: <none>; prim: <none>
    logic [60:0] mul_tree_12_351; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_352; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_353; // decl: <none>; prim: <none>
    logic [40:0] mul_tree_12_354; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_355; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_356; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_12_357; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_358; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_359; // decl: <none>; prim: <none>
    logic [56:0] mul_tree_12_360; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_12_361; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_12_362; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_12_363; // decl: <none>; prim: <none>
    logic [21:0] mul_tree_12_364; // decl: <none>; prim: <none>
    logic [21:0] mul_tree_12_365; // decl: <none>; prim: <none>
    logic [21:0] mul_tree_12_366; // decl: <none>; prim: <none>
    logic [37:0] mul_tree_12_367; // decl: <none>; prim: <none>
    logic [37:0] mul_tree_12_368; // decl: <none>; prim: <none>
    logic [37:0] mul_tree_12_369; // decl: <none>; prim: <none>
    logic [25:0] mul_tree_12_370; // decl: <none>; prim: <none>
    logic [25:0] mul_tree_12_371; // decl: <none>; prim: <none>
    logic [25:0] mul_tree_12_372; // decl: <none>; prim: <none>
    logic [41:0] mul_tree_12_373; // decl: <none>; prim: <none>
    logic [41:0] mul_tree_12_374; // decl: <none>; prim: <none>
    logic [41:0] mul_tree_12_375; // decl: <none>; prim: <none>
    logic [29:0] mul_tree_12_376; // decl: <none>; prim: <none>
    logic [29:0] mul_tree_12_377; // decl: <none>; prim: <none>
    logic [29:0] mul_tree_12_378; // decl: <none>; prim: <none>
    logic [45:0] mul_tree_12_379; // decl: <none>; prim: <none>
    logic [45:0] mul_tree_12_380; // decl: <none>; prim: <none>
    logic [45:0] mul_tree_12_381; // decl: <none>; prim: <none>
    logic [33:0] mul_tree_12_382; // decl: <none>; prim: <none>
    logic [33:0] mul_tree_12_383; // decl: <none>; prim: <none>
    logic [33:0] mul_tree_12_384; // decl: <none>; prim: <none>
    logic [49:0] mul_tree_12_385; // decl: <none>; prim: <none>
    logic [49:0] mul_tree_12_386; // decl: <none>; prim: <none>
    logic [49:0] mul_tree_12_387; // decl: <none>; prim: <none>
    logic [37:0] mul_tree_12_388; // decl: <none>; prim: <none>
    logic [37:0] mul_tree_12_389; // decl: <none>; prim: <none>
    logic [37:0] mul_tree_12_390; // decl: <none>; prim: <none>
    logic [53:0] mul_tree_12_391; // decl: <none>; prim: <none>
    logic [53:0] mul_tree_12_392; // decl: <none>; prim: <none>
    logic [53:0] mul_tree_12_393; // decl: <none>; prim: <none>
    logic [41:0] mul_tree_12_394; // decl: <none>; prim: <none>
    logic [41:0] mul_tree_12_395; // decl: <none>; prim: <none>
    logic [41:0] mul_tree_12_396; // decl: <none>; prim: <none>
    logic [57:0] mul_tree_12_397; // decl: <none>; prim: <none>
    logic [57:0] mul_tree_12_398; // decl: <none>; prim: <none>
    logic [57:0] mul_tree_12_399; // decl: <none>; prim: <none>
    logic [45:0] mul_tree_12_400; // decl: <none>; prim: <none>
    logic [45:0] mul_tree_12_401; // decl: <none>; prim: <none>
    logic [45:0] mul_tree_12_402; // decl: <none>; prim: <none>
    logic [61:0] mul_tree_12_403; // decl: <none>; prim: <none>
    logic [61:0] mul_tree_12_404; // decl: <none>; prim: <none>
    logic [61:0] mul_tree_12_405; // decl: <none>; prim: <none>
    logic [49:0] mul_tree_12_406; // decl: <none>; prim: <none>
    logic [49:0] mul_tree_12_407; // decl: <none>; prim: <none>
    logic [49:0] mul_tree_12_408; // decl: <none>; prim: <none>
    logic [65:0] mul_tree_12_409; // decl: <none>; prim: <none>
    logic [65:0] mul_tree_12_410; // decl: <none>; prim: <none>
    logic [65:0] mul_tree_12_411; // decl: <none>; prim: <none>
    logic [38:0] mul_tree_12_412; // decl: <none>; prim: <none>
    logic [38:0] mul_tree_12_413; // decl: <none>; prim: <none>
    logic [38:0] mul_tree_12_414; // decl: <none>; prim: <none>
    logic [42:0] mul_tree_12_415; // decl: <none>; prim: <none>
    logic [42:0] mul_tree_12_416; // decl: <none>; prim: <none>
    logic [42:0] mul_tree_12_417; // decl: <none>; prim: <none>
    logic [46:0] mul_tree_12_418; // decl: <none>; prim: <none>
    logic [46:0] mul_tree_12_419; // decl: <none>; prim: <none>
    logic [46:0] mul_tree_12_420; // decl: <none>; prim: <none>
    logic [50:0] mul_tree_12_421; // decl: <none>; prim: <none>
    logic [50:0] mul_tree_12_422; // decl: <none>; prim: <none>
    logic [50:0] mul_tree_12_423; // decl: <none>; prim: <none>
    logic [54:0] mul_tree_12_424; // decl: <none>; prim: <none>
    logic [54:0] mul_tree_12_425; // decl: <none>; prim: <none>
    logic [54:0] mul_tree_12_426; // decl: <none>; prim: <none>
    logic [58:0] mul_tree_12_427; // decl: <none>; prim: <none>
    logic [58:0] mul_tree_12_428; // decl: <none>; prim: <none>
    logic [58:0] mul_tree_12_429; // decl: <none>; prim: <none>
    logic [62:0] mul_tree_12_430; // decl: <none>; prim: <none>
    logic [62:0] mul_tree_12_431; // decl: <none>; prim: <none>
    logic [62:0] mul_tree_12_432; // decl: <none>; prim: <none>
    logic [66:0] mul_tree_12_433; // decl: <none>; prim: <none>
    logic [66:0] mul_tree_12_434; // decl: <none>; prim: <none>
    logic [66:0] mul_tree_12_435; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_436; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_437; // decl: <none>; prim: <none>
    logic [43:0] mul_tree_12_438; // decl: <none>; prim: <none>
    logic [51:0] mul_tree_12_439; // decl: <none>; prim: <none>
    logic [51:0] mul_tree_12_440; // decl: <none>; prim: <none>
    logic [51:0] mul_tree_12_441; // decl: <none>; prim: <none>
    logic [59:0] mul_tree_12_442; // decl: <none>; prim: <none>
    logic [59:0] mul_tree_12_443; // decl: <none>; prim: <none>
    logic [59:0] mul_tree_12_444; // decl: <none>; prim: <none>
    logic [67:0] mul_tree_12_445; // decl: <none>; prim: <none>
    logic [67:0] mul_tree_12_446; // decl: <none>; prim: <none>
    logic [67:0] mul_tree_12_447; // decl: <none>; prim: <none>
    logic [52:0] mul_tree_12_448; // decl: <none>; prim: <none>
    logic [52:0] mul_tree_12_449; // decl: <none>; prim: <none>
    logic [52:0] mul_tree_12_450; // decl: <none>; prim: <none>
    logic [68:0] mul_tree_12_451; // decl: <none>; prim: <none>
    logic [68:0] mul_tree_12_452; // decl: <none>; prim: <none>
    logic [68:0] mul_tree_12_453; // decl: <none>; prim: <none>
    logic [69:0] mul_tree_12_454; // decl: <none>; prim: <none>
    logic [69:0] mul_tree_12_455; // decl: <none>; prim: <none>
    logic [69:0] mul_tree_12_456; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_12_457; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_2_s1; // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
    logic [63:0] rtlzz_pipe_2_s2; // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
    logic [7:0] rtlzz_pipe_15_s1; // decl: <none>; prim: <none>
    logic [11:0] rtlzz_pipe_19_s1; // decl: <none>; prim: <none>
    logic [15:0] rtlzz_pipe_23_s1; // decl: <none>; prim: <none>
    logic [19:0] rtlzz_pipe_27_s1; // decl: <none>; prim: <none>
    logic [23:0] rtlzz_pipe_31_s1; // decl: <none>; prim: <none>
    logic [27:0] rtlzz_pipe_35_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_39_s1; // decl: <none>; prim: <none>
    logic [35:0] rtlzz_pipe_43_s1; // decl: <none>; prim: <none>
    logic [11:0] rtlzz_pipe_47_s1; // decl: <none>; prim: <none>
    logic [15:0] rtlzz_pipe_51_s1; // decl: <none>; prim: <none>
    logic [19:0] rtlzz_pipe_55_s1; // decl: <none>; prim: <none>
    logic [23:0] rtlzz_pipe_59_s1; // decl: <none>; prim: <none>
    logic [27:0] rtlzz_pipe_63_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_67_s1; // decl: <none>; prim: <none>
    logic [35:0] rtlzz_pipe_71_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_75_s1; // decl: <none>; prim: <none>
    logic [15:0] rtlzz_pipe_79_s1; // decl: <none>; prim: <none>
    logic [19:0] rtlzz_pipe_83_s1; // decl: <none>; prim: <none>
    logic [23:0] rtlzz_pipe_87_s1; // decl: <none>; prim: <none>
    logic [27:0] rtlzz_pipe_91_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_95_s1; // decl: <none>; prim: <none>
    logic [35:0] rtlzz_pipe_99_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_103_s1; // decl: <none>; prim: <none>
    logic [43:0] rtlzz_pipe_107_s1; // decl: <none>; prim: <none>
    logic [19:0] rtlzz_pipe_111_s1; // decl: <none>; prim: <none>
    logic [23:0] rtlzz_pipe_115_s1; // decl: <none>; prim: <none>
    logic [27:0] rtlzz_pipe_119_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_123_s1; // decl: <none>; prim: <none>
    logic [35:0] rtlzz_pipe_127_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_131_s1; // decl: <none>; prim: <none>
    logic [43:0] rtlzz_pipe_135_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_139_s1; // decl: <none>; prim: <none>
    logic [23:0] rtlzz_pipe_143_s1; // decl: <none>; prim: <none>
    logic [27:0] rtlzz_pipe_147_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_151_s1; // decl: <none>; prim: <none>
    logic [35:0] rtlzz_pipe_155_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_159_s1; // decl: <none>; prim: <none>
    logic [43:0] rtlzz_pipe_163_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_167_s1; // decl: <none>; prim: <none>
    logic [51:0] rtlzz_pipe_171_s1; // decl: <none>; prim: <none>
    logic [27:0] rtlzz_pipe_175_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_179_s1; // decl: <none>; prim: <none>
    logic [35:0] rtlzz_pipe_183_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_187_s1; // decl: <none>; prim: <none>
    logic [43:0] rtlzz_pipe_191_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_195_s1; // decl: <none>; prim: <none>
    logic [51:0] rtlzz_pipe_199_s1; // decl: <none>; prim: <none>
    logic [55:0] rtlzz_pipe_203_s1; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_207_s1; // decl: <none>; prim: <none>
    logic [35:0] rtlzz_pipe_211_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_215_s1; // decl: <none>; prim: <none>
    logic [43:0] rtlzz_pipe_219_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_223_s1; // decl: <none>; prim: <none>
    logic [51:0] rtlzz_pipe_227_s1; // decl: <none>; prim: <none>
    logic [55:0] rtlzz_pipe_231_s1; // decl: <none>; prim: <none>
    logic [59:0] rtlzz_pipe_235_s1; // decl: <none>; prim: <none>
    logic [35:0] rtlzz_pipe_239_s1; // decl: <none>; prim: <none>
    logic [39:0] rtlzz_pipe_243_s1; // decl: <none>; prim: <none>
    logic [43:0] rtlzz_pipe_247_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_251_s1; // decl: <none>; prim: <none>
    logic [51:0] rtlzz_pipe_255_s1; // decl: <none>; prim: <none>
    logic [55:0] rtlzz_pipe_259_s1; // decl: <none>; prim: <none>
    logic [59:0] rtlzz_pipe_263_s1; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_267_s1; // decl: <none>; prim: <none>
    logic [43:0] rtlzz_pipe_438_s2; // decl: <none>; prim: <none>
    logic [51:0] rtlzz_pipe_441_s2; // decl: <none>; prim: <none>
    logic [59:0] rtlzz_pipe_444_s2; // decl: <none>; prim: <none>
    logic [67:0] rtlzz_pipe_447_s2; // decl: <none>; prim: <none>
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8
    logic rtlzz_valid_s2; // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8


    assign s8_norm_mul_2_v0 = arith_original_12; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_5_reduce rtlzz_reduce_5(.i459(rtlzz_pipe_2_s2), .i524(rtlzz_pipe_438_s2), .i525(rtlzz_pipe_441_s2), .i526(rtlzz_pipe_444_s2), .i527(rtlzz_pipe_447_s2), .y(s8_norm_add_4_v0));
    assign y = s8_norm_add_4_v0; // decl: /home/zyrv/vulsim/workload.cpp:11:1-11:10; prim: /home/zyrv/vulsim/workload.cpp:15:5-15:47
    assign ov = rtlzz_valid_s2; // decl: <none>; prim: <none>
    assign __beopt_width_10 = ({32'h0, a}); // decl: <none>; prim: <none>
    assign __beopt_width_11 = ({32'h0, b}); // decl: <none>; prim: <none>
    assign mul_precision_10 = __beopt_width_10[31:0]; // decl: <none>; prim: <none>
    assign mul_precision_11 = __beopt_width_11[31:0]; // decl: <none>; prim: <none>
    assign arith_original_12 = mul_tree_12_457; // decl: <none>; prim: <none>
    assign mul_tree_12_13 = mul_precision_10[3:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_14 = mul_precision_11[3:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_15Core rtlzz_owner_15(.a(4'(mul_tree_12_13)), .b(4'(mul_tree_12_14)), .cin(1'b0), .value(mul_tree_12_15));
    assign mul_tree_12_16 = mul_precision_10[3:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_17 = mul_precision_11[7:4]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_18Core rtlzz_owner_18(.a(4'(mul_tree_12_16)), .b(4'(mul_tree_12_17)), .cin(1'b0), .value(mul_tree_12_18));
    assign mul_tree_12_19 = {mul_tree_12_18, 4'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_20 = mul_precision_10[3:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_21 = mul_precision_11[11:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_22Core rtlzz_owner_22(.a(4'(mul_tree_12_20)), .b(4'(mul_tree_12_21)), .cin(1'b0), .value(mul_tree_12_22));
    assign mul_tree_12_23 = {mul_tree_12_22, 8'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_24 = mul_precision_10[3:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_25 = mul_precision_11[15:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_26Core rtlzz_owner_26(.a(4'(mul_tree_12_24)), .b(4'(mul_tree_12_25)), .cin(1'b0), .value(mul_tree_12_26));
    assign mul_tree_12_27 = {mul_tree_12_26, 12'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_28 = mul_precision_10[3:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_29 = mul_precision_11[19:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_30Core rtlzz_owner_30(.a(4'(mul_tree_12_28)), .b(4'(mul_tree_12_29)), .cin(1'b0), .value(mul_tree_12_30));
    assign mul_tree_12_31 = {mul_tree_12_30, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_32 = mul_precision_10[3:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_33 = mul_precision_11[23:20]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_34Core rtlzz_owner_34(.a(4'(mul_tree_12_32)), .b(4'(mul_tree_12_33)), .cin(1'b0), .value(mul_tree_12_34));
    assign mul_tree_12_35 = {mul_tree_12_34, 20'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_36 = mul_precision_10[3:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_37 = mul_precision_11[27:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_38Core rtlzz_owner_38(.a(4'(mul_tree_12_36)), .b(4'(mul_tree_12_37)), .cin(1'b0), .value(mul_tree_12_38));
    assign mul_tree_12_39 = {mul_tree_12_38, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_40 = mul_precision_10[3:0]; // decl: <none>; prim: <none>
    assign mul_tree_12_41 = mul_precision_11[31:28]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_42Core rtlzz_owner_42(.a(4'(mul_tree_12_40)), .b(4'(mul_tree_12_41)), .cin(1'b0), .value(mul_tree_12_42));
    assign mul_tree_12_43 = {mul_tree_12_42, 28'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_44 = mul_precision_10[7:4]; // decl: <none>; prim: <none>
    assign mul_tree_12_45 = mul_precision_11[3:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_46Core rtlzz_owner_46(.a(4'(mul_tree_12_44)), .b(4'(mul_tree_12_45)), .cin(1'b0), .value(mul_tree_12_46));
    assign mul_tree_12_47 = {mul_tree_12_46, 4'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_48 = mul_precision_10[7:4]; // decl: <none>; prim: <none>
    assign mul_tree_12_49 = mul_precision_11[7:4]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_50Core rtlzz_owner_50(.a(4'(mul_tree_12_48)), .b(4'(mul_tree_12_49)), .cin(1'b0), .value(mul_tree_12_50));
    assign mul_tree_12_51 = {mul_tree_12_50, 8'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_52 = mul_precision_10[7:4]; // decl: <none>; prim: <none>
    assign mul_tree_12_53 = mul_precision_11[11:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_54Core rtlzz_owner_54(.a(4'(mul_tree_12_52)), .b(4'(mul_tree_12_53)), .cin(1'b0), .value(mul_tree_12_54));
    assign mul_tree_12_55 = {mul_tree_12_54, 12'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_56 = mul_precision_10[7:4]; // decl: <none>; prim: <none>
    assign mul_tree_12_57 = mul_precision_11[15:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_58Core rtlzz_owner_58(.a(4'(mul_tree_12_56)), .b(4'(mul_tree_12_57)), .cin(1'b0), .value(mul_tree_12_58));
    assign mul_tree_12_59 = {mul_tree_12_58, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_60 = mul_precision_10[7:4]; // decl: <none>; prim: <none>
    assign mul_tree_12_61 = mul_precision_11[19:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_62Core rtlzz_owner_62(.a(4'(mul_tree_12_60)), .b(4'(mul_tree_12_61)), .cin(1'b0), .value(mul_tree_12_62));
    assign mul_tree_12_63 = {mul_tree_12_62, 20'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_64 = mul_precision_10[7:4]; // decl: <none>; prim: <none>
    assign mul_tree_12_65 = mul_precision_11[23:20]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_66Core rtlzz_owner_66(.a(4'(mul_tree_12_64)), .b(4'(mul_tree_12_65)), .cin(1'b0), .value(mul_tree_12_66));
    assign mul_tree_12_67 = {mul_tree_12_66, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_68 = mul_precision_10[7:4]; // decl: <none>; prim: <none>
    assign mul_tree_12_69 = mul_precision_11[27:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_70Core rtlzz_owner_70(.a(4'(mul_tree_12_68)), .b(4'(mul_tree_12_69)), .cin(1'b0), .value(mul_tree_12_70));
    assign mul_tree_12_71 = {mul_tree_12_70, 28'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_72 = mul_precision_10[7:4]; // decl: <none>; prim: <none>
    assign mul_tree_12_73 = mul_precision_11[31:28]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_74Core rtlzz_owner_74(.a(4'(mul_tree_12_72)), .b(4'(mul_tree_12_73)), .cin(1'b0), .value(mul_tree_12_74));
    assign mul_tree_12_75 = {mul_tree_12_74, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_76 = mul_precision_10[11:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_77 = mul_precision_11[3:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_78Core rtlzz_owner_78(.a(4'(mul_tree_12_76)), .b(4'(mul_tree_12_77)), .cin(1'b0), .value(mul_tree_12_78));
    assign mul_tree_12_79 = {mul_tree_12_78, 8'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_80 = mul_precision_10[11:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_81 = mul_precision_11[7:4]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_82Core rtlzz_owner_82(.a(4'(mul_tree_12_80)), .b(4'(mul_tree_12_81)), .cin(1'b0), .value(mul_tree_12_82));
    assign mul_tree_12_83 = {mul_tree_12_82, 12'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_84 = mul_precision_10[11:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_85 = mul_precision_11[11:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_86Core rtlzz_owner_86(.a(4'(mul_tree_12_84)), .b(4'(mul_tree_12_85)), .cin(1'b0), .value(mul_tree_12_86));
    assign mul_tree_12_87 = {mul_tree_12_86, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_88 = mul_precision_10[11:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_89 = mul_precision_11[15:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_90Core rtlzz_owner_90(.a(4'(mul_tree_12_88)), .b(4'(mul_tree_12_89)), .cin(1'b0), .value(mul_tree_12_90));
    assign mul_tree_12_91 = {mul_tree_12_90, 20'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_92 = mul_precision_10[11:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_93 = mul_precision_11[19:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_94Core rtlzz_owner_94(.a(4'(mul_tree_12_92)), .b(4'(mul_tree_12_93)), .cin(1'b0), .value(mul_tree_12_94));
    assign mul_tree_12_95 = {mul_tree_12_94, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_96 = mul_precision_10[11:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_97 = mul_precision_11[23:20]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_98Core rtlzz_owner_98(.a(4'(mul_tree_12_96)), .b(4'(mul_tree_12_97)), .cin(1'b0), .value(mul_tree_12_98));
    assign mul_tree_12_99 = {mul_tree_12_98, 28'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_100 = mul_precision_10[11:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_101 = mul_precision_11[27:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_102Core rtlzz_owner_102(.a(4'(mul_tree_12_100)), .b(4'(mul_tree_12_101)), .cin(1'b0), .value(mul_tree_12_102));
    assign mul_tree_12_103 = {mul_tree_12_102, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_104 = mul_precision_10[11:8]; // decl: <none>; prim: <none>
    assign mul_tree_12_105 = mul_precision_11[31:28]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_106Core rtlzz_owner_106(.a(4'(mul_tree_12_104)), .b(4'(mul_tree_12_105)), .cin(1'b0), .value(mul_tree_12_106));
    assign mul_tree_12_107 = {mul_tree_12_106, 36'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_108 = mul_precision_10[15:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_109 = mul_precision_11[3:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_110Core rtlzz_owner_110(.a(4'(mul_tree_12_108)), .b(4'(mul_tree_12_109)), .cin(1'b0), .value(mul_tree_12_110));
    assign mul_tree_12_111 = {mul_tree_12_110, 12'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_112 = mul_precision_10[15:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_113 = mul_precision_11[7:4]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_114Core rtlzz_owner_114(.a(4'(mul_tree_12_112)), .b(4'(mul_tree_12_113)), .cin(1'b0), .value(mul_tree_12_114));
    assign mul_tree_12_115 = {mul_tree_12_114, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_116 = mul_precision_10[15:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_117 = mul_precision_11[11:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_118Core rtlzz_owner_118(.a(4'(mul_tree_12_116)), .b(4'(mul_tree_12_117)), .cin(1'b0), .value(mul_tree_12_118));
    assign mul_tree_12_119 = {mul_tree_12_118, 20'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_120 = mul_precision_10[15:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_121 = mul_precision_11[15:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_122Core rtlzz_owner_122(.a(4'(mul_tree_12_120)), .b(4'(mul_tree_12_121)), .cin(1'b0), .value(mul_tree_12_122));
    assign mul_tree_12_123 = {mul_tree_12_122, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_124 = mul_precision_10[15:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_125 = mul_precision_11[19:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_126Core rtlzz_owner_126(.a(4'(mul_tree_12_124)), .b(4'(mul_tree_12_125)), .cin(1'b0), .value(mul_tree_12_126));
    assign mul_tree_12_127 = {mul_tree_12_126, 28'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_128 = mul_precision_10[15:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_129 = mul_precision_11[23:20]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_130Core rtlzz_owner_130(.a(4'(mul_tree_12_128)), .b(4'(mul_tree_12_129)), .cin(1'b0), .value(mul_tree_12_130));
    assign mul_tree_12_131 = {mul_tree_12_130, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_132 = mul_precision_10[15:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_133 = mul_precision_11[27:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_134Core rtlzz_owner_134(.a(4'(mul_tree_12_132)), .b(4'(mul_tree_12_133)), .cin(1'b0), .value(mul_tree_12_134));
    assign mul_tree_12_135 = {mul_tree_12_134, 36'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_136 = mul_precision_10[15:12]; // decl: <none>; prim: <none>
    assign mul_tree_12_137 = mul_precision_11[31:28]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_138Core rtlzz_owner_138(.a(4'(mul_tree_12_136)), .b(4'(mul_tree_12_137)), .cin(1'b0), .value(mul_tree_12_138));
    assign mul_tree_12_139 = {mul_tree_12_138, 40'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_140 = mul_precision_10[19:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_141 = mul_precision_11[3:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_142Core rtlzz_owner_142(.a(4'(mul_tree_12_140)), .b(4'(mul_tree_12_141)), .cin(1'b0), .value(mul_tree_12_142));
    assign mul_tree_12_143 = {mul_tree_12_142, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_144 = mul_precision_10[19:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_145 = mul_precision_11[7:4]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_146Core rtlzz_owner_146(.a(4'(mul_tree_12_144)), .b(4'(mul_tree_12_145)), .cin(1'b0), .value(mul_tree_12_146));
    assign mul_tree_12_147 = {mul_tree_12_146, 20'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_148 = mul_precision_10[19:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_149 = mul_precision_11[11:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_150Core rtlzz_owner_150(.a(4'(mul_tree_12_148)), .b(4'(mul_tree_12_149)), .cin(1'b0), .value(mul_tree_12_150));
    assign mul_tree_12_151 = {mul_tree_12_150, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_152 = mul_precision_10[19:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_153 = mul_precision_11[15:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_154Core rtlzz_owner_154(.a(4'(mul_tree_12_152)), .b(4'(mul_tree_12_153)), .cin(1'b0), .value(mul_tree_12_154));
    assign mul_tree_12_155 = {mul_tree_12_154, 28'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_156 = mul_precision_10[19:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_157 = mul_precision_11[19:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_158Core rtlzz_owner_158(.a(4'(mul_tree_12_156)), .b(4'(mul_tree_12_157)), .cin(1'b0), .value(mul_tree_12_158));
    assign mul_tree_12_159 = {mul_tree_12_158, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_160 = mul_precision_10[19:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_161 = mul_precision_11[23:20]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_162Core rtlzz_owner_162(.a(4'(mul_tree_12_160)), .b(4'(mul_tree_12_161)), .cin(1'b0), .value(mul_tree_12_162));
    assign mul_tree_12_163 = {mul_tree_12_162, 36'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_164 = mul_precision_10[19:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_165 = mul_precision_11[27:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_166Core rtlzz_owner_166(.a(4'(mul_tree_12_164)), .b(4'(mul_tree_12_165)), .cin(1'b0), .value(mul_tree_12_166));
    assign mul_tree_12_167 = {mul_tree_12_166, 40'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_168 = mul_precision_10[19:16]; // decl: <none>; prim: <none>
    assign mul_tree_12_169 = mul_precision_11[31:28]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_170Core rtlzz_owner_170(.a(4'(mul_tree_12_168)), .b(4'(mul_tree_12_169)), .cin(1'b0), .value(mul_tree_12_170));
    assign mul_tree_12_171 = {mul_tree_12_170, 44'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_172 = mul_precision_10[23:20]; // decl: <none>; prim: <none>
    assign mul_tree_12_173 = mul_precision_11[3:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_174Core rtlzz_owner_174(.a(4'(mul_tree_12_172)), .b(4'(mul_tree_12_173)), .cin(1'b0), .value(mul_tree_12_174));
    assign mul_tree_12_175 = {mul_tree_12_174, 20'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_176 = mul_precision_10[23:20]; // decl: <none>; prim: <none>
    assign mul_tree_12_177 = mul_precision_11[7:4]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_178Core rtlzz_owner_178(.a(4'(mul_tree_12_176)), .b(4'(mul_tree_12_177)), .cin(1'b0), .value(mul_tree_12_178));
    assign mul_tree_12_179 = {mul_tree_12_178, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_180 = mul_precision_10[23:20]; // decl: <none>; prim: <none>
    assign mul_tree_12_181 = mul_precision_11[11:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_182Core rtlzz_owner_182(.a(4'(mul_tree_12_180)), .b(4'(mul_tree_12_181)), .cin(1'b0), .value(mul_tree_12_182));
    assign mul_tree_12_183 = {mul_tree_12_182, 28'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_184 = mul_precision_10[23:20]; // decl: <none>; prim: <none>
    assign mul_tree_12_185 = mul_precision_11[15:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_186Core rtlzz_owner_186(.a(4'(mul_tree_12_184)), .b(4'(mul_tree_12_185)), .cin(1'b0), .value(mul_tree_12_186));
    assign mul_tree_12_187 = {mul_tree_12_186, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_188 = mul_precision_10[23:20]; // decl: <none>; prim: <none>
    assign mul_tree_12_189 = mul_precision_11[19:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_190Core rtlzz_owner_190(.a(4'(mul_tree_12_188)), .b(4'(mul_tree_12_189)), .cin(1'b0), .value(mul_tree_12_190));
    assign mul_tree_12_191 = {mul_tree_12_190, 36'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_192 = mul_precision_10[23:20]; // decl: <none>; prim: <none>
    assign mul_tree_12_193 = mul_precision_11[23:20]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_194Core rtlzz_owner_194(.a(4'(mul_tree_12_192)), .b(4'(mul_tree_12_193)), .cin(1'b0), .value(mul_tree_12_194));
    assign mul_tree_12_195 = {mul_tree_12_194, 40'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_196 = mul_precision_10[23:20]; // decl: <none>; prim: <none>
    assign mul_tree_12_197 = mul_precision_11[27:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_198Core rtlzz_owner_198(.a(4'(mul_tree_12_196)), .b(4'(mul_tree_12_197)), .cin(1'b0), .value(mul_tree_12_198));
    assign mul_tree_12_199 = {mul_tree_12_198, 44'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_200 = mul_precision_10[23:20]; // decl: <none>; prim: <none>
    assign mul_tree_12_201 = mul_precision_11[31:28]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_202Core rtlzz_owner_202(.a(4'(mul_tree_12_200)), .b(4'(mul_tree_12_201)), .cin(1'b0), .value(mul_tree_12_202));
    assign mul_tree_12_203 = {mul_tree_12_202, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_204 = mul_precision_10[27:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_205 = mul_precision_11[3:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_206Core rtlzz_owner_206(.a(4'(mul_tree_12_204)), .b(4'(mul_tree_12_205)), .cin(1'b0), .value(mul_tree_12_206));
    assign mul_tree_12_207 = {mul_tree_12_206, 24'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_208 = mul_precision_10[27:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_209 = mul_precision_11[7:4]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_210Core rtlzz_owner_210(.a(4'(mul_tree_12_208)), .b(4'(mul_tree_12_209)), .cin(1'b0), .value(mul_tree_12_210));
    assign mul_tree_12_211 = {mul_tree_12_210, 28'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_212 = mul_precision_10[27:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_213 = mul_precision_11[11:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_214Core rtlzz_owner_214(.a(4'(mul_tree_12_212)), .b(4'(mul_tree_12_213)), .cin(1'b0), .value(mul_tree_12_214));
    assign mul_tree_12_215 = {mul_tree_12_214, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_216 = mul_precision_10[27:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_217 = mul_precision_11[15:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_218Core rtlzz_owner_218(.a(4'(mul_tree_12_216)), .b(4'(mul_tree_12_217)), .cin(1'b0), .value(mul_tree_12_218));
    assign mul_tree_12_219 = {mul_tree_12_218, 36'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_220 = mul_precision_10[27:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_221 = mul_precision_11[19:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_222Core rtlzz_owner_222(.a(4'(mul_tree_12_220)), .b(4'(mul_tree_12_221)), .cin(1'b0), .value(mul_tree_12_222));
    assign mul_tree_12_223 = {mul_tree_12_222, 40'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_224 = mul_precision_10[27:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_225 = mul_precision_11[23:20]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_226Core rtlzz_owner_226(.a(4'(mul_tree_12_224)), .b(4'(mul_tree_12_225)), .cin(1'b0), .value(mul_tree_12_226));
    assign mul_tree_12_227 = {mul_tree_12_226, 44'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_228 = mul_precision_10[27:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_229 = mul_precision_11[27:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_230Core rtlzz_owner_230(.a(4'(mul_tree_12_228)), .b(4'(mul_tree_12_229)), .cin(1'b0), .value(mul_tree_12_230));
    assign mul_tree_12_231 = {mul_tree_12_230, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_232 = mul_precision_10[27:24]; // decl: <none>; prim: <none>
    assign mul_tree_12_233 = mul_precision_11[31:28]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_234Core rtlzz_owner_234(.a(4'(mul_tree_12_232)), .b(4'(mul_tree_12_233)), .cin(1'b0), .value(mul_tree_12_234));
    assign mul_tree_12_235 = {mul_tree_12_234, 52'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_236 = mul_precision_10[31:28]; // decl: <none>; prim: <none>
    assign mul_tree_12_237 = mul_precision_11[3:0]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_238Core rtlzz_owner_238(.a(4'(mul_tree_12_236)), .b(4'(mul_tree_12_237)), .cin(1'b0), .value(mul_tree_12_238));
    assign mul_tree_12_239 = {mul_tree_12_238, 28'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_240 = mul_precision_10[31:28]; // decl: <none>; prim: <none>
    assign mul_tree_12_241 = mul_precision_11[7:4]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_242Core rtlzz_owner_242(.a(4'(mul_tree_12_240)), .b(4'(mul_tree_12_241)), .cin(1'b0), .value(mul_tree_12_242));
    assign mul_tree_12_243 = {mul_tree_12_242, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_244 = mul_precision_10[31:28]; // decl: <none>; prim: <none>
    assign mul_tree_12_245 = mul_precision_11[11:8]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_246Core rtlzz_owner_246(.a(4'(mul_tree_12_244)), .b(4'(mul_tree_12_245)), .cin(1'b0), .value(mul_tree_12_246));
    assign mul_tree_12_247 = {mul_tree_12_246, 36'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_248 = mul_precision_10[31:28]; // decl: <none>; prim: <none>
    assign mul_tree_12_249 = mul_precision_11[15:12]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_250Core rtlzz_owner_250(.a(4'(mul_tree_12_248)), .b(4'(mul_tree_12_249)), .cin(1'b0), .value(mul_tree_12_250));
    assign mul_tree_12_251 = {mul_tree_12_250, 40'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_252 = mul_precision_10[31:28]; // decl: <none>; prim: <none>
    assign mul_tree_12_253 = mul_precision_11[19:16]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_254Core rtlzz_owner_254(.a(4'(mul_tree_12_252)), .b(4'(mul_tree_12_253)), .cin(1'b0), .value(mul_tree_12_254));
    assign mul_tree_12_255 = {mul_tree_12_254, 44'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_256 = mul_precision_10[31:28]; // decl: <none>; prim: <none>
    assign mul_tree_12_257 = mul_precision_11[23:20]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_258Core rtlzz_owner_258(.a(4'(mul_tree_12_256)), .b(4'(mul_tree_12_257)), .cin(1'b0), .value(mul_tree_12_258));
    assign mul_tree_12_259 = {mul_tree_12_258, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_260 = mul_precision_10[31:28]; // decl: <none>; prim: <none>
    assign mul_tree_12_261 = mul_precision_11[27:24]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_262Core rtlzz_owner_262(.a(4'(mul_tree_12_260)), .b(4'(mul_tree_12_261)), .cin(1'b0), .value(mul_tree_12_262));
    assign mul_tree_12_263 = {mul_tree_12_262, 52'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_264 = mul_precision_10[31:28]; // decl: <none>; prim: <none>
    assign mul_tree_12_265 = mul_precision_11[31:28]; // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_266Core rtlzz_owner_266(.a(4'(mul_tree_12_264)), .b(4'(mul_tree_12_265)), .cin(1'b0), .value(mul_tree_12_266));
    assign mul_tree_12_267 = {mul_tree_12_266, 56'h0}; // decl: <none>; prim: <none>
    assign mul_tree_12_268 = ({5'h0, rtlzz_pipe_15_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_269 = ({1'h0, rtlzz_pipe_19_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_271 = ({5'h0, rtlzz_pipe_23_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_272 = ({1'h0, rtlzz_pipe_27_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_274 = ({5'h0, rtlzz_pipe_31_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_275 = ({1'h0, rtlzz_pipe_35_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_277 = ({5'h0, rtlzz_pipe_39_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_278 = ({1'h0, rtlzz_pipe_43_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_280 = ({5'h0, rtlzz_pipe_47_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_281 = ({1'h0, rtlzz_pipe_51_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_283 = ({5'h0, rtlzz_pipe_55_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_284 = ({1'h0, rtlzz_pipe_59_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_286 = ({5'h0, rtlzz_pipe_63_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_287 = ({1'h0, rtlzz_pipe_67_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_289 = ({5'h0, rtlzz_pipe_71_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_290 = ({1'h0, rtlzz_pipe_75_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_292 = ({5'h0, rtlzz_pipe_79_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_293 = ({1'h0, rtlzz_pipe_83_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_295 = ({5'h0, rtlzz_pipe_87_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_296 = ({1'h0, rtlzz_pipe_91_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_298 = ({5'h0, rtlzz_pipe_95_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_299 = ({1'h0, rtlzz_pipe_99_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_301 = ({5'h0, rtlzz_pipe_103_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_302 = ({1'h0, rtlzz_pipe_107_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_304 = ({5'h0, rtlzz_pipe_111_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_305 = ({1'h0, rtlzz_pipe_115_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_307 = ({5'h0, rtlzz_pipe_119_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_308 = ({1'h0, rtlzz_pipe_123_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_310 = ({5'h0, rtlzz_pipe_127_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_311 = ({1'h0, rtlzz_pipe_131_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_313 = ({5'h0, rtlzz_pipe_135_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_314 = ({1'h0, rtlzz_pipe_139_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_316 = ({5'h0, rtlzz_pipe_143_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_317 = ({1'h0, rtlzz_pipe_147_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_319 = ({5'h0, rtlzz_pipe_151_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_320 = ({1'h0, rtlzz_pipe_155_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_322 = ({5'h0, rtlzz_pipe_159_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_323 = ({1'h0, rtlzz_pipe_163_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_325 = ({5'h0, rtlzz_pipe_167_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_326 = ({1'h0, rtlzz_pipe_171_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_328 = ({5'h0, rtlzz_pipe_175_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_329 = ({1'h0, rtlzz_pipe_179_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_331 = ({5'h0, rtlzz_pipe_183_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_332 = ({1'h0, rtlzz_pipe_187_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_334 = ({5'h0, rtlzz_pipe_191_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_335 = ({1'h0, rtlzz_pipe_195_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_337 = ({5'h0, rtlzz_pipe_199_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_338 = ({1'h0, rtlzz_pipe_203_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_340 = ({5'h0, rtlzz_pipe_207_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_341 = ({1'h0, rtlzz_pipe_211_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_343 = ({5'h0, rtlzz_pipe_215_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_344 = ({1'h0, rtlzz_pipe_219_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_346 = ({5'h0, rtlzz_pipe_223_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_347 = ({1'h0, rtlzz_pipe_227_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_349 = ({5'h0, rtlzz_pipe_231_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_350 = ({1'h0, rtlzz_pipe_235_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_352 = ({5'h0, rtlzz_pipe_239_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_353 = ({1'h0, rtlzz_pipe_243_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_355 = ({5'h0, rtlzz_pipe_247_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_356 = ({1'h0, rtlzz_pipe_251_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_358 = ({5'h0, rtlzz_pipe_255_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_359 = ({1'h0, rtlzz_pipe_259_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_361 = ({5'h0, rtlzz_pipe_263_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_362 = ({1'h0, rtlzz_pipe_267_s1}); // decl: <none>; prim: <none>
    assign mul_tree_12_364 = ({9'h0, mul_tree_12_270}); // decl: <none>; prim: <none>
    assign mul_tree_12_365 = ({1'h0, mul_tree_12_273}); // decl: <none>; prim: <none>
    assign mul_tree_12_367 = ({9'h0, mul_tree_12_276}); // decl: <none>; prim: <none>
    assign mul_tree_12_368 = ({1'h0, mul_tree_12_279}); // decl: <none>; prim: <none>
    assign mul_tree_12_370 = ({9'h0, mul_tree_12_282}); // decl: <none>; prim: <none>
    assign mul_tree_12_371 = ({1'h0, mul_tree_12_285}); // decl: <none>; prim: <none>
    assign mul_tree_12_373 = ({9'h0, mul_tree_12_288}); // decl: <none>; prim: <none>
    assign mul_tree_12_374 = ({1'h0, mul_tree_12_291}); // decl: <none>; prim: <none>
    assign mul_tree_12_376 = ({9'h0, mul_tree_12_294}); // decl: <none>; prim: <none>
    assign mul_tree_12_377 = ({1'h0, mul_tree_12_297}); // decl: <none>; prim: <none>
    assign mul_tree_12_379 = ({9'h0, mul_tree_12_300}); // decl: <none>; prim: <none>
    assign mul_tree_12_380 = ({1'h0, mul_tree_12_303}); // decl: <none>; prim: <none>
    assign mul_tree_12_382 = ({9'h0, mul_tree_12_306}); // decl: <none>; prim: <none>
    assign mul_tree_12_383 = ({1'h0, mul_tree_12_309}); // decl: <none>; prim: <none>
    assign mul_tree_12_385 = ({9'h0, mul_tree_12_312}); // decl: <none>; prim: <none>
    assign mul_tree_12_386 = ({1'h0, mul_tree_12_315}); // decl: <none>; prim: <none>
    assign mul_tree_12_388 = ({9'h0, mul_tree_12_318}); // decl: <none>; prim: <none>
    assign mul_tree_12_389 = ({1'h0, mul_tree_12_321}); // decl: <none>; prim: <none>
    assign mul_tree_12_391 = ({9'h0, mul_tree_12_324}); // decl: <none>; prim: <none>
    assign mul_tree_12_392 = ({1'h0, mul_tree_12_327}); // decl: <none>; prim: <none>
    assign mul_tree_12_394 = ({9'h0, mul_tree_12_330}); // decl: <none>; prim: <none>
    assign mul_tree_12_395 = ({1'h0, mul_tree_12_333}); // decl: <none>; prim: <none>
    assign mul_tree_12_397 = ({9'h0, mul_tree_12_336}); // decl: <none>; prim: <none>
    assign mul_tree_12_398 = ({1'h0, mul_tree_12_339}); // decl: <none>; prim: <none>
    assign mul_tree_12_400 = ({9'h0, mul_tree_12_342}); // decl: <none>; prim: <none>
    assign mul_tree_12_401 = ({1'h0, mul_tree_12_345}); // decl: <none>; prim: <none>
    assign mul_tree_12_403 = ({9'h0, mul_tree_12_348}); // decl: <none>; prim: <none>
    assign mul_tree_12_404 = ({1'h0, mul_tree_12_351}); // decl: <none>; prim: <none>
    assign mul_tree_12_406 = ({9'h0, mul_tree_12_354}); // decl: <none>; prim: <none>
    assign mul_tree_12_407 = ({1'h0, mul_tree_12_357}); // decl: <none>; prim: <none>
    assign mul_tree_12_409 = ({9'h0, mul_tree_12_360}); // decl: <none>; prim: <none>
    assign mul_tree_12_410 = ({1'h0, mul_tree_12_363}); // decl: <none>; prim: <none>
    assign mul_tree_12_412 = ({17'h0, mul_tree_12_366}); // decl: <none>; prim: <none>
    assign mul_tree_12_413 = ({1'h0, mul_tree_12_369}); // decl: <none>; prim: <none>
    assign mul_tree_12_415 = ({17'h0, mul_tree_12_372}); // decl: <none>; prim: <none>
    assign mul_tree_12_416 = ({1'h0, mul_tree_12_375}); // decl: <none>; prim: <none>
    assign mul_tree_12_418 = ({17'h0, mul_tree_12_378}); // decl: <none>; prim: <none>
    assign mul_tree_12_419 = ({1'h0, mul_tree_12_381}); // decl: <none>; prim: <none>
    assign mul_tree_12_421 = ({17'h0, mul_tree_12_384}); // decl: <none>; prim: <none>
    assign mul_tree_12_422 = ({1'h0, mul_tree_12_387}); // decl: <none>; prim: <none>
    assign mul_tree_12_424 = ({17'h0, mul_tree_12_390}); // decl: <none>; prim: <none>
    assign mul_tree_12_425 = ({1'h0, mul_tree_12_393}); // decl: <none>; prim: <none>
    assign mul_tree_12_427 = ({17'h0, mul_tree_12_396}); // decl: <none>; prim: <none>
    assign mul_tree_12_428 = ({1'h0, mul_tree_12_399}); // decl: <none>; prim: <none>
    assign mul_tree_12_430 = ({17'h0, mul_tree_12_402}); // decl: <none>; prim: <none>
    assign mul_tree_12_431 = ({1'h0, mul_tree_12_405}); // decl: <none>; prim: <none>
    assign mul_tree_12_433 = ({17'h0, mul_tree_12_408}); // decl: <none>; prim: <none>
    assign mul_tree_12_434 = ({1'h0, mul_tree_12_411}); // decl: <none>; prim: <none>
    assign mul_tree_12_436 = ({5'h0, mul_tree_12_414}); // decl: <none>; prim: <none>
    assign mul_tree_12_437 = ({1'h0, mul_tree_12_417}); // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_438_reduce rtlzz_reduce_438(.i460(rtlzz_pipe_15_s1), .i461(rtlzz_pipe_19_s1), .i462(rtlzz_pipe_23_s1), .i463(rtlzz_pipe_27_s1), .i464(rtlzz_pipe_31_s1), .i465(rtlzz_pipe_35_s1), .i466(rtlzz_pipe_39_s1), .i467(rtlzz_pipe_43_s1), .i468(rtlzz_pipe_47_s1), .i469(rtlzz_pipe_51_s1), .i470(rtlzz_pipe_55_s1), .i471(rtlzz_pipe_59_s1), .i472(rtlzz_pipe_63_s1), .i473(rtlzz_pipe_67_s1), .i474(rtlzz_pipe_71_s1), .i475(rtlzz_pipe_75_s1), .y(mul_tree_12_438));
    assign mul_tree_12_439 = ({5'h0, mul_tree_12_420}); // decl: <none>; prim: <none>
    assign mul_tree_12_440 = ({1'h0, mul_tree_12_423}); // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_441_reduce rtlzz_reduce_441(.i476(rtlzz_pipe_79_s1), .i477(rtlzz_pipe_83_s1), .i478(rtlzz_pipe_87_s1), .i479(rtlzz_pipe_91_s1), .i480(rtlzz_pipe_95_s1), .i481(rtlzz_pipe_99_s1), .i482(rtlzz_pipe_103_s1), .i483(rtlzz_pipe_107_s1), .i484(rtlzz_pipe_111_s1), .i485(rtlzz_pipe_115_s1), .i486(rtlzz_pipe_119_s1), .i487(rtlzz_pipe_123_s1), .i488(rtlzz_pipe_127_s1), .i489(rtlzz_pipe_131_s1), .i490(rtlzz_pipe_135_s1), .i491(rtlzz_pipe_139_s1), .y(mul_tree_12_441));
    assign mul_tree_12_442 = ({5'h0, mul_tree_12_426}); // decl: <none>; prim: <none>
    assign mul_tree_12_443 = ({1'h0, mul_tree_12_429}); // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_444_reduce rtlzz_reduce_444(.i492(rtlzz_pipe_143_s1), .i493(rtlzz_pipe_147_s1), .i494(rtlzz_pipe_151_s1), .i495(rtlzz_pipe_155_s1), .i496(rtlzz_pipe_159_s1), .i497(rtlzz_pipe_163_s1), .i498(rtlzz_pipe_167_s1), .i499(rtlzz_pipe_171_s1), .i500(rtlzz_pipe_175_s1), .i501(rtlzz_pipe_179_s1), .i502(rtlzz_pipe_183_s1), .i503(rtlzz_pipe_187_s1), .i504(rtlzz_pipe_191_s1), .i505(rtlzz_pipe_195_s1), .i506(rtlzz_pipe_199_s1), .i507(rtlzz_pipe_203_s1), .y(mul_tree_12_444));
    assign mul_tree_12_445 = ({5'h0, mul_tree_12_432}); // decl: <none>; prim: <none>
    assign mul_tree_12_446 = ({1'h0, mul_tree_12_435}); // decl: <none>; prim: <none>
    (* keep_hierarchy=1 *) WorkloadCore__rtlzz_arith_447_reduce rtlzz_reduce_447(.i508(rtlzz_pipe_207_s1), .i509(rtlzz_pipe_211_s1), .i510(rtlzz_pipe_215_s1), .i511(rtlzz_pipe_219_s1), .i512(rtlzz_pipe_223_s1), .i513(rtlzz_pipe_227_s1), .i514(rtlzz_pipe_231_s1), .i515(rtlzz_pipe_235_s1), .i516(rtlzz_pipe_239_s1), .i517(rtlzz_pipe_243_s1), .i518(rtlzz_pipe_247_s1), .i519(rtlzz_pipe_251_s1), .i520(rtlzz_pipe_255_s1), .i521(rtlzz_pipe_259_s1), .i522(rtlzz_pipe_263_s1), .i523(rtlzz_pipe_267_s1), .y(mul_tree_12_447));
    assign mul_tree_12_448 = ({9'h0, rtlzz_pipe_438_s2}); // decl: <none>; prim: <none>
    assign mul_tree_12_449 = ({1'h0, rtlzz_pipe_441_s2}); // decl: <none>; prim: <none>
    assign mul_tree_12_451 = ({9'h0, rtlzz_pipe_444_s2}); // decl: <none>; prim: <none>
    assign mul_tree_12_452 = ({1'h0, rtlzz_pipe_447_s2}); // decl: <none>; prim: <none>
    assign mul_tree_12_454 = ({17'h0, mul_tree_12_450}); // decl: <none>; prim: <none>
    assign mul_tree_12_455 = ({1'h0, mul_tree_12_453}); // decl: <none>; prim: <none>
    assign mul_tree_12_457 = mul_tree_12_456[63:0]; // decl: <none>; prim: <none>
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_2_s1 <= 64'h0;
            rtlzz_pipe_2_s2 <= 64'h0;
            rtlzz_pipe_15_s1 <= 8'h0;
            rtlzz_pipe_19_s1 <= 12'h0;
            rtlzz_pipe_23_s1 <= 16'h0;
            rtlzz_pipe_27_s1 <= 20'h0;
            rtlzz_pipe_31_s1 <= 24'h0;
            rtlzz_pipe_35_s1 <= 28'h0;
            rtlzz_pipe_39_s1 <= 32'h0;
            rtlzz_pipe_43_s1 <= 36'h0;
            rtlzz_pipe_47_s1 <= 12'h0;
            rtlzz_pipe_51_s1 <= 16'h0;
            rtlzz_pipe_55_s1 <= 20'h0;
            rtlzz_pipe_59_s1 <= 24'h0;
            rtlzz_pipe_63_s1 <= 28'h0;
            rtlzz_pipe_67_s1 <= 32'h0;
            rtlzz_pipe_71_s1 <= 36'h0;
            rtlzz_pipe_75_s1 <= 40'h0;
            rtlzz_pipe_79_s1 <= 16'h0;
            rtlzz_pipe_83_s1 <= 20'h0;
            rtlzz_pipe_87_s1 <= 24'h0;
            rtlzz_pipe_91_s1 <= 28'h0;
            rtlzz_pipe_95_s1 <= 32'h0;
            rtlzz_pipe_99_s1 <= 36'h0;
            rtlzz_pipe_103_s1 <= 40'h0;
            rtlzz_pipe_107_s1 <= 44'h0;
            rtlzz_pipe_111_s1 <= 20'h0;
            rtlzz_pipe_115_s1 <= 24'h0;
            rtlzz_pipe_119_s1 <= 28'h0;
            rtlzz_pipe_123_s1 <= 32'h0;
            rtlzz_pipe_127_s1 <= 36'h0;
            rtlzz_pipe_131_s1 <= 40'h0;
            rtlzz_pipe_135_s1 <= 44'h0;
            rtlzz_pipe_139_s1 <= 48'h0;
            rtlzz_pipe_143_s1 <= 24'h0;
            rtlzz_pipe_147_s1 <= 28'h0;
            rtlzz_pipe_151_s1 <= 32'h0;
            rtlzz_pipe_155_s1 <= 36'h0;
            rtlzz_pipe_159_s1 <= 40'h0;
            rtlzz_pipe_163_s1 <= 44'h0;
            rtlzz_pipe_167_s1 <= 48'h0;
            rtlzz_pipe_171_s1 <= 52'h0;
            rtlzz_pipe_175_s1 <= 28'h0;
            rtlzz_pipe_179_s1 <= 32'h0;
            rtlzz_pipe_183_s1 <= 36'h0;
            rtlzz_pipe_187_s1 <= 40'h0;
            rtlzz_pipe_191_s1 <= 44'h0;
            rtlzz_pipe_195_s1 <= 48'h0;
            rtlzz_pipe_199_s1 <= 52'h0;
            rtlzz_pipe_203_s1 <= 56'h0;
            rtlzz_pipe_207_s1 <= 32'h0;
            rtlzz_pipe_211_s1 <= 36'h0;
            rtlzz_pipe_215_s1 <= 40'h0;
            rtlzz_pipe_219_s1 <= 44'h0;
            rtlzz_pipe_223_s1 <= 48'h0;
            rtlzz_pipe_227_s1 <= 52'h0;
            rtlzz_pipe_231_s1 <= 56'h0;
            rtlzz_pipe_235_s1 <= 60'h0;
            rtlzz_pipe_239_s1 <= 36'h0;
            rtlzz_pipe_243_s1 <= 40'h0;
            rtlzz_pipe_247_s1 <= 44'h0;
            rtlzz_pipe_251_s1 <= 48'h0;
            rtlzz_pipe_255_s1 <= 52'h0;
            rtlzz_pipe_259_s1 <= 56'h0;
            rtlzz_pipe_263_s1 <= 60'h0;
            rtlzz_pipe_267_s1 <= 64'h0;
            rtlzz_pipe_438_s2 <= 44'h0;
            rtlzz_pipe_441_s2 <= 52'h0;
            rtlzz_pipe_444_s2 <= 60'h0;
            rtlzz_pipe_447_s2 <= 68'h0;
            rtlzz_valid_s1 <= 1'h0;
            rtlzz_valid_s2 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_2_s1 <= c; // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_2_s2 <= rtlzz_pipe_2_s1; // decl: /home/zyrv/vulsim/workload.cpp:7:1-7:10; prim: /home/zyrv/vulsim/workload.cpp:7:1-7:10
        end
        if (iv) begin
        rtlzz_pipe_15_s1 <= mul_tree_12_15; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_19_s1 <= mul_tree_12_19; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_23_s1 <= mul_tree_12_23; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_27_s1 <= mul_tree_12_27; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_31_s1 <= mul_tree_12_31; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_35_s1 <= mul_tree_12_35; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_39_s1 <= mul_tree_12_39; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_43_s1 <= mul_tree_12_43; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_47_s1 <= mul_tree_12_47; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_51_s1 <= mul_tree_12_51; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_55_s1 <= mul_tree_12_55; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_59_s1 <= mul_tree_12_59; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_63_s1 <= mul_tree_12_63; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_67_s1 <= mul_tree_12_67; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_71_s1 <= mul_tree_12_71; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_75_s1 <= mul_tree_12_75; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_79_s1 <= mul_tree_12_79; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_83_s1 <= mul_tree_12_83; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_87_s1 <= mul_tree_12_87; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_91_s1 <= mul_tree_12_91; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_95_s1 <= mul_tree_12_95; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_99_s1 <= mul_tree_12_99; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_103_s1 <= mul_tree_12_103; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_107_s1 <= mul_tree_12_107; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_111_s1 <= mul_tree_12_111; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_115_s1 <= mul_tree_12_115; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_119_s1 <= mul_tree_12_119; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_123_s1 <= mul_tree_12_123; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_127_s1 <= mul_tree_12_127; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_131_s1 <= mul_tree_12_131; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_135_s1 <= mul_tree_12_135; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_139_s1 <= mul_tree_12_139; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_143_s1 <= mul_tree_12_143; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_147_s1 <= mul_tree_12_147; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_151_s1 <= mul_tree_12_151; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_155_s1 <= mul_tree_12_155; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_159_s1 <= mul_tree_12_159; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_163_s1 <= mul_tree_12_163; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_167_s1 <= mul_tree_12_167; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_171_s1 <= mul_tree_12_171; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_175_s1 <= mul_tree_12_175; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_179_s1 <= mul_tree_12_179; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_183_s1 <= mul_tree_12_183; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_187_s1 <= mul_tree_12_187; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_191_s1 <= mul_tree_12_191; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_195_s1 <= mul_tree_12_195; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_199_s1 <= mul_tree_12_199; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_203_s1 <= mul_tree_12_203; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_207_s1 <= mul_tree_12_207; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_211_s1 <= mul_tree_12_211; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_215_s1 <= mul_tree_12_215; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_219_s1 <= mul_tree_12_219; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_223_s1 <= mul_tree_12_223; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_227_s1 <= mul_tree_12_227; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_231_s1 <= mul_tree_12_231; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_235_s1 <= mul_tree_12_235; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_239_s1 <= mul_tree_12_239; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_243_s1 <= mul_tree_12_243; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_247_s1 <= mul_tree_12_247; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_251_s1 <= mul_tree_12_251; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_255_s1 <= mul_tree_12_255; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_259_s1 <= mul_tree_12_259; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_263_s1 <= mul_tree_12_263; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_267_s1 <= mul_tree_12_267; // decl: <none>; prim: <none>
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_438_s2 <= mul_tree_12_438; // decl: <none>; prim: <none>
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_441_s2 <= mul_tree_12_441; // decl: <none>; prim: <none>
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_444_s2 <= mul_tree_12_444; // decl: <none>; prim: <none>
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_447_s2 <= mul_tree_12_447; // decl: <none>; prim: <none>
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8
        rtlzz_valid_s2 <= rtlzz_valid_s1; // decl: /home/zyrv/vulsim/workload.cpp:9:1-9:8; prim: /home/zyrv/vulsim/workload.cpp:9:1-9:8
        end
    end
endmodule

(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_5_reduce(input wire [63:0] i459, input wire [43:0] i524, input wire [51:0] i525, input wire [59:0] i526, input wire [67:0] i527, output wire [63:0] y);
wire [63:0] t0 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i524[43], i524[42], i524[41], i524[40], i524[39], i524[38], i524[37], i524[36], i524[35], i524[34], i524[33], i524[32], i524[31], i524[30], i524[29], i524[28], i524[27], i524[26], i524[25], i524[24], i524[23], i524[22], i524[21], i524[20], i524[19], i524[18], i524[17], i524[16], i524[15], i524[14], i524[13], i524[12], i524[11], i524[10], i524[9], i524[8], i524[7], i524[6], i524[5], i524[4], i524[3], i524[2], i524[1], i524[0]};
wire [63:0] t1 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i525[51], i525[50], i525[49], i525[48], i525[47], i525[46], i525[45], i525[44], i525[43], i525[42], i525[41], i525[40], i525[39], i525[38], i525[37], i525[36], i525[35], i525[34], i525[33], i525[32], i525[31], i525[30], i525[29], i525[28], i525[27], i525[26], i525[25], i525[24], i525[23], i525[22], i525[21], i525[20], i525[19], i525[18], i525[17], i525[16], i525[15], i525[14], i525[13], i525[12], i525[11], i525[10], i525[9], i525[8], i525[7], i525[6], i525[5], i525[4], i525[3], i525[2], i525[1], i525[0]};
wire [63:0] t2 = {1'b0, 1'b0, 1'b0, 1'b0, i526[59], i526[58], i526[57], i526[56], i526[55], i526[54], i526[53], i526[52], i526[51], i526[50], i526[49], i526[48], i526[47], i526[46], i526[45], i526[44], i526[43], i526[42], i526[41], i526[40], i526[39], i526[38], i526[37], i526[36], i526[35], i526[34], i526[33], i526[32], i526[31], i526[30], i526[29], i526[28], i526[27], i526[26], i526[25], i526[24], i526[23], i526[22], i526[21], i526[20], i526[19], i526[18], i526[17], i526[16], i526[15], i526[14], i526[13], i526[12], i526[11], i526[10], i526[9], i526[8], i526[7], i526[6], i526[5], i526[4], i526[3], i526[2], i526[1], i526[0]};
wire [63:0] t3 = {i527[63], i527[62], i527[61], i527[60], i527[59], i527[58], i527[57], i527[56], i527[55], i527[54], i527[53], i527[52], i527[51], i527[50], i527[49], i527[48], i527[47], i527[46], i527[45], i527[44], i527[43], i527[42], i527[41], i527[40], i527[39], i527[38], i527[37], i527[36], i527[35], i527[34], i527[33], i527[32], i527[31], i527[30], i527[29], i527[28], i527[27], i527[26], i527[25], i527[24], i527[23], i527[22], i527[21], i527[20], i527[19], i527[18], i527[17], i527[16], i527[15], i527[14], i527[13], i527[12], i527[11], i527[10], i527[9], i527[8], i527[7], i527[6], i527[5], i527[4], i527[3], i527[2], i527[1], i527[0]};
wire [63:0] t4 = {i459[63], i459[62], i459[61], i459[60], i459[59], i459[58], i459[57], i459[56], i459[55], i459[54], i459[53], i459[52], i459[51], i459[50], i459[49], i459[48], i459[47], i459[46], i459[45], i459[44], i459[43], i459[42], i459[41], i459[40], i459[39], i459[38], i459[37], i459[36], i459[35], i459[34], i459[33], i459[32], i459[31], i459[30], i459[29], i459[28], i459[27], i459[26], i459[25], i459[24], i459[23], i459[22], i459[21], i459[20], i459[19], i459[18], i459[17], i459[16], i459[15], i459[14], i459[13], i459[12], i459[11], i459[10], i459[9], i459[8], i459[7], i459[6], i459[5], i459[4], i459[3], i459[2], i459[1], i459[0]};
wire [63:0] sum = t0 + t1 + t2 + t3 + t4;
assign y=sum;
endmodule

(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_438_reduce(input wire [7:0] i460, input wire [11:0] i461, input wire [15:0] i462, input wire [19:0] i463, input wire [23:0] i464, input wire [27:0] i465, input wire [31:0] i466, input wire [35:0] i467, input wire [11:0] i468, input wire [15:0] i469, input wire [19:0] i470, input wire [23:0] i471, input wire [27:0] i472, input wire [31:0] i473, input wire [35:0] i474, input wire [39:0] i475, output wire [43:0] y);
wire [43:0] t0 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i460[7], i460[6], i460[5], i460[4], i460[3], i460[2], i460[1], i460[0]};
wire [43:0] t1 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i461[11], i461[10], i461[9], i461[8], i461[7], i461[6], i461[5], i461[4], 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t2 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i462[15], i462[14], i462[13], i462[12], i462[11], i462[10], i462[9], i462[8], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t3 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i463[19], i463[18], i463[17], i463[16], i463[15], i463[14], i463[13], i463[12], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t4 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i464[23], i464[22], i464[21], i464[20], i464[19], i464[18], i464[17], i464[16], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t5 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i465[27], i465[26], i465[25], i465[24], i465[23], i465[22], i465[21], i465[20], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t6 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i466[31], i466[30], i466[29], i466[28], i466[27], i466[26], i466[25], i466[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t7 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i467[35], i467[34], i467[33], i467[32], i467[31], i467[30], i467[29], i467[28], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t8 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i468[11], i468[10], i468[9], i468[8], i468[7], i468[6], i468[5], i468[4], 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t9 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i469[15], i469[14], i469[13], i469[12], i469[11], i469[10], i469[9], i469[8], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t10 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i470[19], i470[18], i470[17], i470[16], i470[15], i470[14], i470[13], i470[12], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t11 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i471[23], i471[22], i471[21], i471[20], i471[19], i471[18], i471[17], i471[16], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t12 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i472[27], i472[26], i472[25], i472[24], i472[23], i472[22], i472[21], i472[20], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t13 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i473[31], i473[30], i473[29], i473[28], i473[27], i473[26], i473[25], i473[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t14 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i474[35], i474[34], i474[33], i474[32], i474[31], i474[30], i474[29], i474[28], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] t15 = {1'b0, 1'b0, 1'b0, 1'b0, i475[39], i475[38], i475[37], i475[36], i475[35], i475[34], i475[33], i475[32], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [43:0] sum = t0 + t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8 + t9 + t10 + t11 + t12 + t13 + t14 + t15;
assign y=sum;
endmodule

(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_441_reduce(input wire [15:0] i476, input wire [19:0] i477, input wire [23:0] i478, input wire [27:0] i479, input wire [31:0] i480, input wire [35:0] i481, input wire [39:0] i482, input wire [43:0] i483, input wire [19:0] i484, input wire [23:0] i485, input wire [27:0] i486, input wire [31:0] i487, input wire [35:0] i488, input wire [39:0] i489, input wire [43:0] i490, input wire [47:0] i491, output wire [51:0] y);
wire [51:0] t0 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i476[15], i476[14], i476[13], i476[12], i476[11], i476[10], i476[9], i476[8], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t1 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i477[19], i477[18], i477[17], i477[16], i477[15], i477[14], i477[13], i477[12], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t2 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i478[23], i478[22], i478[21], i478[20], i478[19], i478[18], i478[17], i478[16], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t3 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i479[27], i479[26], i479[25], i479[24], i479[23], i479[22], i479[21], i479[20], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t4 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i480[31], i480[30], i480[29], i480[28], i480[27], i480[26], i480[25], i480[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t5 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i481[35], i481[34], i481[33], i481[32], i481[31], i481[30], i481[29], i481[28], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t6 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i482[39], i482[38], i482[37], i482[36], i482[35], i482[34], i482[33], i482[32], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t7 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i483[43], i483[42], i483[41], i483[40], i483[39], i483[38], i483[37], i483[36], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t8 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i484[19], i484[18], i484[17], i484[16], i484[15], i484[14], i484[13], i484[12], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t9 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i485[23], i485[22], i485[21], i485[20], i485[19], i485[18], i485[17], i485[16], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t10 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i486[27], i486[26], i486[25], i486[24], i486[23], i486[22], i486[21], i486[20], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t11 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i487[31], i487[30], i487[29], i487[28], i487[27], i487[26], i487[25], i487[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t12 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i488[35], i488[34], i488[33], i488[32], i488[31], i488[30], i488[29], i488[28], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t13 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i489[39], i489[38], i489[37], i489[36], i489[35], i489[34], i489[33], i489[32], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t14 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i490[43], i490[42], i490[41], i490[40], i490[39], i490[38], i490[37], i490[36], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] t15 = {1'b0, 1'b0, 1'b0, 1'b0, i491[47], i491[46], i491[45], i491[44], i491[43], i491[42], i491[41], i491[40], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [51:0] sum = t0 + t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8 + t9 + t10 + t11 + t12 + t13 + t14 + t15;
assign y=sum;
endmodule

(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_444_reduce(input wire [23:0] i492, input wire [27:0] i493, input wire [31:0] i494, input wire [35:0] i495, input wire [39:0] i496, input wire [43:0] i497, input wire [47:0] i498, input wire [51:0] i499, input wire [27:0] i500, input wire [31:0] i501, input wire [35:0] i502, input wire [39:0] i503, input wire [43:0] i504, input wire [47:0] i505, input wire [51:0] i506, input wire [55:0] i507, output wire [59:0] y);
wire [59:0] t0 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i492[23], i492[22], i492[21], i492[20], i492[19], i492[18], i492[17], i492[16], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t1 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i493[27], i493[26], i493[25], i493[24], i493[23], i493[22], i493[21], i493[20], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t2 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i494[31], i494[30], i494[29], i494[28], i494[27], i494[26], i494[25], i494[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t3 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i495[35], i495[34], i495[33], i495[32], i495[31], i495[30], i495[29], i495[28], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t4 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i496[39], i496[38], i496[37], i496[36], i496[35], i496[34], i496[33], i496[32], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t5 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i497[43], i497[42], i497[41], i497[40], i497[39], i497[38], i497[37], i497[36], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t6 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i498[47], i498[46], i498[45], i498[44], i498[43], i498[42], i498[41], i498[40], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t7 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i499[51], i499[50], i499[49], i499[48], i499[47], i499[46], i499[45], i499[44], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t8 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i500[27], i500[26], i500[25], i500[24], i500[23], i500[22], i500[21], i500[20], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t9 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i501[31], i501[30], i501[29], i501[28], i501[27], i501[26], i501[25], i501[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t10 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i502[35], i502[34], i502[33], i502[32], i502[31], i502[30], i502[29], i502[28], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t11 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i503[39], i503[38], i503[37], i503[36], i503[35], i503[34], i503[33], i503[32], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t12 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i504[43], i504[42], i504[41], i504[40], i504[39], i504[38], i504[37], i504[36], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t13 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i505[47], i505[46], i505[45], i505[44], i505[43], i505[42], i505[41], i505[40], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t14 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i506[51], i506[50], i506[49], i506[48], i506[47], i506[46], i506[45], i506[44], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] t15 = {1'b0, 1'b0, 1'b0, 1'b0, i507[55], i507[54], i507[53], i507[52], i507[51], i507[50], i507[49], i507[48], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [59:0] sum = t0 + t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8 + t9 + t10 + t11 + t12 + t13 + t14 + t15;
assign y=sum;
endmodule

(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_447_reduce(input wire [31:0] i508, input wire [35:0] i509, input wire [39:0] i510, input wire [43:0] i511, input wire [47:0] i512, input wire [51:0] i513, input wire [55:0] i514, input wire [59:0] i515, input wire [35:0] i516, input wire [39:0] i517, input wire [43:0] i518, input wire [47:0] i519, input wire [51:0] i520, input wire [55:0] i521, input wire [59:0] i522, input wire [63:0] i523, output wire [67:0] y);
wire [63:0] t0 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i508[31], i508[30], i508[29], i508[28], i508[27], i508[26], i508[25], i508[24], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t1 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i509[35], i509[34], i509[33], i509[32], i509[31], i509[30], i509[29], i509[28], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t2 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i510[39], i510[38], i510[37], i510[36], i510[35], i510[34], i510[33], i510[32], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t3 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i511[43], i511[42], i511[41], i511[40], i511[39], i511[38], i511[37], i511[36], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t4 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i512[47], i512[46], i512[45], i512[44], i512[43], i512[42], i512[41], i512[40], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t5 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i513[51], i513[50], i513[49], i513[48], i513[47], i513[46], i513[45], i513[44], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t6 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i514[55], i514[54], i514[53], i514[52], i514[51], i514[50], i514[49], i514[48], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t7 = {1'b0, 1'b0, 1'b0, 1'b0, i515[59], i515[58], i515[57], i515[56], i515[55], i515[54], i515[53], i515[52], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t8 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i516[35], i516[34], i516[33], i516[32], i516[31], i516[30], i516[29], i516[28], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t9 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i517[39], i517[38], i517[37], i517[36], i517[35], i517[34], i517[33], i517[32], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t10 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i518[43], i518[42], i518[41], i518[40], i518[39], i518[38], i518[37], i518[36], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t11 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i519[47], i519[46], i519[45], i519[44], i519[43], i519[42], i519[41], i519[40], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t12 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i520[51], i520[50], i520[49], i520[48], i520[47], i520[46], i520[45], i520[44], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t13 = {1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i521[55], i521[54], i521[53], i521[52], i521[51], i521[50], i521[49], i521[48], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t14 = {1'b0, 1'b0, 1'b0, 1'b0, i522[59], i522[58], i522[57], i522[56], i522[55], i522[54], i522[53], i522[52], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] t15 = {i523[63], i523[62], i523[61], i523[60], i523[59], i523[58], i523[57], i523[56], 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
wire [63:0] sum = t0 + t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8 + t9 + t10 + t11 + t12 + t13 + t14 + t15;
assign y=sum;
endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_15Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_15();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_18Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_18();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_22Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_22();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_26Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_26();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_30Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_30();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_34Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_34();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_38Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_38();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_42Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_42();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_46Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_46();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_50Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_50();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_54Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_54();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_58Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_58();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_62Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_62();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_66Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_66();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_70Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_70();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_74Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_74();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_78Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_78();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_82Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_82();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_86Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_86();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_90Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_90();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_94Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_94();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_98Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_98();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_102Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_102();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_106Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_106();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_110Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_110();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_114Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_114();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_118Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_118();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_122Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_122();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_126Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_126();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_130Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_130();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_134Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_134();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_138Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_138();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_142Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_142();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_146Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_146();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_150Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_150();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_154Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_154();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_158Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_158();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_162Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_162();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_166Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_166();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_170Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_170();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_174Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_174();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_178Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_178();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_182Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_182();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_186Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_186();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_190Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_190();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_194Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_194();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_198Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_198();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_202Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_202();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_206Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_206();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_210Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_210();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_214Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_214();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_218Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_218();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_222Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_222();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_226Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_226();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_230Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_230();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_234Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_234();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_238Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_238();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_242Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_242();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_246Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_246();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_250Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_250();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_254Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_254();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_258Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_258();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_262Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_262();endmodule
// unsigned-wide-family-hierarchy-v1
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_266Core(input wire [3:0] a,input wire [3:0] b,input wire cin,output wire [7:0] value);
wire [3:0] masked_a=((a&4'hf)|4'h0);
wire [3:0] masked_b=((b&4'hf)|4'h0);
wire [7:0] aa=8'(masked_a);
wire [7:0] bb=8'(masked_b);
wire [7:0] native_value=aa*bb;
assign value=native_value[0+:8];
endmodule
(* keep_hierarchy=1 *) module WorkloadCore__rtlzz_arith_266();endmodule

module Workload(input wire clk,input wire rstn,input wire iv_data,input wire iv_wen,output reg ov,input wire [31:0] a_data,input wire a_wen,input wire [31:0] b_data,input wire b_wen,input wire [63:0] c_data,input wire c_wen,output reg [63:0] y);
reg liv;wire cov;
reg [31:0] l_a;
reg [31:0] l_b;
reg [63:0] l_c;
wire [63:0] c_y;
WorkloadCore core(.iv(liv),.ov(cov),.clk(clk),.rstn(rstn),.a(l_a),.b(l_b),.c(l_c),.y(c_y));
always @(posedge clk)if(!rstn)begin liv<=1'b0;ov<=1'b0;l_a<=32'h0;l_b<=32'h0;l_c<=64'h0;y<=64'h0;end else begin if(iv_wen)liv<=iv_data;ov<=cov;if(a_wen)l_a<=a_data;if(b_wen)l_b<=b_data;if(c_wen)l_c<=c_data;y<=c_y;end
endmodule
