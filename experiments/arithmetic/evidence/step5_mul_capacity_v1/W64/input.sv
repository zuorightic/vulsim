`timescale 1ns/1ps

module w64_full_3(
    input logic [63:0] a, // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:10; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:10
    input logic [63:0] b, // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:12; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:12
    input logic [63:0] c, // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:14; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:14
    input logic iv, // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:23; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:23
    output logic ov, // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:26; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:26
    output logic [127:0] y, // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:28-2:38; prim: /home/zyrv/vulsim/mul-template.logic.cpp:10:19-10:24
    output logic [127:0] z, // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:28-2:40; prim: /home/zyrv/vulsim/mul-template.logic.cpp:10:25-10:30
    input logic rstn, // decl: <none>; prim: <none>
    input logic clk // decl: <none>; prim: <none>
);

    logic [127:0] s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:10:21-10:24; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:12
    logic [127:0] s8_norm_mul_1_v0; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:10:27-10:30; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:14
    logic [63:0] __beopt_width_12; // decl: <none>; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:10
    logic [63:0] __beopt_width_13; // decl: <none>; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:12
    logic [63:0] __beopt_width_17; // decl: <none>; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:14
    logic [127:0] __beopt_width_14; // decl: <none>; prim: <none>
    logic [127:0] __beopt_width_15; // decl: <none>; prim: <none>
    logic [127:0] __beopt_width_18; // decl: <none>; prim: <none>
    logic [127:0] arith_original_15; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:10:21-10:24; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:12
    logic [127:0] arith_original_16; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:10:27-10:30; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:14
    logic [15:0] mul_tree_15_17; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_18; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_19; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_20; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_21; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_22; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_15_23; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_24; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_25; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_26; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_15_27; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_28; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_29; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_30; // decl: <none>; prim: <none>
    logic [79:0] mul_tree_15_31; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_32; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_33; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_34; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_15_35; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_36; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_37; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_38; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_15_39; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_40; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_41; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_42; // decl: <none>; prim: <none>
    logic [79:0] mul_tree_15_43; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_44; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_45; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_46; // decl: <none>; prim: <none>
    logic [95:0] mul_tree_15_47; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_48; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_49; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_50; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_15_51; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_52; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_53; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_54; // decl: <none>; prim: <none>
    logic [79:0] mul_tree_15_55; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_56; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_57; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_58; // decl: <none>; prim: <none>
    logic [95:0] mul_tree_15_59; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_60; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_61; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_62; // decl: <none>; prim: <none>
    logic [111:0] mul_tree_15_63; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_64; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_65; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_66; // decl: <none>; prim: <none>
    logic [79:0] mul_tree_15_67; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_68; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_69; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_70; // decl: <none>; prim: <none>
    logic [95:0] mul_tree_15_71; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_72; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_73; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_74; // decl: <none>; prim: <none>
    logic [111:0] mul_tree_15_75; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_76; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_15_77; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_15_78; // decl: <none>; prim: <none>
    logic [127:0] mul_tree_15_79; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_15_80; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_15_81; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_15_82; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_15_83; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_15_84; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_15_85; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_15_86; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_15_87; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_15_88; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_15_89; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_15_90; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_15_91; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_15_92; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_15_93; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_15_94; // decl: <none>; prim: <none>
    logic [112:0] mul_tree_15_95; // decl: <none>; prim: <none>
    logic [112:0] mul_tree_15_96; // decl: <none>; prim: <none>
    logic [112:0] mul_tree_15_97; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_15_98; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_15_99; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_15_100; // decl: <none>; prim: <none>
    logic [128:0] mul_tree_15_101; // decl: <none>; prim: <none>
    logic [128:0] mul_tree_15_102; // decl: <none>; prim: <none>
    logic [128:0] mul_tree_15_103; // decl: <none>; prim: <none>
    logic [81:0] mul_tree_15_104; // decl: <none>; prim: <none>
    logic [81:0] mul_tree_15_105; // decl: <none>; prim: <none>
    logic [81:0] mul_tree_15_106; // decl: <none>; prim: <none>
    logic [97:0] mul_tree_15_107; // decl: <none>; prim: <none>
    logic [97:0] mul_tree_15_108; // decl: <none>; prim: <none>
    logic [97:0] mul_tree_15_109; // decl: <none>; prim: <none>
    logic [113:0] mul_tree_15_110; // decl: <none>; prim: <none>
    logic [113:0] mul_tree_15_111; // decl: <none>; prim: <none>
    logic [113:0] mul_tree_15_112; // decl: <none>; prim: <none>
    logic [129:0] mul_tree_15_113; // decl: <none>; prim: <none>
    logic [129:0] mul_tree_15_114; // decl: <none>; prim: <none>
    logic [129:0] mul_tree_15_115; // decl: <none>; prim: <none>
    logic [98:0] mul_tree_15_116; // decl: <none>; prim: <none>
    logic [98:0] mul_tree_15_117; // decl: <none>; prim: <none>
    logic [98:0] mul_tree_15_118; // decl: <none>; prim: <none>
    logic [130:0] mul_tree_15_119; // decl: <none>; prim: <none>
    logic [130:0] mul_tree_15_120; // decl: <none>; prim: <none>
    logic [130:0] mul_tree_15_121; // decl: <none>; prim: <none>
    logic [131:0] mul_tree_15_122; // decl: <none>; prim: <none>
    logic [131:0] mul_tree_15_123; // decl: <none>; prim: <none>
    logic [131:0] mul_tree_15_124; // decl: <none>; prim: <none>
    logic [127:0] mul_tree_15_125; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_126; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_127; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_128; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_129; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_130; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_131; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_16_132; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_133; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_134; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_135; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_16_136; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_137; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_138; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_139; // decl: <none>; prim: <none>
    logic [79:0] mul_tree_16_140; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_141; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_142; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_143; // decl: <none>; prim: <none>
    logic [47:0] mul_tree_16_144; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_145; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_146; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_147; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_16_148; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_149; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_150; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_151; // decl: <none>; prim: <none>
    logic [79:0] mul_tree_16_152; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_153; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_154; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_155; // decl: <none>; prim: <none>
    logic [95:0] mul_tree_16_156; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_157; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_158; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_159; // decl: <none>; prim: <none>
    logic [63:0] mul_tree_16_160; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_161; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_162; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_163; // decl: <none>; prim: <none>
    logic [79:0] mul_tree_16_164; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_165; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_166; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_167; // decl: <none>; prim: <none>
    logic [95:0] mul_tree_16_168; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_169; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_170; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_171; // decl: <none>; prim: <none>
    logic [111:0] mul_tree_16_172; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_173; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_174; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_175; // decl: <none>; prim: <none>
    logic [79:0] mul_tree_16_176; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_177; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_178; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_179; // decl: <none>; prim: <none>
    logic [95:0] mul_tree_16_180; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_181; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_182; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_183; // decl: <none>; prim: <none>
    logic [111:0] mul_tree_16_184; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_185; // decl: <none>; prim: <none>
    logic [15:0] mul_tree_16_186; // decl: <none>; prim: <none>
    logic [31:0] mul_tree_16_187; // decl: <none>; prim: <none>
    logic [127:0] mul_tree_16_188; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_16_189; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_16_190; // decl: <none>; prim: <none>
    logic [48:0] mul_tree_16_191; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_16_192; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_16_193; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_16_194; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_16_195; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_16_196; // decl: <none>; prim: <none>
    logic [64:0] mul_tree_16_197; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_16_198; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_16_199; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_16_200; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_16_201; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_16_202; // decl: <none>; prim: <none>
    logic [80:0] mul_tree_16_203; // decl: <none>; prim: <none>
    logic [112:0] mul_tree_16_204; // decl: <none>; prim: <none>
    logic [112:0] mul_tree_16_205; // decl: <none>; prim: <none>
    logic [112:0] mul_tree_16_206; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_16_207; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_16_208; // decl: <none>; prim: <none>
    logic [96:0] mul_tree_16_209; // decl: <none>; prim: <none>
    logic [128:0] mul_tree_16_210; // decl: <none>; prim: <none>
    logic [128:0] mul_tree_16_211; // decl: <none>; prim: <none>
    logic [128:0] mul_tree_16_212; // decl: <none>; prim: <none>
    logic [81:0] mul_tree_16_213; // decl: <none>; prim: <none>
    logic [81:0] mul_tree_16_214; // decl: <none>; prim: <none>
    logic [81:0] mul_tree_16_215; // decl: <none>; prim: <none>
    logic [97:0] mul_tree_16_216; // decl: <none>; prim: <none>
    logic [97:0] mul_tree_16_217; // decl: <none>; prim: <none>
    logic [97:0] mul_tree_16_218; // decl: <none>; prim: <none>
    logic [113:0] mul_tree_16_219; // decl: <none>; prim: <none>
    logic [113:0] mul_tree_16_220; // decl: <none>; prim: <none>
    logic [113:0] mul_tree_16_221; // decl: <none>; prim: <none>
    logic [129:0] mul_tree_16_222; // decl: <none>; prim: <none>
    logic [129:0] mul_tree_16_223; // decl: <none>; prim: <none>
    logic [129:0] mul_tree_16_224; // decl: <none>; prim: <none>
    logic [98:0] mul_tree_16_225; // decl: <none>; prim: <none>
    logic [98:0] mul_tree_16_226; // decl: <none>; prim: <none>
    logic [98:0] mul_tree_16_227; // decl: <none>; prim: <none>
    logic [130:0] mul_tree_16_228; // decl: <none>; prim: <none>
    logic [130:0] mul_tree_16_229; // decl: <none>; prim: <none>
    logic [130:0] mul_tree_16_230; // decl: <none>; prim: <none>
    logic [131:0] mul_tree_16_231; // decl: <none>; prim: <none>
    logic [131:0] mul_tree_16_232; // decl: <none>; prim: <none>
    logic [131:0] mul_tree_16_233; // decl: <none>; prim: <none>
    logic [127:0] mul_tree_16_234; // decl: <none>; prim: <none>
    logic [31:0] rtlzz_pipe_19_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_23_s1; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_27_s1; // decl: <none>; prim: <none>
    logic [79:0] rtlzz_pipe_31_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_35_s1; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_39_s1; // decl: <none>; prim: <none>
    logic [79:0] rtlzz_pipe_43_s1; // decl: <none>; prim: <none>
    logic [95:0] rtlzz_pipe_47_s1; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_51_s1; // decl: <none>; prim: <none>
    logic [79:0] rtlzz_pipe_55_s1; // decl: <none>; prim: <none>
    logic [95:0] rtlzz_pipe_59_s1; // decl: <none>; prim: <none>
    logic [111:0] rtlzz_pipe_63_s1; // decl: <none>; prim: <none>
    logic [79:0] rtlzz_pipe_67_s1; // decl: <none>; prim: <none>
    logic [95:0] rtlzz_pipe_71_s1; // decl: <none>; prim: <none>
    logic [111:0] rtlzz_pipe_75_s1; // decl: <none>; prim: <none>
    logic [127:0] rtlzz_pipe_79_s1; // decl: <none>; prim: <none>
    logic [127:0] rtlzz_pipe_4_s2; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:10:21-10:24; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:12
    logic [31:0] rtlzz_pipe_128_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_132_s1; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_136_s1; // decl: <none>; prim: <none>
    logic [79:0] rtlzz_pipe_140_s1; // decl: <none>; prim: <none>
    logic [47:0] rtlzz_pipe_144_s1; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_148_s1; // decl: <none>; prim: <none>
    logic [79:0] rtlzz_pipe_152_s1; // decl: <none>; prim: <none>
    logic [95:0] rtlzz_pipe_156_s1; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_160_s1; // decl: <none>; prim: <none>
    logic [79:0] rtlzz_pipe_164_s1; // decl: <none>; prim: <none>
    logic [95:0] rtlzz_pipe_168_s1; // decl: <none>; prim: <none>
    logic [111:0] rtlzz_pipe_172_s1; // decl: <none>; prim: <none>
    logic [79:0] rtlzz_pipe_176_s1; // decl: <none>; prim: <none>
    logic [95:0] rtlzz_pipe_180_s1; // decl: <none>; prim: <none>
    logic [111:0] rtlzz_pipe_184_s1; // decl: <none>; prim: <none>
    logic [127:0] rtlzz_pipe_188_s1; // decl: <none>; prim: <none>
    logic [127:0] rtlzz_pipe_5_s2; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:10:27-10:30; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:14
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:23; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:23
    logic rtlzz_valid_s2; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:23; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:23


    assign s8_norm_mul_0_v0 = arith_original_15; // decl: <none>; prim: <none>
    assign s8_norm_mul_1_v0 = arith_original_16; // decl: <none>; prim: <none>
    assign ov = rtlzz_valid_s2; // decl: <none>; prim: <none>
    assign y = rtlzz_pipe_4_s2; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:28-2:38; prim: /home/zyrv/vulsim/mul-template.logic.cpp:10:19-10:24
    assign z = rtlzz_pipe_5_s2; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:28-2:40; prim: /home/zyrv/vulsim/mul-template.logic.cpp:10:25-10:30
    assign __beopt_width_12 = a; // decl: <none>; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:10
    assign __beopt_width_13 = b; // decl: <none>; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:12
    assign __beopt_width_17 = c; // decl: <none>; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:14
    assign __beopt_width_14 = ({64'h0, __beopt_width_12}); // decl: <none>; prim: <none>
    assign __beopt_width_15 = ({64'h0, __beopt_width_13}); // decl: <none>; prim: <none>
    assign __beopt_width_18 = ({64'h0, __beopt_width_17}); // decl: <none>; prim: <none>
    assign arith_original_15 = mul_tree_15_125; // decl: <none>; prim: <none>
    assign arith_original_16 = mul_tree_16_234; // decl: <none>; prim: <none>
    assign mul_tree_15_17 = __beopt_width_14[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_15_18 = __beopt_width_15[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_15_19 = 32'(($unsigned(32'($unsigned(mul_tree_15_17))) * $unsigned(32'($unsigned(mul_tree_15_18))))); // decl: <none>; prim: <none>
    assign mul_tree_15_20 = __beopt_width_14[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_15_21 = __beopt_width_15[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_15_22 = 32'(($unsigned(32'($unsigned(mul_tree_15_20))) * $unsigned(32'($unsigned(mul_tree_15_21))))); // decl: <none>; prim: <none>
    assign mul_tree_15_23 = {mul_tree_15_22, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_24 = __beopt_width_14[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_15_25 = __beopt_width_15[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_15_26 = 32'(($unsigned(32'($unsigned(mul_tree_15_24))) * $unsigned(32'($unsigned(mul_tree_15_25))))); // decl: <none>; prim: <none>
    assign mul_tree_15_27 = {mul_tree_15_26, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_28 = __beopt_width_14[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_15_29 = __beopt_width_15[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_15_30 = 32'(($unsigned(32'($unsigned(mul_tree_15_28))) * $unsigned(32'($unsigned(mul_tree_15_29))))); // decl: <none>; prim: <none>
    assign mul_tree_15_31 = {mul_tree_15_30, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_32 = __beopt_width_14[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_15_33 = __beopt_width_15[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_15_34 = 32'(($unsigned(32'($unsigned(mul_tree_15_32))) * $unsigned(32'($unsigned(mul_tree_15_33))))); // decl: <none>; prim: <none>
    assign mul_tree_15_35 = {mul_tree_15_34, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_36 = __beopt_width_14[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_15_37 = __beopt_width_15[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_15_38 = 32'(($unsigned(32'($unsigned(mul_tree_15_36))) * $unsigned(32'($unsigned(mul_tree_15_37))))); // decl: <none>; prim: <none>
    assign mul_tree_15_39 = {mul_tree_15_38, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_40 = __beopt_width_14[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_15_41 = __beopt_width_15[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_15_42 = 32'(($unsigned(32'($unsigned(mul_tree_15_40))) * $unsigned(32'($unsigned(mul_tree_15_41))))); // decl: <none>; prim: <none>
    assign mul_tree_15_43 = {mul_tree_15_42, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_44 = __beopt_width_14[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_15_45 = __beopt_width_15[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_15_46 = 32'(($unsigned(32'($unsigned(mul_tree_15_44))) * $unsigned(32'($unsigned(mul_tree_15_45))))); // decl: <none>; prim: <none>
    assign mul_tree_15_47 = {mul_tree_15_46, 64'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_48 = __beopt_width_14[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_15_49 = __beopt_width_15[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_15_50 = 32'(($unsigned(32'($unsigned(mul_tree_15_48))) * $unsigned(32'($unsigned(mul_tree_15_49))))); // decl: <none>; prim: <none>
    assign mul_tree_15_51 = {mul_tree_15_50, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_52 = __beopt_width_14[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_15_53 = __beopt_width_15[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_15_54 = 32'(($unsigned(32'($unsigned(mul_tree_15_52))) * $unsigned(32'($unsigned(mul_tree_15_53))))); // decl: <none>; prim: <none>
    assign mul_tree_15_55 = {mul_tree_15_54, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_56 = __beopt_width_14[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_15_57 = __beopt_width_15[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_15_58 = 32'(($unsigned(32'($unsigned(mul_tree_15_56))) * $unsigned(32'($unsigned(mul_tree_15_57))))); // decl: <none>; prim: <none>
    assign mul_tree_15_59 = {mul_tree_15_58, 64'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_60 = __beopt_width_14[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_15_61 = __beopt_width_15[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_15_62 = 32'(($unsigned(32'($unsigned(mul_tree_15_60))) * $unsigned(32'($unsigned(mul_tree_15_61))))); // decl: <none>; prim: <none>
    assign mul_tree_15_63 = {mul_tree_15_62, 80'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_64 = __beopt_width_14[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_15_65 = __beopt_width_15[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_15_66 = 32'(($unsigned(32'($unsigned(mul_tree_15_64))) * $unsigned(32'($unsigned(mul_tree_15_65))))); // decl: <none>; prim: <none>
    assign mul_tree_15_67 = {mul_tree_15_66, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_68 = __beopt_width_14[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_15_69 = __beopt_width_15[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_15_70 = 32'(($unsigned(32'($unsigned(mul_tree_15_68))) * $unsigned(32'($unsigned(mul_tree_15_69))))); // decl: <none>; prim: <none>
    assign mul_tree_15_71 = {mul_tree_15_70, 64'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_72 = __beopt_width_14[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_15_73 = __beopt_width_15[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_15_74 = 32'(($unsigned(32'($unsigned(mul_tree_15_72))) * $unsigned(32'($unsigned(mul_tree_15_73))))); // decl: <none>; prim: <none>
    assign mul_tree_15_75 = {mul_tree_15_74, 80'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_76 = __beopt_width_14[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_15_77 = __beopt_width_15[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_15_78 = 32'(($unsigned(32'($unsigned(mul_tree_15_76))) * $unsigned(32'($unsigned(mul_tree_15_77))))); // decl: <none>; prim: <none>
    assign mul_tree_15_79 = {mul_tree_15_78, 96'h0}; // decl: <none>; prim: <none>
    assign mul_tree_15_80 = ({17'h0, rtlzz_pipe_19_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_81 = ({1'h0, rtlzz_pipe_23_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_82 = 49'((mul_tree_15_80 + mul_tree_15_81 + ({48'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_83 = ({17'h0, rtlzz_pipe_27_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_84 = ({1'h0, rtlzz_pipe_31_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_85 = 81'((mul_tree_15_83 + mul_tree_15_84 + ({80'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_86 = ({17'h0, rtlzz_pipe_35_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_87 = ({1'h0, rtlzz_pipe_39_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_88 = 65'((mul_tree_15_86 + mul_tree_15_87 + ({64'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_89 = ({17'h0, rtlzz_pipe_43_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_90 = ({1'h0, rtlzz_pipe_47_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_91 = 97'((mul_tree_15_89 + mul_tree_15_90 + ({96'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_92 = ({17'h0, rtlzz_pipe_51_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_93 = ({1'h0, rtlzz_pipe_55_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_94 = 81'((mul_tree_15_92 + mul_tree_15_93 + ({80'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_95 = ({17'h0, rtlzz_pipe_59_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_96 = ({1'h0, rtlzz_pipe_63_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_97 = 113'((mul_tree_15_95 + mul_tree_15_96 + ({112'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_98 = ({17'h0, rtlzz_pipe_67_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_99 = ({1'h0, rtlzz_pipe_71_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_100 = 97'((mul_tree_15_98 + mul_tree_15_99 + ({96'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_101 = ({17'h0, rtlzz_pipe_75_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_102 = ({1'h0, rtlzz_pipe_79_s1}); // decl: <none>; prim: <none>
    assign mul_tree_15_103 = 129'((mul_tree_15_101 + mul_tree_15_102 + ({128'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_104 = ({33'h0, mul_tree_15_82}); // decl: <none>; prim: <none>
    assign mul_tree_15_105 = ({1'h0, mul_tree_15_85}); // decl: <none>; prim: <none>
    assign mul_tree_15_106 = 82'((mul_tree_15_104 + mul_tree_15_105 + ({81'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_107 = ({33'h0, mul_tree_15_88}); // decl: <none>; prim: <none>
    assign mul_tree_15_108 = ({1'h0, mul_tree_15_91}); // decl: <none>; prim: <none>
    assign mul_tree_15_109 = 98'((mul_tree_15_107 + mul_tree_15_108 + ({97'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_110 = ({33'h0, mul_tree_15_94}); // decl: <none>; prim: <none>
    assign mul_tree_15_111 = ({1'h0, mul_tree_15_97}); // decl: <none>; prim: <none>
    assign mul_tree_15_112 = 114'((mul_tree_15_110 + mul_tree_15_111 + ({113'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_113 = ({33'h0, mul_tree_15_100}); // decl: <none>; prim: <none>
    assign mul_tree_15_114 = ({1'h0, mul_tree_15_103}); // decl: <none>; prim: <none>
    assign mul_tree_15_115 = 130'((mul_tree_15_113 + mul_tree_15_114 + ({129'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_116 = ({17'h0, mul_tree_15_106}); // decl: <none>; prim: <none>
    assign mul_tree_15_117 = ({1'h0, mul_tree_15_109}); // decl: <none>; prim: <none>
    assign mul_tree_15_118 = 99'((mul_tree_15_116 + mul_tree_15_117 + ({98'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_119 = ({17'h0, mul_tree_15_112}); // decl: <none>; prim: <none>
    assign mul_tree_15_120 = ({1'h0, mul_tree_15_115}); // decl: <none>; prim: <none>
    assign mul_tree_15_121 = 131'((mul_tree_15_119 + mul_tree_15_120 + ({130'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_122 = ({33'h0, mul_tree_15_118}); // decl: <none>; prim: <none>
    assign mul_tree_15_123 = ({1'h0, mul_tree_15_121}); // decl: <none>; prim: <none>
    assign mul_tree_15_124 = 132'((mul_tree_15_122 + mul_tree_15_123 + ({131'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_15_125 = mul_tree_15_124[127:0]; // decl: <none>; prim: <none>
    assign mul_tree_16_126 = __beopt_width_14[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_16_127 = __beopt_width_18[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_16_128 = 32'(($unsigned(32'($unsigned(mul_tree_16_126))) * $unsigned(32'($unsigned(mul_tree_16_127))))); // decl: <none>; prim: <none>
    assign mul_tree_16_129 = __beopt_width_14[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_16_130 = __beopt_width_18[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_16_131 = 32'(($unsigned(32'($unsigned(mul_tree_16_129))) * $unsigned(32'($unsigned(mul_tree_16_130))))); // decl: <none>; prim: <none>
    assign mul_tree_16_132 = {mul_tree_16_131, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_133 = __beopt_width_14[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_16_134 = __beopt_width_18[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_16_135 = 32'(($unsigned(32'($unsigned(mul_tree_16_133))) * $unsigned(32'($unsigned(mul_tree_16_134))))); // decl: <none>; prim: <none>
    assign mul_tree_16_136 = {mul_tree_16_135, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_137 = __beopt_width_14[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_16_138 = __beopt_width_18[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_16_139 = 32'(($unsigned(32'($unsigned(mul_tree_16_137))) * $unsigned(32'($unsigned(mul_tree_16_138))))); // decl: <none>; prim: <none>
    assign mul_tree_16_140 = {mul_tree_16_139, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_141 = __beopt_width_14[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_16_142 = __beopt_width_18[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_16_143 = 32'(($unsigned(32'($unsigned(mul_tree_16_141))) * $unsigned(32'($unsigned(mul_tree_16_142))))); // decl: <none>; prim: <none>
    assign mul_tree_16_144 = {mul_tree_16_143, 16'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_145 = __beopt_width_14[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_16_146 = __beopt_width_18[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_16_147 = 32'(($unsigned(32'($unsigned(mul_tree_16_145))) * $unsigned(32'($unsigned(mul_tree_16_146))))); // decl: <none>; prim: <none>
    assign mul_tree_16_148 = {mul_tree_16_147, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_149 = __beopt_width_14[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_16_150 = __beopt_width_18[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_16_151 = 32'(($unsigned(32'($unsigned(mul_tree_16_149))) * $unsigned(32'($unsigned(mul_tree_16_150))))); // decl: <none>; prim: <none>
    assign mul_tree_16_152 = {mul_tree_16_151, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_153 = __beopt_width_14[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_16_154 = __beopt_width_18[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_16_155 = 32'(($unsigned(32'($unsigned(mul_tree_16_153))) * $unsigned(32'($unsigned(mul_tree_16_154))))); // decl: <none>; prim: <none>
    assign mul_tree_16_156 = {mul_tree_16_155, 64'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_157 = __beopt_width_14[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_16_158 = __beopt_width_18[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_16_159 = 32'(($unsigned(32'($unsigned(mul_tree_16_157))) * $unsigned(32'($unsigned(mul_tree_16_158))))); // decl: <none>; prim: <none>
    assign mul_tree_16_160 = {mul_tree_16_159, 32'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_161 = __beopt_width_14[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_16_162 = __beopt_width_18[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_16_163 = 32'(($unsigned(32'($unsigned(mul_tree_16_161))) * $unsigned(32'($unsigned(mul_tree_16_162))))); // decl: <none>; prim: <none>
    assign mul_tree_16_164 = {mul_tree_16_163, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_165 = __beopt_width_14[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_16_166 = __beopt_width_18[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_16_167 = 32'(($unsigned(32'($unsigned(mul_tree_16_165))) * $unsigned(32'($unsigned(mul_tree_16_166))))); // decl: <none>; prim: <none>
    assign mul_tree_16_168 = {mul_tree_16_167, 64'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_169 = __beopt_width_14[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_16_170 = __beopt_width_18[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_16_171 = 32'(($unsigned(32'($unsigned(mul_tree_16_169))) * $unsigned(32'($unsigned(mul_tree_16_170))))); // decl: <none>; prim: <none>
    assign mul_tree_16_172 = {mul_tree_16_171, 80'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_173 = __beopt_width_14[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_16_174 = __beopt_width_18[15:0]; // decl: <none>; prim: <none>
    assign mul_tree_16_175 = 32'(($unsigned(32'($unsigned(mul_tree_16_173))) * $unsigned(32'($unsigned(mul_tree_16_174))))); // decl: <none>; prim: <none>
    assign mul_tree_16_176 = {mul_tree_16_175, 48'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_177 = __beopt_width_14[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_16_178 = __beopt_width_18[31:16]; // decl: <none>; prim: <none>
    assign mul_tree_16_179 = 32'(($unsigned(32'($unsigned(mul_tree_16_177))) * $unsigned(32'($unsigned(mul_tree_16_178))))); // decl: <none>; prim: <none>
    assign mul_tree_16_180 = {mul_tree_16_179, 64'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_181 = __beopt_width_14[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_16_182 = __beopt_width_18[47:32]; // decl: <none>; prim: <none>
    assign mul_tree_16_183 = 32'(($unsigned(32'($unsigned(mul_tree_16_181))) * $unsigned(32'($unsigned(mul_tree_16_182))))); // decl: <none>; prim: <none>
    assign mul_tree_16_184 = {mul_tree_16_183, 80'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_185 = __beopt_width_14[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_16_186 = __beopt_width_18[63:48]; // decl: <none>; prim: <none>
    assign mul_tree_16_187 = 32'(($unsigned(32'($unsigned(mul_tree_16_185))) * $unsigned(32'($unsigned(mul_tree_16_186))))); // decl: <none>; prim: <none>
    assign mul_tree_16_188 = {mul_tree_16_187, 96'h0}; // decl: <none>; prim: <none>
    assign mul_tree_16_189 = ({17'h0, rtlzz_pipe_128_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_190 = ({1'h0, rtlzz_pipe_132_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_191 = 49'((mul_tree_16_189 + mul_tree_16_190 + ({48'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_192 = ({17'h0, rtlzz_pipe_136_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_193 = ({1'h0, rtlzz_pipe_140_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_194 = 81'((mul_tree_16_192 + mul_tree_16_193 + ({80'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_195 = ({17'h0, rtlzz_pipe_144_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_196 = ({1'h0, rtlzz_pipe_148_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_197 = 65'((mul_tree_16_195 + mul_tree_16_196 + ({64'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_198 = ({17'h0, rtlzz_pipe_152_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_199 = ({1'h0, rtlzz_pipe_156_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_200 = 97'((mul_tree_16_198 + mul_tree_16_199 + ({96'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_201 = ({17'h0, rtlzz_pipe_160_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_202 = ({1'h0, rtlzz_pipe_164_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_203 = 81'((mul_tree_16_201 + mul_tree_16_202 + ({80'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_204 = ({17'h0, rtlzz_pipe_168_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_205 = ({1'h0, rtlzz_pipe_172_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_206 = 113'((mul_tree_16_204 + mul_tree_16_205 + ({112'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_207 = ({17'h0, rtlzz_pipe_176_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_208 = ({1'h0, rtlzz_pipe_180_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_209 = 97'((mul_tree_16_207 + mul_tree_16_208 + ({96'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_210 = ({17'h0, rtlzz_pipe_184_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_211 = ({1'h0, rtlzz_pipe_188_s1}); // decl: <none>; prim: <none>
    assign mul_tree_16_212 = 129'((mul_tree_16_210 + mul_tree_16_211 + ({128'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_213 = ({33'h0, mul_tree_16_191}); // decl: <none>; prim: <none>
    assign mul_tree_16_214 = ({1'h0, mul_tree_16_194}); // decl: <none>; prim: <none>
    assign mul_tree_16_215 = 82'((mul_tree_16_213 + mul_tree_16_214 + ({81'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_216 = ({33'h0, mul_tree_16_197}); // decl: <none>; prim: <none>
    assign mul_tree_16_217 = ({1'h0, mul_tree_16_200}); // decl: <none>; prim: <none>
    assign mul_tree_16_218 = 98'((mul_tree_16_216 + mul_tree_16_217 + ({97'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_219 = ({33'h0, mul_tree_16_203}); // decl: <none>; prim: <none>
    assign mul_tree_16_220 = ({1'h0, mul_tree_16_206}); // decl: <none>; prim: <none>
    assign mul_tree_16_221 = 114'((mul_tree_16_219 + mul_tree_16_220 + ({113'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_222 = ({33'h0, mul_tree_16_209}); // decl: <none>; prim: <none>
    assign mul_tree_16_223 = ({1'h0, mul_tree_16_212}); // decl: <none>; prim: <none>
    assign mul_tree_16_224 = 130'((mul_tree_16_222 + mul_tree_16_223 + ({129'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_225 = ({17'h0, mul_tree_16_215}); // decl: <none>; prim: <none>
    assign mul_tree_16_226 = ({1'h0, mul_tree_16_218}); // decl: <none>; prim: <none>
    assign mul_tree_16_227 = 99'((mul_tree_16_225 + mul_tree_16_226 + ({98'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_228 = ({17'h0, mul_tree_16_221}); // decl: <none>; prim: <none>
    assign mul_tree_16_229 = ({1'h0, mul_tree_16_224}); // decl: <none>; prim: <none>
    assign mul_tree_16_230 = 131'((mul_tree_16_228 + mul_tree_16_229 + ({130'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_231 = ({33'h0, mul_tree_16_227}); // decl: <none>; prim: <none>
    assign mul_tree_16_232 = ({1'h0, mul_tree_16_230}); // decl: <none>; prim: <none>
    assign mul_tree_16_233 = 132'((mul_tree_16_231 + mul_tree_16_232 + ({131'h0, 1'h0}))); // decl: <none>; prim: <none>
    assign mul_tree_16_234 = mul_tree_16_233[127:0]; // decl: <none>; prim: <none>
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_19_s1 <= 32'h23;
            rtlzz_pipe_23_s1 <= 48'h0;
            rtlzz_pipe_27_s1 <= 64'h0;
            rtlzz_pipe_31_s1 <= 80'h0;
            rtlzz_pipe_35_s1 <= 48'h0;
            rtlzz_pipe_39_s1 <= 64'h0;
            rtlzz_pipe_43_s1 <= 80'h0;
            rtlzz_pipe_47_s1 <= 96'h0;
            rtlzz_pipe_51_s1 <= 64'h0;
            rtlzz_pipe_55_s1 <= 80'h0;
            rtlzz_pipe_59_s1 <= 96'h0;
            rtlzz_pipe_63_s1 <= 112'h0;
            rtlzz_pipe_67_s1 <= 80'h0;
            rtlzz_pipe_71_s1 <= 96'h0;
            rtlzz_pipe_75_s1 <= 112'h0;
            rtlzz_pipe_79_s1 <= 128'h0;
            rtlzz_pipe_4_s2 <= 128'h23;
            rtlzz_pipe_128_s1 <= 32'h37;
            rtlzz_pipe_132_s1 <= 48'h0;
            rtlzz_pipe_136_s1 <= 64'h0;
            rtlzz_pipe_140_s1 <= 80'h0;
            rtlzz_pipe_144_s1 <= 48'h0;
            rtlzz_pipe_148_s1 <= 64'h0;
            rtlzz_pipe_152_s1 <= 80'h0;
            rtlzz_pipe_156_s1 <= 96'h0;
            rtlzz_pipe_160_s1 <= 64'h0;
            rtlzz_pipe_164_s1 <= 80'h0;
            rtlzz_pipe_168_s1 <= 96'h0;
            rtlzz_pipe_172_s1 <= 112'h0;
            rtlzz_pipe_176_s1 <= 80'h0;
            rtlzz_pipe_180_s1 <= 96'h0;
            rtlzz_pipe_184_s1 <= 112'h0;
            rtlzz_pipe_188_s1 <= 128'h0;
            rtlzz_pipe_5_s2 <= 128'h37;
            rtlzz_valid_s1 <= 1'h0;
            rtlzz_valid_s2 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_19_s1 <= mul_tree_15_19; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_23_s1 <= mul_tree_15_23; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_27_s1 <= mul_tree_15_27; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_31_s1 <= mul_tree_15_31; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_35_s1 <= mul_tree_15_35; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_39_s1 <= mul_tree_15_39; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_43_s1 <= mul_tree_15_43; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_47_s1 <= mul_tree_15_47; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_51_s1 <= mul_tree_15_51; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_55_s1 <= mul_tree_15_55; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_59_s1 <= mul_tree_15_59; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_63_s1 <= mul_tree_15_63; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_67_s1 <= mul_tree_15_67; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_71_s1 <= mul_tree_15_71; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_75_s1 <= mul_tree_15_75; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_79_s1 <= mul_tree_15_79; // decl: <none>; prim: <none>
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_4_s2 <= s8_norm_mul_0_v0; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:10:21-10:24; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:12
        end
        if (iv) begin
        rtlzz_pipe_128_s1 <= mul_tree_16_128; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_132_s1 <= mul_tree_16_132; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_136_s1 <= mul_tree_16_136; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_140_s1 <= mul_tree_16_140; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_144_s1 <= mul_tree_16_144; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_148_s1 <= mul_tree_16_148; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_152_s1 <= mul_tree_16_152; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_156_s1 <= mul_tree_16_156; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_160_s1 <= mul_tree_16_160; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_164_s1 <= mul_tree_16_164; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_168_s1 <= mul_tree_16_168; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_172_s1 <= mul_tree_16_172; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_176_s1 <= mul_tree_16_176; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_180_s1 <= mul_tree_16_180; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_184_s1 <= mul_tree_16_184; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_188_s1 <= mul_tree_16_188; // decl: <none>; prim: <none>
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_5_s2 <= s8_norm_mul_1_v0; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:10:27-10:30; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:1-2:14
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:23; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:23
        rtlzz_valid_s2 <= rtlzz_valid_s1; // decl: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:23; prim: /home/zyrv/vulsim/mul-template.logic.cpp:2:16-2:23
        end
    end
endmodule
