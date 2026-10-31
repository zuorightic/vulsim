`timescale 1ns/1ps

module top(
    input logic [31:0] a, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    input logic [31:0] b, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    input logic [31:0] c, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:14; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:14
    output logic [36:0] y, // decl: <none>; prim: <none>
    output logic [36:0] z, // decl: <none>; prim: <none>
    output logic [63:0] m, // decl: <none>; prim: <none>
    input logic iv, // decl: /home/zyrv/vulsim/interface.logic.cpp:2:37-2:44; prim: /home/zyrv/vulsim/interface.logic.cpp:2:37-2:44
    output logic ov, // decl: <none>; prim: <none>
    input logic rstn, // decl: <none>; prim: <none>
    input logic clk // decl: <none>; prim: <none>
);

    logic [36:0] arith_4_335; // decl: <none>; prim: <none>
    logic [36:0] arith_5_335; // decl: <none>; prim: <none>
    logic [63:0] arith_opt_917; // decl: /home/zyrv/vulsim/interface.logic.cpp:12:38-12:41; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    logic [31:0] arith_opt_918; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    logic [31:0] arith_opt_919; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    logic [63:0] arith_opt_920; // decl: <none>; prim: <none>
    logic [63:0] arith_opt_921; // decl: <none>; prim: <none>
    logic [31:0] arith_opt_922; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:27-44:32; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:27-44:32
    logic arith_opt_923; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:63-6:64
    logic [7:0] arith_opt_924; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:10
    logic [7:0] arith_opt_925; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:12
    logic [22:0] arith_opt_926; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28
    logic [22:0] arith_opt_927; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45
    logic arith_opt_928; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:16-47:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:24-45:31
    logic arith_opt_929; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:39-47:55; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    logic arith_opt_930; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:15-47:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:15-47:56
    logic arith_opt_931; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:16-48:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:46-45:53
    logic arith_opt_932; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:39-48:55; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    logic arith_opt_933; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:15-48:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:15-48:56
    logic [22:0] arith_opt_934; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:49:24-49:46; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    logic arith_opt_935; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:49:23-49:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28
    logic [22:0] arith_opt_936; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:50:24-50:46; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    logic arith_opt_937; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:50:23-50:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45
    logic arith_opt_938; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:51:16-51:55; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:63-6:64
    logic arith_opt_939; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:52:16-52:55; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:65-6:66
    logic arith_opt_940; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:9-54:24; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:24-45:31
    logic [23:0] arith_opt_941; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:31-54:53; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:5-46:46
    logic [23:0] arith_opt_942; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:31-54:53
    logic arith_opt_943; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:9-55:24; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:46-45:53
    logic [23:0] arith_opt_944; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:31-55:53; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:5-46:46
    logic [23:0] arith_opt_945; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:31-55:53
    logic arith_opt_946; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_947; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [23:0] arith_opt_948; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic arith_opt_949; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_950; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_951; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [23:0] arith_opt_952; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic arith_opt_953; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_954; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_955; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [1:0] arith_opt_956; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_957; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [1:0] arith_opt_958; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_959; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_960; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [1:0] arith_opt_961; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_962; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [1:0] arith_opt_963; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_964; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_965; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [2:0] arith_opt_966; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_967; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [2:0] arith_opt_968; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_969; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_970; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [2:0] arith_opt_971; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_972; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [2:0] arith_opt_973; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_974; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_975; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [3:0] arith_opt_976; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_977; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [3:0] arith_opt_978; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_979; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_980; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [3:0] arith_opt_981; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_982; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [3:0] arith_opt_983; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_984; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_985; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [4:0] arith_opt_986; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_987; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [4:0] arith_opt_988; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_989; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_990; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [4:0] arith_opt_991; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_992; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [4:0] arith_opt_993; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_994; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_995; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [5:0] arith_opt_996; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_997; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [5:0] arith_opt_998; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_999; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1000; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [5:0] arith_opt_1001; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_1002; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [5:0] arith_opt_1003; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1004; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1005; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [6:0] arith_opt_1006; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_1007; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [6:0] arith_opt_1008; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_1009; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1010; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [6:0] arith_opt_1011; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_1012; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [6:0] arith_opt_1013; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1014; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1015; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1016; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_1017; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1018; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_1019; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1020; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1021; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_1022; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1023; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1024; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1025; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1026; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1027; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1028; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1029; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1030; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1031; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1032; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1033; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1034; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1035; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1036; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1037; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1038; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1039; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1040; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1041; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1042; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1043; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1044; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1045; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1046; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1047; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1048; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1049; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1050; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1051; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1052; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1053; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1054; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1055; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1056; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1057; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1058; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1059; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1060; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1061; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1062; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1063; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1064; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1065; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1066; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1067; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1068; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1069; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1070; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1071; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1072; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1073; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1074; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1075; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1076; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1077; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1078; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1079; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1080; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1081; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1082; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1083; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1084; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1085; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1086; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1087; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1088; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1089; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1090; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1091; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1092; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1093; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1094; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1095; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1096; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1097; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1098; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1099; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1100; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1101; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1102; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1103; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1104; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1105; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1106; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1107; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1108; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1109; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1110; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1111; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1112; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1113; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1114; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1115; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1116; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1117; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1118; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1119; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1120; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1121; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1122; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1123; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1124; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1125; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1126; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1127; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1128; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1129; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1130; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1131; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1132; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1133; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1134; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1135; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1136; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1137; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1138; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1139; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1140; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1141; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1142; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1143; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1144; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1145; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1146; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1147; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1148; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1149; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1150; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1151; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1152; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1153; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1154; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1155; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1156; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1157; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1158; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1159; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1160; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1161; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1162; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1163; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1164; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1165; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1166; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1167; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1168; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1169; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1170; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1171; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1172; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1173; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic [7:0] arith_opt_1174; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:58; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:17-45:32
    logic [10:0] arith_opt_1175; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:41
    logic [11:0] arith_opt_1176; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:18-62:88; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:58
    logic [7:0] arith_opt_1177; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:58; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:39-45:54
    logic [10:0] arith_opt_1178; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:41
    logic [11:0] arith_opt_1179; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:18-63:88; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:58
    logic [11:0] arith_opt_1180; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25
    logic [11:0] arith_opt_1181; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:40; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:18-62:88
    logic [47:0] arith_opt_1182; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    logic [30:0] arith_opt_1183; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    logic arith_opt_1184; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:67:9-67:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    logic [30:0] arith_opt_1185; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:27-66:40
    logic [30:0] arith_opt_1186; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:67:59-67:75
    logic arith_opt_1187; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:9-68:34; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:15-68:34
    logic [31:0] arith_opt_1188; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52
    logic [11:0] arith_opt_1189; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:59-68:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25
    logic [11:0] arith_opt_1190; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:5-64:41; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:5-64:41
    logic [31:0] arith_opt_1191; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52
    logic arith_opt_1192; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:71:9-71:26; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:71:14-71:26
    logic arith_opt_1193; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:22-72:39; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:27-72:39
    logic arith_opt_1194; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:21-72:85; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:21-72:85
    logic [31:0] arith_opt_1195; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:62; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:62
    logic arith_opt_1196; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:84; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:84
    logic arith_opt_1197; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:21-85:38; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:26-85:38
    logic arith_opt_1198; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81
    logic arith_opt_1199; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:15-86:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:21-86:33
    logic arith_opt_1200; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:14-86:80; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:14-86:80
    logic arith_opt_1201; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81
    logic [11:0] arith_opt_1202; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:37
    logic arith_opt_1203; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:37
    logic arith_opt_1204; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:36; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:36
    logic arith_opt_1205; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:39-75:49
    logic [31:0] arith_opt_1206; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:29-77:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:29-77:48
    logic [31:0] arith_opt_1207; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:28-77:62; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:28-77:62
    logic [31:0] arith_opt_1208; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:25-78:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:25-78:35
    logic arith_opt_1209; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:24-78:50; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:24-78:50
    logic [31:0] arith_opt_1210; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:79:19-79:31; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:79:19-79:31
    logic [31:0] arith_opt_1211; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:80:28-80:44; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:80:28-80:44
    logic [31:0] arith_opt_1212; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42
    logic [31:0] arith_opt_1213; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:62
    logic arith_opt_1214; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:22-83:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:46-83:56
    logic [1:0] arith_opt_1215; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:67-83:84
    logic [8:0] arith_opt_1216; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:54-68:74
    logic [31:0] arith_opt_1217; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42
    logic [1:0] arith_opt_1218; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:13-83:57
    logic [6:0] arith_opt_1219; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:88:24-88:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:88:24-88:35
    logic [31:0] arith_opt_1220; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41
    logic [24:0] arith_opt_1221; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:30-89:41
    logic arith_opt_1222; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:9-90:31; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:22-90:31
    logic [1:0] arith_opt_1223; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:20-69:29
    logic [1:0] arith_opt_1224; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:41-90:58
    logic arith_opt_1225; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:9-91:32; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:22-91:32
    logic [24:0] arith_opt_1226; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41
    logic [24:0] arith_opt_1227; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:44-91:73
    logic [8:0] arith_opt_1228; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:82:9-82:26
    logic arith_opt_1229; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:93:9-93:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:34-91:73
    logic [8:0] arith_opt_1230; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:93:42-93:52
    logic [31:0] arith_opt_1231; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:23-94:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:19-44:40
    logic [31:0] arith_opt_1232; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61
    logic [31:0] arith_opt_1233; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:47-94:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61
    logic [31:0] arith_opt_1234; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:22-94:73; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:22-94:73
    logic [31:0] arith_opt_1235; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:30-95:73; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:30-95:73
    logic [2:0] arith_opt_1236; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:83-95:92
    logic arith_opt_1237; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:97:14-97:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:97:14-97:56
    logic [2:0] arith_opt_1238; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:100:66-100:75
    logic [4:0] arith_opt_1239; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:98:63-98:73
    logic [4:0] arith_opt_1240; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic [4:0] arith_opt_1241; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic [31:0] arith_opt_1242; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic [36:0] arith_opt_1243; // decl: <none>; prim: <none>
    logic arith_opt_1244; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:5-47:57
    logic arith_opt_1245; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:5-48:57
    logic arith_opt_1246; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    logic arith_opt_1247; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    logic arith_opt_1248; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    logic arith_opt_1249; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:13-78:51
    logic arith_opt_1250; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:70:5-70:27
    logic arith_opt_1251; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:96:9-96:17
    logic arith_opt_1252; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:98:13-98:21
    logic [30:0] arith_opt_1253; // decl: <none>; prim: <none>
    logic [30:0] arith_opt_1254; // decl: <none>; prim: <none>
    logic [23:0] arith_opt_1255; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    logic [23:0] arith_opt_1256; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    logic [9:0] arith_opt_1257; // decl: <none>; prim: <none>
    logic [10:0] arith_opt_1258; // decl: <none>; prim: <none>
    logic [9:0] arith_opt_1259; // decl: <none>; prim: <none>
    logic [10:0] arith_opt_1260; // decl: <none>; prim: <none>
    logic [47:0] arith_opt_1261; // decl: <none>; prim: <none>
    logic [47:0] arith_opt_1262; // decl: <none>; prim: <none>
    logic [16:0] arith_opt_1263; // decl: <none>; prim: <none>
    logic [31:0] arith_opt_1264; // decl: <none>; prim: <none>
    logic [6:0] arith_opt_1265; // decl: <none>; prim: <none>
    logic [9:0] arith_opt_1266; // decl: <none>; prim: <none>
    logic [31:0] arith_opt_1267; // decl: <none>; prim: <none>
    logic [31:0] arith_opt_1268; // decl: <none>; prim: <none>
    logic [23:0] arith_opt_1269; // decl: <none>; prim: <none>
    logic [23:0] arith_opt_1270; // decl: <none>; prim: <none>
    logic arith_opt_1271; // decl: <none>; prim: <none>
    logic arith_opt_1272; // decl: <none>; prim: <none>
    logic arith_opt_1273; // decl: <none>; prim: <none>
    logic arith_opt_1274; // decl: <none>; prim: <none>
    logic arith_opt_1275; // decl: <none>; prim: <none>
    logic arith_opt_1276; // decl: <none>; prim: <none>
    logic arith_opt_1277; // decl: <none>; prim: <none>
    logic arith_opt_1278; // decl: <none>; prim: <none>
    logic arith_opt_1279; // decl: <none>; prim: <none>
    logic arith_opt_1280; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1281; // decl: <none>; prim: <none>
    logic arith_opt_1282; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1283; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1284; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1285; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1286; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1287; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1288; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1289; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1290; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1291; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1292; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1293; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1294; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1295; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1296; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1297; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1298; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1299; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1300; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1301; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1302; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1303; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1304; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1305; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1306; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1307; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1308; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1309; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1310; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1311; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1312; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1313; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1314; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1315; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1316; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1317; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1318; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1319; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1320; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1321; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1322; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1323; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1324; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1325; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1326; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1327; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1328; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1329; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1330; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1331; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1332; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1333; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1334; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1335; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1336; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1337; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1338; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1339; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1340; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1341; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1342; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1343; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1344; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic [31:0] arith_opt_1345; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:10
    logic [31:0] arith_opt_1346; // decl: <none>; prim: <none>
    logic arith_opt_1347; // decl: <none>; prim: <none>
    logic arith_opt_1348; // decl: <none>; prim: <none>
    logic arith_opt_1349; // decl: <none>; prim: <none>
    logic arith_opt_1350; // decl: <none>; prim: <none>
    logic arith_opt_1351; // decl: <none>; prim: <none>
    logic arith_opt_1352; // decl: <none>; prim: <none>
    logic arith_opt_1353; // decl: <none>; prim: <none>
    logic arith_opt_1354; // decl: <none>; prim: <none>
    logic arith_opt_1355; // decl: <none>; prim: <none>
    logic arith_opt_1356; // decl: <none>; prim: <none>
    logic arith_opt_1357; // decl: <none>; prim: <none>
    logic arith_opt_1358; // decl: <none>; prim: <none>
    logic arith_opt_1359; // decl: <none>; prim: <none>
    logic arith_opt_1360; // decl: <none>; prim: <none>
    logic arith_opt_1361; // decl: <none>; prim: <none>
    logic arith_opt_1362; // decl: <none>; prim: <none>
    logic arith_opt_1363; // decl: <none>; prim: <none>
    logic arith_opt_1364; // decl: <none>; prim: <none>
    logic arith_opt_1365; // decl: <none>; prim: <none>
    logic arith_opt_1366; // decl: <none>; prim: <none>
    logic arith_opt_1367; // decl: <none>; prim: <none>
    logic arith_opt_1368; // decl: <none>; prim: <none>
    logic [31:0] arith_opt_1369; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:27-44:32; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:27-44:32
    logic arith_opt_1370; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:63-6:64
    logic [7:0] arith_opt_1371; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:10
    logic [7:0] arith_opt_1372; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:12
    logic [22:0] arith_opt_1373; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28
    logic [22:0] arith_opt_1374; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45
    logic arith_opt_1375; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:16-47:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:24-45:31
    logic arith_opt_1376; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:39-47:55; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    logic arith_opt_1377; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:15-47:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:15-47:56
    logic arith_opt_1378; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:16-48:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:46-45:53
    logic arith_opt_1379; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:39-48:55; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    logic arith_opt_1380; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:15-48:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:15-48:56
    logic [22:0] arith_opt_1381; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:49:24-49:46; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    logic arith_opt_1382; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:49:23-49:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28
    logic [22:0] arith_opt_1383; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:50:24-50:46; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    logic arith_opt_1384; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:50:23-50:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45
    logic arith_opt_1385; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:51:16-51:55; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:63-6:64
    logic arith_opt_1386; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:52:16-52:55; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:65-6:66
    logic arith_opt_1387; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:9-54:24; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:24-45:31
    logic [23:0] arith_opt_1388; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:31-54:53; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:5-46:46
    logic [23:0] arith_opt_1389; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:31-54:53
    logic arith_opt_1390; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:9-55:24; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:46-45:53
    logic [23:0] arith_opt_1391; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:31-55:53; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:5-46:46
    logic [23:0] arith_opt_1392; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:31-55:53
    logic arith_opt_1393; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1394; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [23:0] arith_opt_1395; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic arith_opt_1396; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_1397; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1398; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [23:0] arith_opt_1399; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic arith_opt_1400; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1401; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1402; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [1:0] arith_opt_1403; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_1404; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [1:0] arith_opt_1405; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_1406; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1407; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [1:0] arith_opt_1408; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_1409; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [1:0] arith_opt_1410; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1411; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1412; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [2:0] arith_opt_1413; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_1414; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [2:0] arith_opt_1415; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_1416; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1417; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [2:0] arith_opt_1418; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_1419; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [2:0] arith_opt_1420; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1421; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1422; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [3:0] arith_opt_1423; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_1424; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [3:0] arith_opt_1425; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_1426; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1427; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [3:0] arith_opt_1428; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_1429; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [3:0] arith_opt_1430; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1431; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1432; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [4:0] arith_opt_1433; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_1434; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [4:0] arith_opt_1435; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_1436; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1437; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [4:0] arith_opt_1438; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_1439; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [4:0] arith_opt_1440; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1441; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1442; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [5:0] arith_opt_1443; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_1444; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [5:0] arith_opt_1445; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_1446; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1447; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [5:0] arith_opt_1448; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_1449; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [5:0] arith_opt_1450; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1451; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1452; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [6:0] arith_opt_1453; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_1454; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [6:0] arith_opt_1455; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_1456; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1457; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [6:0] arith_opt_1458; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_1459; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [6:0] arith_opt_1460; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1461; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1462; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1463; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    logic [23:0] arith_opt_1464; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1465; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    logic arith_opt_1466; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1467; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1468; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    logic [23:0] arith_opt_1469; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1470; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    logic arith_opt_1471; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1472; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1473; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1474; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1475; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1476; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1477; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1478; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1479; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1480; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1481; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1482; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1483; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1484; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1485; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1486; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1487; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1488; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1489; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1490; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1491; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1492; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1493; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1494; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1495; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1496; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1497; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1498; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1499; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1500; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1501; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1502; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1503; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1504; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1505; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1506; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1507; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1508; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1509; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1510; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1511; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1512; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1513; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1514; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1515; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1516; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1517; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1518; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1519; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1520; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1521; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1522; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1523; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1524; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1525; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1526; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1527; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1528; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1529; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1530; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1531; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1532; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1533; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1534; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1535; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1536; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1537; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1538; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1539; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1540; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1541; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1542; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1543; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1544; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1545; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1546; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1547; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1548; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1549; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1550; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1551; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1552; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1553; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1554; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1555; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1556; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1557; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1558; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1559; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1560; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1561; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1562; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1563; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1564; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1565; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1566; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1567; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1568; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1569; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1570; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1571; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1572; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1573; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1574; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1575; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1576; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1577; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1578; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1579; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1580; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1581; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1582; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1583; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1584; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1585; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1586; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1587; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1588; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1589; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1590; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1591; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1592; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1593; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1594; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1595; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1596; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1597; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1598; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1599; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1600; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1601; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1602; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1603; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1604; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1605; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1606; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1607; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1608; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1609; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1610; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1611; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    logic [23:0] arith_opt_1612; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    logic [7:0] arith_opt_1613; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    logic [23:0] arith_opt_1614; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1615; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic arith_opt_1616; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    logic [23:0] arith_opt_1617; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    logic [7:0] arith_opt_1618; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    logic [23:0] arith_opt_1619; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    logic [7:0] arith_opt_1620; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    logic [7:0] arith_opt_1621; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:58; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:17-45:32
    logic [10:0] arith_opt_1622; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:41
    logic [11:0] arith_opt_1623; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:18-62:88; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:58
    logic [7:0] arith_opt_1624; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:58; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:39-45:54
    logic [10:0] arith_opt_1625; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:41
    logic [11:0] arith_opt_1626; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:18-63:88; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:58
    logic [11:0] arith_opt_1627; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25
    logic [11:0] arith_opt_1628; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:40; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:18-62:88
    logic [47:0] arith_opt_1629; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    logic [30:0] arith_opt_1630; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    logic arith_opt_1631; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:67:9-67:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    logic [30:0] arith_opt_1632; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:27-66:40
    logic [30:0] arith_opt_1633; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:67:59-67:75
    logic arith_opt_1634; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:9-68:34; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:15-68:34
    logic [31:0] arith_opt_1635; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52
    logic [11:0] arith_opt_1636; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:59-68:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25
    logic [11:0] arith_opt_1637; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:5-64:41; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:5-64:41
    logic [31:0] arith_opt_1638; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52
    logic arith_opt_1639; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:71:9-71:26; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:71:14-71:26
    logic arith_opt_1640; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:22-72:39; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:27-72:39
    logic arith_opt_1641; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:21-72:85; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:21-72:85
    logic [31:0] arith_opt_1642; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:62; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:62
    logic arith_opt_1643; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:84; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:84
    logic arith_opt_1644; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:21-85:38; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:26-85:38
    logic arith_opt_1645; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81
    logic arith_opt_1646; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:15-86:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:21-86:33
    logic arith_opt_1647; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:14-86:80; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:14-86:80
    logic arith_opt_1648; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81
    logic [11:0] arith_opt_1649; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:37
    logic arith_opt_1650; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:37
    logic arith_opt_1651; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:36; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:36
    logic arith_opt_1652; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:39-75:49
    logic [31:0] arith_opt_1653; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:29-77:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:29-77:48
    logic [31:0] arith_opt_1654; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:28-77:62; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:28-77:62
    logic [31:0] arith_opt_1655; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:25-78:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:25-78:35
    logic arith_opt_1656; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:24-78:50; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:24-78:50
    logic [31:0] arith_opt_1657; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:79:19-79:31; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:79:19-79:31
    logic [31:0] arith_opt_1658; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:80:28-80:44; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:80:28-80:44
    logic [31:0] arith_opt_1659; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42
    logic [31:0] arith_opt_1660; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:62
    logic arith_opt_1661; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:22-83:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:46-83:56
    logic [1:0] arith_opt_1662; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:67-83:84
    logic [8:0] arith_opt_1663; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:54-68:74
    logic [31:0] arith_opt_1664; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42
    logic [1:0] arith_opt_1665; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:13-83:57
    logic [6:0] arith_opt_1666; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:88:24-88:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:88:24-88:35
    logic [31:0] arith_opt_1667; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41
    logic [24:0] arith_opt_1668; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:30-89:41
    logic arith_opt_1669; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:9-90:31; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:22-90:31
    logic [1:0] arith_opt_1670; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:20-69:29
    logic [1:0] arith_opt_1671; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:41-90:58
    logic arith_opt_1672; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:9-91:32; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:22-91:32
    logic [24:0] arith_opt_1673; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41
    logic [24:0] arith_opt_1674; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:44-91:73
    logic [8:0] arith_opt_1675; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:82:9-82:26
    logic arith_opt_1676; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:93:9-93:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:34-91:73
    logic [8:0] arith_opt_1677; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:93:42-93:52
    logic [31:0] arith_opt_1678; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:23-94:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:19-44:40
    logic [31:0] arith_opt_1679; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61
    logic [31:0] arith_opt_1680; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:47-94:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61
    logic [31:0] arith_opt_1681; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:22-94:73; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:22-94:73
    logic [31:0] arith_opt_1682; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:30-95:73; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:30-95:73
    logic [2:0] arith_opt_1683; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:83-95:92
    logic arith_opt_1684; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:97:14-97:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:97:14-97:56
    logic [2:0] arith_opt_1685; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:100:66-100:75
    logic [4:0] arith_opt_1686; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:98:63-98:73
    logic [4:0] arith_opt_1687; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic [4:0] arith_opt_1688; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic [31:0] arith_opt_1689; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic [36:0] arith_opt_1690; // decl: <none>; prim: <none>
    logic arith_opt_1691; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:5-47:57
    logic arith_opt_1692; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:5-48:57
    logic arith_opt_1693; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    logic arith_opt_1694; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    logic arith_opt_1695; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    logic arith_opt_1696; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:13-78:51
    logic arith_opt_1697; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:70:5-70:27
    logic arith_opt_1698; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:96:9-96:17
    logic arith_opt_1699; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:98:13-98:21
    logic [30:0] arith_opt_1700; // decl: <none>; prim: <none>
    logic [30:0] arith_opt_1701; // decl: <none>; prim: <none>
    logic [23:0] arith_opt_1702; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    logic [23:0] arith_opt_1703; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    logic [9:0] arith_opt_1704; // decl: <none>; prim: <none>
    logic [10:0] arith_opt_1705; // decl: <none>; prim: <none>
    logic [9:0] arith_opt_1706; // decl: <none>; prim: <none>
    logic [10:0] arith_opt_1707; // decl: <none>; prim: <none>
    logic [47:0] arith_opt_1708; // decl: <none>; prim: <none>
    logic [47:0] arith_opt_1709; // decl: <none>; prim: <none>
    logic [16:0] arith_opt_1710; // decl: <none>; prim: <none>
    logic [31:0] arith_opt_1711; // decl: <none>; prim: <none>
    logic [6:0] arith_opt_1712; // decl: <none>; prim: <none>
    logic [9:0] arith_opt_1713; // decl: <none>; prim: <none>
    logic [31:0] arith_opt_1714; // decl: <none>; prim: <none>
    logic [31:0] arith_opt_1715; // decl: <none>; prim: <none>
    logic [23:0] arith_opt_1716; // decl: <none>; prim: <none>
    logic [23:0] arith_opt_1717; // decl: <none>; prim: <none>
    logic arith_opt_1718; // decl: <none>; prim: <none>
    logic arith_opt_1719; // decl: <none>; prim: <none>
    logic arith_opt_1720; // decl: <none>; prim: <none>
    logic arith_opt_1721; // decl: <none>; prim: <none>
    logic arith_opt_1722; // decl: <none>; prim: <none>
    logic arith_opt_1723; // decl: <none>; prim: <none>
    logic arith_opt_1724; // decl: <none>; prim: <none>
    logic arith_opt_1725; // decl: <none>; prim: <none>
    logic arith_opt_1726; // decl: <none>; prim: <none>
    logic arith_opt_1727; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1728; // decl: <none>; prim: <none>
    logic arith_opt_1729; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1730; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1731; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1732; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1733; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1734; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1735; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1736; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1737; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1738; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1739; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1740; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1741; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1742; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1743; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1744; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1745; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1746; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1747; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1748; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1749; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1750; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1751; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1752; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1753; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1754; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1755; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1756; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1757; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1758; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1759; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1760; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1761; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1762; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1763; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1764; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1765; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1766; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1767; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1768; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1769; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    logic arith_opt_1770; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1771; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1772; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1773; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1774; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1775; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1776; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1777; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1778; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1779; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1780; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1781; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1782; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1783; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1784; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1785; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1786; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1787; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1788; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1789; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1790; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic arith_opt_1791; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    logic [31:0] arith_opt_1792; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:10
    logic [31:0] arith_opt_1793; // decl: <none>; prim: <none>
    logic arith_opt_1794; // decl: <none>; prim: <none>
    logic arith_opt_1795; // decl: <none>; prim: <none>
    logic arith_opt_1796; // decl: <none>; prim: <none>
    logic arith_opt_1797; // decl: <none>; prim: <none>
    logic arith_opt_1798; // decl: <none>; prim: <none>
    logic arith_opt_1799; // decl: <none>; prim: <none>
    logic arith_opt_1800; // decl: <none>; prim: <none>
    logic arith_opt_1801; // decl: <none>; prim: <none>
    logic arith_opt_1802; // decl: <none>; prim: <none>
    logic arith_opt_1803; // decl: <none>; prim: <none>
    logic arith_opt_1804; // decl: <none>; prim: <none>
    logic arith_opt_1805; // decl: <none>; prim: <none>
    logic arith_opt_1806; // decl: <none>; prim: <none>
    logic arith_opt_1807; // decl: <none>; prim: <none>
    logic arith_opt_1808; // decl: <none>; prim: <none>
    logic arith_opt_1809; // decl: <none>; prim: <none>
    logic arith_opt_1810; // decl: <none>; prim: <none>
    logic arith_opt_1811; // decl: <none>; prim: <none>
    logic arith_opt_1812; // decl: <none>; prim: <none>
    logic arith_opt_1813; // decl: <none>; prim: <none>
    logic arith_opt_1814; // decl: <none>; prim: <none>
    logic arith_opt_1815; // decl: <none>; prim: <none>
    logic [4:0] arith_selection_909; // decl: <none>; prim: <none>
    logic [4:0] arith_selection_910; // decl: <none>; prim: <none>
    logic [31:0] arith_selection_911; // decl: <none>; prim: <none>
    logic [31:0] arith_selection_912; // decl: <none>; prim: <none>
    logic [31:0] arith_selection_913; // decl: <none>; prim: <none>
    logic [31:0] arith_selection_914; // decl: <none>; prim: <none>
    logic [31:0] arith_selection_915; // decl: <none>; prim: <none>
    logic [4:0] arith_selection_916; // decl: <none>; prim: <none>
    logic [4:0] arith_selection_917; // decl: <none>; prim: <none>
    logic [31:0] arith_selection_918; // decl: <none>; prim: <none>
    logic [31:0] arith_selection_919; // decl: <none>; prim: <none>
    logic [31:0] arith_selection_920; // decl: <none>; prim: <none>
    logic [31:0] arith_selection_921; // decl: <none>; prim: <none>
    logic [31:0] arith_selection_922; // decl: <none>; prim: <none>
    logic [63:0] arith_original_923; // decl: /home/zyrv/vulsim/interface.logic.cpp:12:38-12:41; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    logic [36:0] rtlzz_pipe_8_s1; // decl: <none>; prim: <none>
    logic [36:0] rtlzz_pipe_8_s2; // decl: <none>; prim: <none>
    logic [36:0] rtlzz_pipe_9_s1; // decl: <none>; prim: <none>
    logic [36:0] rtlzz_pipe_9_s2; // decl: <none>; prim: <none>
    logic [63:0] rtlzz_pipe_10_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:12:38-12:41; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    logic [63:0] rtlzz_pipe_10_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:12:38-12:41; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:37-2:44; prim: /home/zyrv/vulsim/interface.logic.cpp:2:37-2:44
    logic rtlzz_valid_s2; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:37-2:44; prim: /home/zyrv/vulsim/interface.logic.cpp:2:37-2:44


    assign y = rtlzz_pipe_8_s2; // decl: <none>; prim: <none>
    assign z = rtlzz_pipe_9_s2; // decl: <none>; prim: <none>
    assign m = rtlzz_pipe_10_s2; // decl: <none>; prim: <none>
    assign ov = rtlzz_valid_s2; // decl: <none>; prim: <none>
    assign arith_4_335 = arith_opt_1243; // decl: <none>; prim: <none>
    assign arith_5_335 = arith_opt_1690; // decl: <none>; prim: <none>
    assign arith_opt_917 = arith_original_923; // decl: <none>; prim: <none>
    assign arith_opt_918 = a; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:10
    assign arith_opt_919 = b; // decl: <none>; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    assign arith_opt_920 = ({32'h0, arith_opt_918}); // decl: <none>; prim: <none>
    assign arith_opt_921 = ({32'h0, arith_opt_919}); // decl: <none>; prim: <none>
    assign arith_opt_922 = (a ^ b); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:27-44:32; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:27-44:32
    assign arith_opt_923 = arith_opt_922[31]; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:63-6:64
    assign arith_opt_924 = a[30:23]; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:10
    assign arith_opt_925 = b[30:23]; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:12
    assign arith_opt_926 = a[22:0]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28
    assign arith_opt_927 = b[22:0]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45
    assign arith_opt_928 = (arith_opt_924 == 8'hff); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:16-47:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:24-45:31
    assign arith_opt_929 = (arith_opt_926 != 23'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:39-47:55; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    assign arith_opt_930 = (arith_opt_928 & arith_opt_929); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:15-47:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:15-47:56
    assign arith_opt_931 = (arith_opt_925 == 8'hff); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:16-48:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:46-45:53
    assign arith_opt_932 = (arith_opt_927 != 23'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:39-48:55; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    assign arith_opt_933 = (arith_opt_931 & arith_opt_932); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:15-48:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:15-48:56
    assign arith_opt_934 = (arith_opt_926 & 23'h400000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:49:24-49:46; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    assign arith_opt_935 = (arith_opt_934 == 23'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:49:23-49:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28
    assign arith_opt_936 = (arith_opt_927 & 23'h400000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:50:24-50:46; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    assign arith_opt_937 = (arith_opt_936 == 23'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:50:23-50:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45
    assign arith_opt_938 = (arith_opt_1253 == 31'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:51:16-51:55; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:63-6:64
    assign arith_opt_939 = (arith_opt_1254 == 31'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:52:16-52:55; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:65-6:66
    assign arith_opt_940 = (arith_opt_924 != 8'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:9-54:24; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:24-45:31
    assign arith_opt_941 = (arith_opt_1255 | 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:31-54:53; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:5-46:46
    assign arith_opt_942 = (arith_opt_940 ? arith_opt_941 : ({1'h0, arith_opt_926})); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:31-54:53
    assign arith_opt_943 = (arith_opt_925 != 8'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:9-55:24; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:46-45:53
    assign arith_opt_944 = (arith_opt_1256 | 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:31-55:53; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:5-46:46
    assign arith_opt_945 = (arith_opt_943 ? arith_opt_944 : ({1'h0, arith_opt_927})); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:31-55:53
    assign arith_opt_946 = (arith_opt_942 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_947 = (arith_opt_942 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_948 = (arith_opt_946 ? arith_opt_947 : arith_opt_942); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_949 = (arith_opt_946 ? 1'(8'h1) : 1'(8'h0)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_950 = (arith_opt_945 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_951 = (arith_opt_945 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_952 = (arith_opt_950 ? arith_opt_951 : arith_opt_945); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_953 = (arith_opt_950 ? 1'(8'h1) : 1'(8'h0)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_954 = (arith_opt_948 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_955 = (arith_opt_948 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_956 = (arith_opt_949 + 1'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_957 = (arith_opt_954 ? arith_opt_955 : arith_opt_948); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_958 = (arith_opt_954 ? arith_opt_956 : ({1'h0, arith_opt_949})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_959 = (arith_opt_952 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_960 = (arith_opt_952 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_961 = (arith_opt_953 + 1'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_962 = (arith_opt_959 ? arith_opt_960 : arith_opt_952); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_963 = (arith_opt_959 ? arith_opt_961 : ({1'h0, arith_opt_953})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_964 = (arith_opt_957 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_965 = (arith_opt_957 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_966 = (arith_opt_958 + 2'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_967 = (arith_opt_964 ? arith_opt_965 : arith_opt_957); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_968 = (arith_opt_964 ? arith_opt_966 : ({1'h0, arith_opt_958})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_969 = (arith_opt_962 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_970 = (arith_opt_962 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_971 = (arith_opt_963 + 2'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_972 = (arith_opt_969 ? arith_opt_970 : arith_opt_962); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_973 = (arith_opt_969 ? arith_opt_971 : ({1'h0, arith_opt_963})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_974 = (arith_opt_967 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_975 = (arith_opt_967 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_976 = (arith_opt_968 + 3'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_977 = (arith_opt_974 ? arith_opt_975 : arith_opt_967); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_978 = (arith_opt_974 ? arith_opt_976 : ({1'h0, arith_opt_968})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_979 = (arith_opt_972 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_980 = (arith_opt_972 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_981 = (arith_opt_973 + 3'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_982 = (arith_opt_979 ? arith_opt_980 : arith_opt_972); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_983 = (arith_opt_979 ? arith_opt_981 : ({1'h0, arith_opt_973})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_984 = (arith_opt_977 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_985 = (arith_opt_977 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_986 = (arith_opt_978 + 4'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_987 = (arith_opt_984 ? arith_opt_985 : arith_opt_977); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_988 = (arith_opt_984 ? arith_opt_986 : ({1'h0, arith_opt_978})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_989 = (arith_opt_982 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_990 = (arith_opt_982 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_991 = (arith_opt_983 + 4'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_992 = (arith_opt_989 ? arith_opt_990 : arith_opt_982); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_993 = (arith_opt_989 ? arith_opt_991 : ({1'h0, arith_opt_983})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_994 = (arith_opt_987 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_995 = (arith_opt_987 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_996 = (arith_opt_988 + 5'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_997 = (arith_opt_994 ? arith_opt_995 : arith_opt_987); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_998 = (arith_opt_994 ? arith_opt_996 : ({1'h0, arith_opt_988})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_999 = (arith_opt_992 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1000 = (arith_opt_992 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1001 = (arith_opt_993 + 5'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_1002 = (arith_opt_999 ? arith_opt_1000 : arith_opt_992); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1003 = (arith_opt_999 ? arith_opt_1001 : ({1'h0, arith_opt_993})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1004 = (arith_opt_997 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1005 = (arith_opt_997 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1006 = (arith_opt_998 + 6'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_1007 = (arith_opt_1004 ? arith_opt_1005 : arith_opt_997); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1008 = (arith_opt_1004 ? arith_opt_1006 : ({1'h0, arith_opt_998})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_1009 = (arith_opt_1002 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1010 = (arith_opt_1002 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1011 = (arith_opt_1003 + 6'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_1012 = (arith_opt_1009 ? arith_opt_1010 : arith_opt_1002); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1013 = (arith_opt_1009 ? arith_opt_1011 : ({1'h0, arith_opt_1003})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1014 = (arith_opt_1007 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1015 = (arith_opt_1007 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1016 = (arith_opt_1008 + 7'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_1017 = (arith_opt_1014 ? arith_opt_1015 : arith_opt_1007); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1018 = (arith_opt_1014 ? arith_opt_1016 : ({1'h0, arith_opt_1008})); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_1019 = (arith_opt_1012 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1020 = (arith_opt_1012 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1021 = (arith_opt_1013 + 7'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_1022 = (arith_opt_1019 ? arith_opt_1020 : arith_opt_1012); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1023 = (arith_opt_1019 ? arith_opt_1021 : ({1'h0, arith_opt_1013})); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1024 = (arith_opt_1017 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1025 = (arith_opt_1017 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1026 = (arith_opt_1018 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1027 = (arith_opt_1024 ? arith_opt_1025 : arith_opt_1017); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1028 = (arith_opt_1024 ? arith_opt_1026 : arith_opt_1018); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1029 = (arith_opt_1022 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1030 = (arith_opt_1022 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1031 = (arith_opt_1023 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1032 = (arith_opt_1029 ? arith_opt_1030 : arith_opt_1022); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1033 = (arith_opt_1029 ? arith_opt_1031 : arith_opt_1023); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1034 = (arith_opt_1027 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1035 = (arith_opt_1027 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1036 = (arith_opt_1028 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1037 = (arith_opt_1034 ? arith_opt_1035 : arith_opt_1027); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1038 = (arith_opt_1034 ? arith_opt_1036 : arith_opt_1028); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1039 = (arith_opt_1032 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1040 = (arith_opt_1032 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1041 = (arith_opt_1033 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1042 = (arith_opt_1039 ? arith_opt_1040 : arith_opt_1032); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1043 = (arith_opt_1039 ? arith_opt_1041 : arith_opt_1033); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1044 = (arith_opt_1037 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1045 = (arith_opt_1037 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1046 = (arith_opt_1038 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1047 = (arith_opt_1044 ? arith_opt_1045 : arith_opt_1037); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1048 = (arith_opt_1044 ? arith_opt_1046 : arith_opt_1038); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1049 = (arith_opt_1042 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1050 = (arith_opt_1042 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1051 = (arith_opt_1043 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1052 = (arith_opt_1049 ? arith_opt_1050 : arith_opt_1042); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1053 = (arith_opt_1049 ? arith_opt_1051 : arith_opt_1043); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1054 = (arith_opt_1047 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1055 = (arith_opt_1047 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1056 = (arith_opt_1048 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1057 = (arith_opt_1054 ? arith_opt_1055 : arith_opt_1047); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1058 = (arith_opt_1054 ? arith_opt_1056 : arith_opt_1048); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1059 = (arith_opt_1052 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1060 = (arith_opt_1052 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1061 = (arith_opt_1053 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1062 = (arith_opt_1059 ? arith_opt_1060 : arith_opt_1052); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1063 = (arith_opt_1059 ? arith_opt_1061 : arith_opt_1053); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1064 = (arith_opt_1057 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1065 = (arith_opt_1057 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1066 = (arith_opt_1058 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1067 = (arith_opt_1064 ? arith_opt_1065 : arith_opt_1057); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1068 = (arith_opt_1064 ? arith_opt_1066 : arith_opt_1058); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1069 = (arith_opt_1062 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1070 = (arith_opt_1062 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1071 = (arith_opt_1063 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1072 = (arith_opt_1069 ? arith_opt_1070 : arith_opt_1062); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1073 = (arith_opt_1069 ? arith_opt_1071 : arith_opt_1063); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1074 = (arith_opt_1067 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1075 = (arith_opt_1067 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1076 = (arith_opt_1068 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1077 = (arith_opt_1074 ? arith_opt_1075 : arith_opt_1067); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1078 = (arith_opt_1074 ? arith_opt_1076 : arith_opt_1068); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1079 = (arith_opt_1072 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1080 = (arith_opt_1072 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1081 = (arith_opt_1073 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1082 = (arith_opt_1079 ? arith_opt_1080 : arith_opt_1072); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1083 = (arith_opt_1079 ? arith_opt_1081 : arith_opt_1073); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1084 = (arith_opt_1077 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1085 = (arith_opt_1077 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1086 = (arith_opt_1078 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1087 = (arith_opt_1084 ? arith_opt_1085 : arith_opt_1077); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1088 = (arith_opt_1084 ? arith_opt_1086 : arith_opt_1078); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1089 = (arith_opt_1082 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1090 = (arith_opt_1082 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1091 = (arith_opt_1083 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1092 = (arith_opt_1089 ? arith_opt_1090 : arith_opt_1082); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1093 = (arith_opt_1089 ? arith_opt_1091 : arith_opt_1083); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1094 = (arith_opt_1087 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1095 = (arith_opt_1087 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1096 = (arith_opt_1088 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1097 = (arith_opt_1094 ? arith_opt_1095 : arith_opt_1087); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1098 = (arith_opt_1094 ? arith_opt_1096 : arith_opt_1088); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1099 = (arith_opt_1092 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1100 = (arith_opt_1092 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1101 = (arith_opt_1093 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1102 = (arith_opt_1099 ? arith_opt_1100 : arith_opt_1092); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1103 = (arith_opt_1099 ? arith_opt_1101 : arith_opt_1093); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1104 = (arith_opt_1097 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1105 = (arith_opt_1097 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1106 = (arith_opt_1098 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1107 = (arith_opt_1104 ? arith_opt_1105 : arith_opt_1097); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1108 = (arith_opt_1104 ? arith_opt_1106 : arith_opt_1098); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1109 = (arith_opt_1102 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1110 = (arith_opt_1102 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1111 = (arith_opt_1103 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1112 = (arith_opt_1109 ? arith_opt_1110 : arith_opt_1102); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1113 = (arith_opt_1109 ? arith_opt_1111 : arith_opt_1103); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1114 = (arith_opt_1107 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1115 = (arith_opt_1107 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1116 = (arith_opt_1108 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1117 = (arith_opt_1114 ? arith_opt_1115 : arith_opt_1107); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1118 = (arith_opt_1114 ? arith_opt_1116 : arith_opt_1108); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1119 = (arith_opt_1112 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1120 = (arith_opt_1112 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1121 = (arith_opt_1113 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1122 = (arith_opt_1119 ? arith_opt_1120 : arith_opt_1112); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1123 = (arith_opt_1119 ? arith_opt_1121 : arith_opt_1113); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1124 = (arith_opt_1117 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1125 = (arith_opt_1117 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1126 = (arith_opt_1118 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1127 = (arith_opt_1124 ? arith_opt_1125 : arith_opt_1117); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1128 = (arith_opt_1124 ? arith_opt_1126 : arith_opt_1118); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1129 = (arith_opt_1122 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1130 = (arith_opt_1122 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1131 = (arith_opt_1123 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1132 = (arith_opt_1129 ? arith_opt_1130 : arith_opt_1122); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1133 = (arith_opt_1129 ? arith_opt_1131 : arith_opt_1123); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1134 = (arith_opt_1127 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1135 = (arith_opt_1127 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1136 = (arith_opt_1128 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1137 = (arith_opt_1134 ? arith_opt_1135 : arith_opt_1127); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1138 = (arith_opt_1134 ? arith_opt_1136 : arith_opt_1128); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1139 = (arith_opt_1132 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1140 = (arith_opt_1132 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1141 = (arith_opt_1133 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1142 = (arith_opt_1139 ? arith_opt_1140 : arith_opt_1132); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1143 = (arith_opt_1139 ? arith_opt_1141 : arith_opt_1133); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1144 = (arith_opt_1137 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1145 = (arith_opt_1137 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1146 = (arith_opt_1138 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1147 = (arith_opt_1144 ? arith_opt_1145 : arith_opt_1137); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1148 = (arith_opt_1144 ? arith_opt_1146 : arith_opt_1138); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1149 = (arith_opt_1142 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1150 = (arith_opt_1142 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1151 = (arith_opt_1143 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1152 = (arith_opt_1149 ? arith_opt_1150 : arith_opt_1142); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1153 = (arith_opt_1149 ? arith_opt_1151 : arith_opt_1143); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1154 = (arith_opt_1147 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1155 = (arith_opt_1147 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1156 = (arith_opt_1148 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1157 = (arith_opt_1154 ? arith_opt_1155 : arith_opt_1147); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1158 = (arith_opt_1154 ? arith_opt_1156 : arith_opt_1148); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1159 = (arith_opt_1152 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1160 = (arith_opt_1152 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1161 = (arith_opt_1153 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1162 = (arith_opt_1159 ? arith_opt_1160 : arith_opt_1152); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1163 = (arith_opt_1159 ? arith_opt_1161 : arith_opt_1153); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1164 = (arith_opt_1157 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1165 = (arith_opt_1157 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1166 = (arith_opt_1158 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1167 = (arith_opt_1164 ? arith_opt_1165 : arith_opt_1157); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1168 = (arith_opt_1164 ? arith_opt_1166 : arith_opt_1158); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1169 = (arith_opt_1162 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1170 = (arith_opt_1162 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1171 = (arith_opt_1163 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1172 = (arith_opt_1169 ? arith_opt_1170 : arith_opt_1162); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1173 = (arith_opt_1169 ? arith_opt_1171 : arith_opt_1163); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1174 = (arith_opt_940 ? arith_opt_924 : 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:58; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:17-45:32
    assign arith_opt_1175 = (arith_opt_1257 + 10'h200); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:41
    assign arith_opt_1176 = (arith_opt_1175 - arith_opt_1258); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:18-62:88; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:58
    assign arith_opt_1177 = (arith_opt_943 ? arith_opt_925 : 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:58; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:39-45:54
    assign arith_opt_1178 = (arith_opt_1259 + 10'h200); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:41
    assign arith_opt_1179 = (arith_opt_1178 - arith_opt_1260); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:18-63:88; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:58
    assign arith_opt_1180 = (arith_opt_1176 + arith_opt_1179); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25
    assign arith_opt_1181 = (arith_opt_1180 - 12'h27f); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:40; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:18-62:88
    assign arith_opt_1182 = 48'(($unsigned(48'($unsigned(arith_opt_1261))) * $unsigned(48'($unsigned(arith_opt_1262))))); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    assign arith_opt_1183 = arith_opt_1182[47:17]; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    assign arith_opt_1184 = (arith_opt_1263 != 17'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:67:9-67:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    assign arith_opt_1185 = (arith_opt_1183 | 31'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:27-66:40
    assign arith_opt_1186 = (arith_opt_1184 ? arith_opt_1185 : arith_opt_1183); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:67:59-67:75
    assign arith_opt_1187 = (arith_opt_1264 < 32'h40000000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:9-68:34; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:15-68:34
    assign arith_opt_1188 = (arith_opt_1264 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52
    assign arith_opt_1189 = (arith_opt_1181 - 12'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:59-68:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25
    assign arith_opt_1190 = (arith_opt_1187 ? arith_opt_1189 : arith_opt_1181); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:5-64:41; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:5-64:41
    assign arith_opt_1191 = (arith_opt_1187 ? arith_opt_1188 : ({1'h0, arith_opt_1186})); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52
    assign arith_opt_1192 = (arith_opt_1190 < 12'h200); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:71:9-71:26; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:71:14-71:26
    assign arith_opt_1193 = (arith_opt_1190 < 12'h1ff); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:22-72:39; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:27-72:39
    assign arith_opt_1194 = (!arith_opt_1193); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:21-72:85; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:21-72:85
    assign arith_opt_1195 = (arith_opt_1191 + 32'h40); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:62; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:62
    assign arith_opt_1196 = (arith_opt_1195 < 32'h80000000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:84; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:84
    assign arith_opt_1197 = (arith_opt_1190 > 12'h2fd); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:21-85:38; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:26-85:38
    assign arith_opt_1198 = (!arith_opt_1197); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81
    assign arith_opt_1199 = (arith_opt_1190 == 12'h2fd); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:15-86:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:21-86:33
    assign arith_opt_1200 = (arith_opt_1273 & arith_opt_1199); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:14-86:80; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:14-86:80
    assign arith_opt_1201 = (!arith_opt_1250); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81
    assign arith_opt_1202 = (12'h200 - arith_opt_1190); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:37
    assign arith_opt_1203 = (arith_opt_1202 >= 12'h20); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:37
    assign arith_opt_1204 = (arith_opt_1191 != 32'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:36; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:36
    assign arith_opt_1205 = (arith_opt_1204 ? 1'(32'h1) : 1'(32'h0)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:39-75:49
    assign arith_opt_1206 = (arith_opt_1202 >= 12'd32 ? 32'h0 : (32'h1 << arith_opt_1202)); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:29-77:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:29-77:48
    assign arith_opt_1207 = (arith_opt_1206 - 32'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:28-77:62; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:28-77:62
    assign arith_opt_1208 = (arith_opt_1191 & arith_opt_1207); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:25-78:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:25-78:35
    assign arith_opt_1209 = (arith_opt_1208 != 32'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:24-78:50; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:24-78:50
    assign arith_opt_1210 = (arith_opt_1202 >= 12'd32 ? 32'h0 : (arith_opt_1191 >> arith_opt_1202)); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:79:19-79:31; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:79:19-79:31
    assign arith_opt_1211 = (arith_opt_1210 | 32'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:80:28-80:44; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:80:28-80:44
    assign arith_opt_1212 = (arith_opt_1249 ? arith_opt_1211 : arith_opt_1210); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42
    assign arith_opt_1213 = (arith_opt_1246 ? ({31'h0, arith_opt_1205}) : arith_opt_1212); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:62
    assign arith_opt_1214 = (arith_opt_1265 != 7'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:22-83:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:46-83:56
    assign arith_opt_1215 = (arith_opt_1278 ? 2'(5'h2) : 2'(5'h0)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:67-83:84
    assign arith_opt_1216 = (arith_opt_1192 ? 9'(12'h200) : arith_opt_1190[8:0]); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:54-68:74
    assign arith_opt_1217 = (arith_opt_1192 ? arith_opt_1213 : arith_opt_1191); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42
    assign arith_opt_1218 = (arith_opt_1192 ? arith_opt_1215 : 2'(5'h0)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:13-83:57
    assign arith_opt_1219 = arith_opt_1217[6:0]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:88:24-88:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:88:24-88:35
    assign arith_opt_1220 = (arith_opt_1217 + 32'h40); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41
    assign arith_opt_1221 = arith_opt_1220[31:7]; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:30-89:41
    assign arith_opt_1222 = (arith_opt_1219 != 7'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:9-90:31; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:22-90:31
    assign arith_opt_1223 = (arith_opt_1218 | 2'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:20-69:29
    assign arith_opt_1224 = (arith_opt_1222 ? arith_opt_1223 : arith_opt_1218); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:41-90:58
    assign arith_opt_1225 = (arith_opt_1219 == 7'h40); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:9-91:32; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:22-91:32
    assign arith_opt_1226 = (arith_opt_1221 & 25'h1fffffe); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41
    assign arith_opt_1227 = (arith_opt_1225 ? arith_opt_1226 : arith_opt_1221); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:44-91:73
    assign arith_opt_1228 = 9'((arith_opt_1266 - 10'h200)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:82:9-82:26
    assign arith_opt_1229 = (arith_opt_1227 == 25'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:93:9-93:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:34-91:73
    assign arith_opt_1230 = (arith_opt_1229 ? 9'(32'h0) : arith_opt_1228); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:93:42-93:52
    assign arith_opt_1231 = (arith_opt_1345 << 5'h1f); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:23-94:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:19-44:40
    assign arith_opt_1232 = (arith_opt_1268 << 5'h17); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61
    assign arith_opt_1233 = (arith_opt_1232 + arith_opt_1267); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:47-94:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61
    assign arith_opt_1234 = (arith_opt_1231 | arith_opt_1233); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:22-94:73; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:22-94:73
    assign arith_opt_1235 = (arith_opt_1231 | 32'h7f800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:30-95:73; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:30-95:73
    assign arith_opt_1236 = (arith_opt_1201 ? 3'(5'h5) : ({1'h0, arith_opt_1224})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:83-95:92
    assign arith_opt_1237 = (!arith_opt_928); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:97:14-97:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:97:14-97:56
    assign arith_opt_1238 = (arith_opt_1280 ? 3'(5'h0) : arith_opt_1236); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:100:66-100:75
    assign arith_opt_1239 = (arith_opt_1281 ? 5'h10 : 5'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:98:63-98:73
    assign arith_opt_1240 = (arith_opt_1275 ? ({2'h0, arith_opt_1238}) : arith_opt_1239); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1241 = arith_selection_910; // decl: <none>; prim: <none>
    assign arith_opt_1242 = arith_selection_915; // decl: <none>; prim: <none>
    assign arith_opt_1243 = {arith_opt_1241, arith_opt_1242}; // decl: <none>; prim: <none>
    assign arith_opt_1244 = (!arith_opt_930); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:5-47:57
    assign arith_opt_1245 = (!arith_opt_933); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:5-48:57
    assign arith_opt_1246 = (arith_opt_1192 & arith_opt_1203); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    assign arith_opt_1247 = (!arith_opt_1203); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    assign arith_opt_1248 = (arith_opt_1192 & arith_opt_1247); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    assign arith_opt_1249 = (arith_opt_1209 & arith_opt_1248); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:13-78:51
    assign arith_opt_1250 = (arith_opt_1198 & arith_opt_1274); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:70:5-70:27
    assign arith_opt_1251 = (arith_opt_1244 & arith_opt_1245); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:96:9-96:17
    assign arith_opt_1252 = (arith_opt_1271 & arith_opt_1272); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:98:13-98:21
    assign arith_opt_1253 = a[30:0]; // decl: <none>; prim: <none>
    assign arith_opt_1254 = b[30:0]; // decl: <none>; prim: <none>
    assign arith_opt_1255 = (arith_opt_1269 & 24'h7fffff); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    assign arith_opt_1256 = (arith_opt_1270 & 24'h7fffff); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    assign arith_opt_1257 = ({2'h0, arith_opt_1174}); // decl: <none>; prim: <none>
    assign arith_opt_1258 = ({3'h0, arith_opt_1168}); // decl: <none>; prim: <none>
    assign arith_opt_1259 = ({2'h0, arith_opt_1177}); // decl: <none>; prim: <none>
    assign arith_opt_1260 = ({3'h0, arith_opt_1173}); // decl: <none>; prim: <none>
    assign arith_opt_1261 = ({24'h0, arith_opt_1167}); // decl: <none>; prim: <none>
    assign arith_opt_1262 = ({24'h0, arith_opt_1172}); // decl: <none>; prim: <none>
    assign arith_opt_1263 = arith_opt_1182[16:0]; // decl: <none>; prim: <none>
    assign arith_opt_1264 = ({1'h0, arith_opt_1186}); // decl: <none>; prim: <none>
    assign arith_opt_1265 = arith_opt_1213[6:0]; // decl: <none>; prim: <none>
    assign arith_opt_1266 = ({1'h0, arith_opt_1216}); // decl: <none>; prim: <none>
    assign arith_opt_1267 = ({7'h0, arith_opt_1227}); // decl: <none>; prim: <none>
    assign arith_opt_1268 = ({23'h0, arith_opt_1230}); // decl: <none>; prim: <none>
    assign arith_opt_1269 = a[23:0]; // decl: <none>; prim: <none>
    assign arith_opt_1270 = b[23:0]; // decl: <none>; prim: <none>
    assign arith_opt_1271 = (!arith_opt_938); // decl: <none>; prim: <none>
    assign arith_opt_1272 = (!arith_opt_939); // decl: <none>; prim: <none>
    assign arith_opt_1273 = (!arith_opt_1196); // decl: <none>; prim: <none>
    assign arith_opt_1274 = (!arith_opt_1200); // decl: <none>; prim: <none>
    assign arith_opt_1275 = (arith_opt_1237 & arith_opt_1279); // decl: <none>; prim: <none>
    assign arith_opt_1276 = (arith_opt_1273 & arith_opt_1194); // decl: <none>; prim: <none>
    assign arith_opt_1277 = (!arith_opt_1276); // decl: <none>; prim: <none>
    assign arith_opt_1278 = (arith_opt_1277 & arith_opt_1214); // decl: <none>; prim: <none>
    assign arith_opt_1279 = (!arith_opt_931); // decl: <none>; prim: <none>
    assign arith_opt_1280 = arith_opt_1326; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1281 = (arith_opt_1326 & arith_opt_1251); // decl: <none>; prim: <none>
    assign arith_opt_1282 = a[23]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1283 = a[24]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1284 = (arith_opt_1282 & arith_opt_1283); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1285 = a[25]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1286 = a[26]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1287 = (arith_opt_1285 & arith_opt_1286); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1288 = (arith_opt_1284 & arith_opt_1287); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1289 = a[27]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1290 = a[28]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1291 = (arith_opt_1289 & arith_opt_1290); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1292 = a[29]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1293 = a[30]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1294 = (arith_opt_1292 & arith_opt_1293); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1295 = (arith_opt_1291 & arith_opt_1294); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1296 = (arith_opt_1288 & arith_opt_1295); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1297 = (arith_opt_1296 & arith_opt_929); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1298 = (arith_opt_1297 & arith_opt_935); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1299 = b[23]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1300 = b[24]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1301 = (arith_opt_1299 & arith_opt_1300); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1302 = b[25]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1303 = b[26]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1304 = (arith_opt_1302 & arith_opt_1303); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1305 = (arith_opt_1301 & arith_opt_1304); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1306 = b[27]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1307 = b[28]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1308 = (arith_opt_1306 & arith_opt_1307); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1309 = b[29]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1310 = b[30]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1311 = (arith_opt_1309 & arith_opt_1310); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1312 = (arith_opt_1308 & arith_opt_1311); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1313 = (arith_opt_1305 & arith_opt_1312); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1314 = (arith_opt_1313 & arith_opt_932); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1315 = (arith_opt_1314 & arith_opt_937); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1316 = (!arith_opt_1368); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1317 = (!arith_opt_1296); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1318 = (!arith_opt_1297); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1319 = (!arith_opt_1313); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1320 = (!arith_opt_1314); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1321 = (arith_opt_1318 & arith_opt_1320); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1322 = (arith_opt_1368 & arith_opt_1323); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1323 = (!arith_opt_1321); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1324 = (!arith_opt_1343); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1325 = (arith_opt_1326 & arith_opt_1343); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1326 = (!arith_opt_1252); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1327 = arith_opt_1190[6]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1328 = arith_opt_1190[7]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1329 = arith_opt_1190[9]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1330 = arith_opt_1190[1]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1331 = arith_opt_1190[8]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1332 = arith_opt_1190[2]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1333 = arith_opt_1190[3]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1334 = arith_opt_1190[4]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1335 = arith_opt_1190[5]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1336 = arith_opt_1190[10]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1337 = arith_opt_1190[11]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1338 = arith_opt_1190[0]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1339 = (!arith_opt_1364); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1340 = (arith_opt_1198 & arith_opt_1339); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1341 = (arith_opt_1348 & arith_opt_1365); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1342 = (arith_opt_1250 & arith_opt_1348); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1343 = (arith_opt_1317 & arith_opt_1319); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1344 = (arith_opt_1321 & arith_opt_1347); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1345 = (arith_opt_1346 & 32'h1); // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:10
    assign arith_opt_1346 = ({31'h0, arith_opt_923}); // decl: <none>; prim: <none>
    assign arith_opt_1347 = (arith_opt_1326 & arith_opt_1324); // decl: <none>; prim: <none>
    assign arith_opt_1348 = (arith_opt_1252 & arith_opt_1343); // decl: <none>; prim: <none>
    assign arith_opt_1349 = (arith_opt_1327 & arith_opt_1328); // decl: <none>; prim: <none>
    assign arith_opt_1350 = (!arith_opt_1330); // decl: <none>; prim: <none>
    assign arith_opt_1351 = (!arith_opt_1331); // decl: <none>; prim: <none>
    assign arith_opt_1352 = (arith_opt_1350 & arith_opt_1351); // decl: <none>; prim: <none>
    assign arith_opt_1353 = (arith_opt_1329 & arith_opt_1352); // decl: <none>; prim: <none>
    assign arith_opt_1354 = (arith_opt_1349 & arith_opt_1353); // decl: <none>; prim: <none>
    assign arith_opt_1355 = (arith_opt_1332 & arith_opt_1333); // decl: <none>; prim: <none>
    assign arith_opt_1356 = (arith_opt_1334 & arith_opt_1335); // decl: <none>; prim: <none>
    assign arith_opt_1357 = (arith_opt_1355 & arith_opt_1356); // decl: <none>; prim: <none>
    assign arith_opt_1358 = (!arith_opt_1336); // decl: <none>; prim: <none>
    assign arith_opt_1359 = (!arith_opt_1337); // decl: <none>; prim: <none>
    assign arith_opt_1360 = (arith_opt_1358 & arith_opt_1359); // decl: <none>; prim: <none>
    assign arith_opt_1361 = (arith_opt_1273 & arith_opt_1338); // decl: <none>; prim: <none>
    assign arith_opt_1362 = (arith_opt_1360 & arith_opt_1361); // decl: <none>; prim: <none>
    assign arith_opt_1363 = (arith_opt_1357 & arith_opt_1362); // decl: <none>; prim: <none>
    assign arith_opt_1364 = (arith_opt_1354 & arith_opt_1363); // decl: <none>; prim: <none>
    assign arith_opt_1365 = (!arith_opt_1340); // decl: <none>; prim: <none>
    assign arith_opt_1366 = (!arith_opt_1298); // decl: <none>; prim: <none>
    assign arith_opt_1367 = (!arith_opt_1315); // decl: <none>; prim: <none>
    assign arith_opt_1368 = (arith_opt_1366 & arith_opt_1367); // decl: <none>; prim: <none>
    assign arith_opt_1369 = (a ^ c); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:27-44:32; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:27-44:32
    assign arith_opt_1370 = arith_opt_1369[31]; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:63-6:64
    assign arith_opt_1371 = a[30:23]; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:10
    assign arith_opt_1372 = c[30:23]; // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:12
    assign arith_opt_1373 = a[22:0]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28
    assign arith_opt_1374 = c[22:0]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45
    assign arith_opt_1375 = (arith_opt_1371 == 8'hff); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:16-47:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:24-45:31
    assign arith_opt_1376 = (arith_opt_1373 != 23'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:39-47:55; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    assign arith_opt_1377 = (arith_opt_1375 & arith_opt_1376); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:15-47:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:15-47:56
    assign arith_opt_1378 = (arith_opt_1372 == 8'hff); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:16-48:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:46-45:53
    assign arith_opt_1379 = (arith_opt_1374 != 23'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:39-48:55; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    assign arith_opt_1380 = (arith_opt_1378 & arith_opt_1379); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:15-48:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:15-48:56
    assign arith_opt_1381 = (arith_opt_1373 & 23'h400000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:49:24-49:46; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    assign arith_opt_1382 = (arith_opt_1381 == 23'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:49:23-49:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:18-46:28
    assign arith_opt_1383 = (arith_opt_1374 & 23'h400000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:50:24-50:46; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    assign arith_opt_1384 = (arith_opt_1383 == 23'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:50:23-50:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:35-46:45
    assign arith_opt_1385 = (arith_opt_1700 == 31'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:51:16-51:55; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:63-6:64
    assign arith_opt_1386 = (arith_opt_1701 == 31'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:52:16-52:55; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:6:65-6:66
    assign arith_opt_1387 = (arith_opt_1371 != 8'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:9-54:24; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:24-45:31
    assign arith_opt_1388 = (arith_opt_1702 | 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:31-54:53; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:5-46:46
    assign arith_opt_1389 = (arith_opt_1387 ? arith_opt_1388 : ({1'h0, arith_opt_1373})); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:54:31-54:53
    assign arith_opt_1390 = (arith_opt_1372 != 8'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:9-55:24; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:46-45:53
    assign arith_opt_1391 = (arith_opt_1703 | 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:31-55:53; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:46:5-46:46
    assign arith_opt_1392 = (arith_opt_1390 ? arith_opt_1391 : ({1'h0, arith_opt_1374})); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:55:31-55:53
    assign arith_opt_1393 = (arith_opt_1389 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1394 = (arith_opt_1389 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1395 = (arith_opt_1393 ? arith_opt_1394 : arith_opt_1389); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1396 = (arith_opt_1393 ? 1'(8'h1) : 1'(8'h0)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_1397 = (arith_opt_1392 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1398 = (arith_opt_1392 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1399 = (arith_opt_1397 ? arith_opt_1398 : arith_opt_1392); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1400 = (arith_opt_1397 ? 1'(8'h1) : 1'(8'h0)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1401 = (arith_opt_1395 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1402 = (arith_opt_1395 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1403 = (arith_opt_1396 + 1'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_1404 = (arith_opt_1401 ? arith_opt_1402 : arith_opt_1395); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1405 = (arith_opt_1401 ? arith_opt_1403 : ({1'h0, arith_opt_1396})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_1406 = (arith_opt_1399 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1407 = (arith_opt_1399 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1408 = (arith_opt_1400 + 1'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_1409 = (arith_opt_1406 ? arith_opt_1407 : arith_opt_1399); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1410 = (arith_opt_1406 ? arith_opt_1408 : ({1'h0, arith_opt_1400})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1411 = (arith_opt_1404 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1412 = (arith_opt_1404 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1413 = (arith_opt_1405 + 2'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_1414 = (arith_opt_1411 ? arith_opt_1412 : arith_opt_1404); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1415 = (arith_opt_1411 ? arith_opt_1413 : ({1'h0, arith_opt_1405})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_1416 = (arith_opt_1409 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1417 = (arith_opt_1409 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1418 = (arith_opt_1410 + 2'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_1419 = (arith_opt_1416 ? arith_opt_1417 : arith_opt_1409); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1420 = (arith_opt_1416 ? arith_opt_1418 : ({1'h0, arith_opt_1410})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1421 = (arith_opt_1414 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1422 = (arith_opt_1414 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1423 = (arith_opt_1415 + 3'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_1424 = (arith_opt_1421 ? arith_opt_1422 : arith_opt_1414); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1425 = (arith_opt_1421 ? arith_opt_1423 : ({1'h0, arith_opt_1415})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_1426 = (arith_opt_1419 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1427 = (arith_opt_1419 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1428 = (arith_opt_1420 + 3'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_1429 = (arith_opt_1426 ? arith_opt_1427 : arith_opt_1419); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1430 = (arith_opt_1426 ? arith_opt_1428 : ({1'h0, arith_opt_1420})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1431 = (arith_opt_1424 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1432 = (arith_opt_1424 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1433 = (arith_opt_1425 + 4'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_1434 = (arith_opt_1431 ? arith_opt_1432 : arith_opt_1424); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1435 = (arith_opt_1431 ? arith_opt_1433 : ({1'h0, arith_opt_1425})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_1436 = (arith_opt_1429 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1437 = (arith_opt_1429 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1438 = (arith_opt_1430 + 4'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_1439 = (arith_opt_1436 ? arith_opt_1437 : arith_opt_1429); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1440 = (arith_opt_1436 ? arith_opt_1438 : ({1'h0, arith_opt_1430})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1441 = (arith_opt_1434 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1442 = (arith_opt_1434 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1443 = (arith_opt_1435 + 5'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_1444 = (arith_opt_1441 ? arith_opt_1442 : arith_opt_1434); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1445 = (arith_opt_1441 ? arith_opt_1443 : ({1'h0, arith_opt_1435})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_1446 = (arith_opt_1439 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1447 = (arith_opt_1439 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1448 = (arith_opt_1440 + 5'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_1449 = (arith_opt_1446 ? arith_opt_1447 : arith_opt_1439); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1450 = (arith_opt_1446 ? arith_opt_1448 : ({1'h0, arith_opt_1440})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1451 = (arith_opt_1444 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1452 = (arith_opt_1444 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1453 = (arith_opt_1445 + 6'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_1454 = (arith_opt_1451 ? arith_opt_1452 : arith_opt_1444); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1455 = (arith_opt_1451 ? arith_opt_1453 : ({1'h0, arith_opt_1445})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_1456 = (arith_opt_1449 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1457 = (arith_opt_1449 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1458 = (arith_opt_1450 + 6'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_1459 = (arith_opt_1456 ? arith_opt_1457 : arith_opt_1449); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1460 = (arith_opt_1456 ? arith_opt_1458 : ({1'h0, arith_opt_1450})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1461 = (arith_opt_1454 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1462 = (arith_opt_1454 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1463 = (arith_opt_1455 + 7'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:53-58:72
    assign arith_opt_1464 = (arith_opt_1461 ? arith_opt_1462 : arith_opt_1454); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1465 = (arith_opt_1461 ? arith_opt_1463 : ({1'h0, arith_opt_1455})); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72
    assign arith_opt_1466 = (arith_opt_1459 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1467 = (arith_opt_1459 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1468 = (arith_opt_1460 + 7'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:53-59:72
    assign arith_opt_1469 = (arith_opt_1466 ? arith_opt_1467 : arith_opt_1459); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1470 = (arith_opt_1466 ? arith_opt_1468 : ({1'h0, arith_opt_1460})); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72
    assign arith_opt_1471 = (arith_opt_1464 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1472 = (arith_opt_1464 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1473 = (arith_opt_1465 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1474 = (arith_opt_1471 ? arith_opt_1472 : arith_opt_1464); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1475 = (arith_opt_1471 ? arith_opt_1473 : arith_opt_1465); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1476 = (arith_opt_1469 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1477 = (arith_opt_1469 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1478 = (arith_opt_1470 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1479 = (arith_opt_1476 ? arith_opt_1477 : arith_opt_1469); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1480 = (arith_opt_1476 ? arith_opt_1478 : arith_opt_1470); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1481 = (arith_opt_1474 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1482 = (arith_opt_1474 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1483 = (arith_opt_1475 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1484 = (arith_opt_1481 ? arith_opt_1482 : arith_opt_1474); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1485 = (arith_opt_1481 ? arith_opt_1483 : arith_opt_1475); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1486 = (arith_opt_1479 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1487 = (arith_opt_1479 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1488 = (arith_opt_1480 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1489 = (arith_opt_1486 ? arith_opt_1487 : arith_opt_1479); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1490 = (arith_opt_1486 ? arith_opt_1488 : arith_opt_1480); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1491 = (arith_opt_1484 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1492 = (arith_opt_1484 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1493 = (arith_opt_1485 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1494 = (arith_opt_1491 ? arith_opt_1492 : arith_opt_1484); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1495 = (arith_opt_1491 ? arith_opt_1493 : arith_opt_1485); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1496 = (arith_opt_1489 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1497 = (arith_opt_1489 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1498 = (arith_opt_1490 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1499 = (arith_opt_1496 ? arith_opt_1497 : arith_opt_1489); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1500 = (arith_opt_1496 ? arith_opt_1498 : arith_opt_1490); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1501 = (arith_opt_1494 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1502 = (arith_opt_1494 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1503 = (arith_opt_1495 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1504 = (arith_opt_1501 ? arith_opt_1502 : arith_opt_1494); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1505 = (arith_opt_1501 ? arith_opt_1503 : arith_opt_1495); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1506 = (arith_opt_1499 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1507 = (arith_opt_1499 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1508 = (arith_opt_1500 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1509 = (arith_opt_1506 ? arith_opt_1507 : arith_opt_1499); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1510 = (arith_opt_1506 ? arith_opt_1508 : arith_opt_1500); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1511 = (arith_opt_1504 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1512 = (arith_opt_1504 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1513 = (arith_opt_1505 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1514 = (arith_opt_1511 ? arith_opt_1512 : arith_opt_1504); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1515 = (arith_opt_1511 ? arith_opt_1513 : arith_opt_1505); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1516 = (arith_opt_1509 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1517 = (arith_opt_1509 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1518 = (arith_opt_1510 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1519 = (arith_opt_1516 ? arith_opt_1517 : arith_opt_1509); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1520 = (arith_opt_1516 ? arith_opt_1518 : arith_opt_1510); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1521 = (arith_opt_1514 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1522 = (arith_opt_1514 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1523 = (arith_opt_1515 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1524 = (arith_opt_1521 ? arith_opt_1522 : arith_opt_1514); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1525 = (arith_opt_1521 ? arith_opt_1523 : arith_opt_1515); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1526 = (arith_opt_1519 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1527 = (arith_opt_1519 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1528 = (arith_opt_1520 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1529 = (arith_opt_1526 ? arith_opt_1527 : arith_opt_1519); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1530 = (arith_opt_1526 ? arith_opt_1528 : arith_opt_1520); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1531 = (arith_opt_1524 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1532 = (arith_opt_1524 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1533 = (arith_opt_1525 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1534 = (arith_opt_1531 ? arith_opt_1532 : arith_opt_1524); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1535 = (arith_opt_1531 ? arith_opt_1533 : arith_opt_1525); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1536 = (arith_opt_1529 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1537 = (arith_opt_1529 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1538 = (arith_opt_1530 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1539 = (arith_opt_1536 ? arith_opt_1537 : arith_opt_1529); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1540 = (arith_opt_1536 ? arith_opt_1538 : arith_opt_1530); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1541 = (arith_opt_1534 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1542 = (arith_opt_1534 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1543 = (arith_opt_1535 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1544 = (arith_opt_1541 ? arith_opt_1542 : arith_opt_1534); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1545 = (arith_opt_1541 ? arith_opt_1543 : arith_opt_1535); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1546 = (arith_opt_1539 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1547 = (arith_opt_1539 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1548 = (arith_opt_1540 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1549 = (arith_opt_1546 ? arith_opt_1547 : arith_opt_1539); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1550 = (arith_opt_1546 ? arith_opt_1548 : arith_opt_1540); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1551 = (arith_opt_1544 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1552 = (arith_opt_1544 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1553 = (arith_opt_1545 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1554 = (arith_opt_1551 ? arith_opt_1552 : arith_opt_1544); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1555 = (arith_opt_1551 ? arith_opt_1553 : arith_opt_1545); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1556 = (arith_opt_1549 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1557 = (arith_opt_1549 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1558 = (arith_opt_1550 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1559 = (arith_opt_1556 ? arith_opt_1557 : arith_opt_1549); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1560 = (arith_opt_1556 ? arith_opt_1558 : arith_opt_1550); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1561 = (arith_opt_1554 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1562 = (arith_opt_1554 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1563 = (arith_opt_1555 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1564 = (arith_opt_1561 ? arith_opt_1562 : arith_opt_1554); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1565 = (arith_opt_1561 ? arith_opt_1563 : arith_opt_1555); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1566 = (arith_opt_1559 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1567 = (arith_opt_1559 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1568 = (arith_opt_1560 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1569 = (arith_opt_1566 ? arith_opt_1567 : arith_opt_1559); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1570 = (arith_opt_1566 ? arith_opt_1568 : arith_opt_1560); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1571 = (arith_opt_1564 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1572 = (arith_opt_1564 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1573 = (arith_opt_1565 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1574 = (arith_opt_1571 ? arith_opt_1572 : arith_opt_1564); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1575 = (arith_opt_1571 ? arith_opt_1573 : arith_opt_1565); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1576 = (arith_opt_1569 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1577 = (arith_opt_1569 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1578 = (arith_opt_1570 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1579 = (arith_opt_1576 ? arith_opt_1577 : arith_opt_1569); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1580 = (arith_opt_1576 ? arith_opt_1578 : arith_opt_1570); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1581 = (arith_opt_1574 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1582 = (arith_opt_1574 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1583 = (arith_opt_1575 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1584 = (arith_opt_1581 ? arith_opt_1582 : arith_opt_1574); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1585 = (arith_opt_1581 ? arith_opt_1583 : arith_opt_1575); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1586 = (arith_opt_1579 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1587 = (arith_opt_1579 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1588 = (arith_opt_1580 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1589 = (arith_opt_1586 ? arith_opt_1587 : arith_opt_1579); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1590 = (arith_opt_1586 ? arith_opt_1588 : arith_opt_1580); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1591 = (arith_opt_1584 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1592 = (arith_opt_1584 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1593 = (arith_opt_1585 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1594 = (arith_opt_1591 ? arith_opt_1592 : arith_opt_1584); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1595 = (arith_opt_1591 ? arith_opt_1593 : arith_opt_1585); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1596 = (arith_opt_1589 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1597 = (arith_opt_1589 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1598 = (arith_opt_1590 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1599 = (arith_opt_1596 ? arith_opt_1597 : arith_opt_1589); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1600 = (arith_opt_1596 ? arith_opt_1598 : arith_opt_1590); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1601 = (arith_opt_1594 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1602 = (arith_opt_1594 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1603 = (arith_opt_1595 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1604 = (arith_opt_1601 ? arith_opt_1602 : arith_opt_1594); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1605 = (arith_opt_1601 ? arith_opt_1603 : arith_opt_1595); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1606 = (arith_opt_1599 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1607 = (arith_opt_1599 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1608 = (arith_opt_1600 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1609 = (arith_opt_1606 ? arith_opt_1607 : arith_opt_1599); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1610 = (arith_opt_1606 ? arith_opt_1608 : arith_opt_1600); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1611 = (arith_opt_1604 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:13-58:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:18-58:35
    assign arith_opt_1612 = (arith_opt_1604 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:44-58:51
    assign arith_opt_1613 = (arith_opt_1605 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:58-58:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:58:63-58:72
    assign arith_opt_1614 = (arith_opt_1611 ? arith_opt_1612 : arith_opt_1604); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1615 = (arith_opt_1611 ? arith_opt_1613 : arith_opt_1605); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1616 = (arith_opt_1609 < 24'h800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:13-59:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:18-59:35
    assign arith_opt_1617 = (arith_opt_1609 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:44-59:51
    assign arith_opt_1618 = (arith_opt_1610 + 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:58-59:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:59:63-59:72
    assign arith_opt_1619 = (arith_opt_1616 ? arith_opt_1617 : arith_opt_1609); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:53:5-53:48
    assign arith_opt_1620 = (arith_opt_1616 ? arith_opt_1618 : arith_opt_1610); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:56:5-56:27
    assign arith_opt_1621 = (arith_opt_1387 ? arith_opt_1371 : 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:58; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:17-45:32
    assign arith_opt_1622 = (arith_opt_1704 + 10'h200); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:41
    assign arith_opt_1623 = (arith_opt_1622 - arith_opt_1705); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:18-62:88; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:26-62:58
    assign arith_opt_1624 = (arith_opt_1390 ? arith_opt_1372 : 8'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:58; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:45:39-45:54
    assign arith_opt_1625 = (arith_opt_1706 + 10'h200); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:41
    assign arith_opt_1626 = (arith_opt_1625 - arith_opt_1707); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:18-63:88; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:63:26-63:58
    assign arith_opt_1627 = (arith_opt_1623 + arith_opt_1626); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25
    assign arith_opt_1628 = (arith_opt_1627 - 12'h27f); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:40; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:62:18-62:88
    assign arith_opt_1629 = 48'(($unsigned(48'($unsigned(arith_opt_1708))) * $unsigned(48'($unsigned(arith_opt_1709))))); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    assign arith_opt_1630 = arith_opt_1629[47:17]; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    assign arith_opt_1631 = (arith_opt_1710 != 17'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:67:9-67:51; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:65:23-65:30
    assign arith_opt_1632 = (arith_opt_1630 | 31'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:27-66:40
    assign arith_opt_1633 = (arith_opt_1631 ? arith_opt_1632 : arith_opt_1630); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:67:59-67:75
    assign arith_opt_1634 = (arith_opt_1711 < 32'h40000000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:9-68:34; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:15-68:34
    assign arith_opt_1635 = (arith_opt_1711 << 1'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52
    assign arith_opt_1636 = (arith_opt_1628 - 12'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:59-68:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:18-64:25
    assign arith_opt_1637 = (arith_opt_1634 ? arith_opt_1636 : arith_opt_1628); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:5-64:41; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:64:5-64:41
    assign arith_opt_1638 = (arith_opt_1634 ? arith_opt_1635 : ({1'h0, arith_opt_1633})); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:44-68:52
    assign arith_opt_1639 = (arith_opt_1637 < 12'h200); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:71:9-71:26; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:71:14-71:26
    assign arith_opt_1640 = (arith_opt_1637 < 12'h1ff); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:22-72:39; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:27-72:39
    assign arith_opt_1641 = (!arith_opt_1640); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:21-72:85; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:21-72:85
    assign arith_opt_1642 = (arith_opt_1638 + 32'h40); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:62; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:62
    assign arith_opt_1643 = (arith_opt_1642 < 32'h80000000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:84; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:72:45-72:84
    assign arith_opt_1644 = (arith_opt_1637 > 12'h2fd); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:21-85:38; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:26-85:38
    assign arith_opt_1645 = (!arith_opt_1644); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81
    assign arith_opt_1646 = (arith_opt_1637 == 12'h2fd); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:15-86:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:21-86:33
    assign arith_opt_1647 = (arith_opt_1720 & arith_opt_1646); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:14-86:80; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:86:14-86:80
    assign arith_opt_1648 = (!arith_opt_1697); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:85:20-86:81
    assign arith_opt_1649 = (12'h200 - arith_opt_1637); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:37
    assign arith_opt_1650 = (arith_opt_1649 >= 12'h20); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:73:25-73:37
    assign arith_opt_1651 = (arith_opt_1638 != 32'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:36; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:36
    assign arith_opt_1652 = (arith_opt_1651 ? 1'(32'h1) : 1'(32'h0)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:39-75:49
    assign arith_opt_1653 = (arith_opt_1649 >= 12'd32 ? 32'h0 : (32'h1 << arith_opt_1649)); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:29-77:48; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:29-77:48
    assign arith_opt_1654 = (arith_opt_1653 - 32'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:28-77:62; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:77:28-77:62
    assign arith_opt_1655 = (arith_opt_1638 & arith_opt_1654); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:25-78:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:25-78:35
    assign arith_opt_1656 = (arith_opt_1655 != 32'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:24-78:50; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:24-78:50
    assign arith_opt_1657 = (arith_opt_1649 >= 12'd32 ? 32'h0 : (arith_opt_1638 >> arith_opt_1649)); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:79:19-79:31; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:79:19-79:31
    assign arith_opt_1658 = (arith_opt_1657 | 32'h1); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:80:28-80:44; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:80:28-80:44
    assign arith_opt_1659 = (arith_opt_1696 ? arith_opt_1658 : arith_opt_1657); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42
    assign arith_opt_1660 = (arith_opt_1693 ? ({31'h0, arith_opt_1652}) : arith_opt_1659); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:75:19-75:62
    assign arith_opt_1661 = (arith_opt_1712 != 7'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:22-83:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:46-83:56
    assign arith_opt_1662 = (arith_opt_1725 ? 2'(5'h2) : 2'(5'h0)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:67-83:84
    assign arith_opt_1663 = (arith_opt_1639 ? 9'(12'h200) : arith_opt_1637[8:0]); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:68:54-68:74
    assign arith_opt_1664 = (arith_opt_1639 ? arith_opt_1660 : arith_opt_1638); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:66:5-66:42
    assign arith_opt_1665 = (arith_opt_1639 ? arith_opt_1662 : 2'(5'h0)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:83:13-83:57
    assign arith_opt_1666 = arith_opt_1664[6:0]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:88:24-88:35; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:88:24-88:35
    assign arith_opt_1667 = (arith_opt_1664 + 32'h40); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41
    assign arith_opt_1668 = arith_opt_1667[31:7]; // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:30-89:41
    assign arith_opt_1669 = (arith_opt_1666 != 7'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:9-90:31; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:22-90:31
    assign arith_opt_1670 = (arith_opt_1665 | 2'h1); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:20-69:29
    assign arith_opt_1671 = (arith_opt_1669 ? arith_opt_1670 : arith_opt_1665); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:90:41-90:58
    assign arith_opt_1672 = (arith_opt_1666 == 7'h40); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:9-91:32; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:22-91:32
    assign arith_opt_1673 = (arith_opt_1668 & 25'h1fffffe); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:89:24-89:41
    assign arith_opt_1674 = (arith_opt_1672 ? arith_opt_1673 : arith_opt_1668); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:44-91:73
    assign arith_opt_1675 = 9'((arith_opt_1713 - 10'h200)); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:82:9-82:26
    assign arith_opt_1676 = (arith_opt_1674 == 25'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:93:9-93:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:91:34-91:73
    assign arith_opt_1677 = (arith_opt_1676 ? 9'(32'h0) : arith_opt_1675); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:93:42-93:52
    assign arith_opt_1678 = (arith_opt_1792 << 5'h1f); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:23-94:42; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:44:19-44:40
    assign arith_opt_1679 = (arith_opt_1715 << 5'h17); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61
    assign arith_opt_1680 = (arith_opt_1679 + arith_opt_1714); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:47-94:72; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:48-94:61
    assign arith_opt_1681 = (arith_opt_1678 | arith_opt_1680); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:22-94:73; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:22-94:73
    assign arith_opt_1682 = (arith_opt_1678 | 32'h7f800000); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:30-95:73; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:30-95:73
    assign arith_opt_1683 = (arith_opt_1648 ? 3'(5'h5) : ({1'h0, arith_opt_1671})); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:95:83-95:92
    assign arith_opt_1684 = (!arith_opt_1375); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:97:14-97:56; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:97:14-97:56
    assign arith_opt_1685 = (arith_opt_1727 ? 3'(5'h0) : arith_opt_1683); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:100:66-100:75
    assign arith_opt_1686 = (arith_opt_1728 ? 5'h10 : 5'h0); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:98:63-98:73
    assign arith_opt_1687 = (arith_opt_1722 ? ({2'h0, arith_opt_1685}) : arith_opt_1686); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1688 = arith_selection_917; // decl: <none>; prim: <none>
    assign arith_opt_1689 = arith_selection_922; // decl: <none>; prim: <none>
    assign arith_opt_1690 = {arith_opt_1688, arith_opt_1689}; // decl: <none>; prim: <none>
    assign arith_opt_1691 = (!arith_opt_1377); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:47:5-47:57
    assign arith_opt_1692 = (!arith_opt_1380); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:48:5-48:57
    assign arith_opt_1693 = (arith_opt_1639 & arith_opt_1650); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    assign arith_opt_1694 = (!arith_opt_1650); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    assign arith_opt_1695 = (arith_opt_1639 & arith_opt_1694); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:74:13-74:33
    assign arith_opt_1696 = (arith_opt_1656 & arith_opt_1695); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:78:13-78:51
    assign arith_opt_1697 = (arith_opt_1645 & arith_opt_1721); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:70:5-70:27
    assign arith_opt_1698 = (arith_opt_1691 & arith_opt_1692); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:96:9-96:17
    assign arith_opt_1699 = (arith_opt_1718 & arith_opt_1719); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:98:13-98:21
    assign arith_opt_1700 = a[30:0]; // decl: <none>; prim: <none>
    assign arith_opt_1701 = c[30:0]; // decl: <none>; prim: <none>
    assign arith_opt_1702 = (arith_opt_1716 & 24'h7fffff); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:30-43:39
    assign arith_opt_1703 = (arith_opt_1717 & 24'h7fffff); // decl: <none>; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:43:41-43:50
    assign arith_opt_1704 = ({2'h0, arith_opt_1621}); // decl: <none>; prim: <none>
    assign arith_opt_1705 = ({3'h0, arith_opt_1615}); // decl: <none>; prim: <none>
    assign arith_opt_1706 = ({2'h0, arith_opt_1624}); // decl: <none>; prim: <none>
    assign arith_opt_1707 = ({3'h0, arith_opt_1620}); // decl: <none>; prim: <none>
    assign arith_opt_1708 = ({24'h0, arith_opt_1614}); // decl: <none>; prim: <none>
    assign arith_opt_1709 = ({24'h0, arith_opt_1619}); // decl: <none>; prim: <none>
    assign arith_opt_1710 = arith_opt_1629[16:0]; // decl: <none>; prim: <none>
    assign arith_opt_1711 = ({1'h0, arith_opt_1633}); // decl: <none>; prim: <none>
    assign arith_opt_1712 = arith_opt_1660[6:0]; // decl: <none>; prim: <none>
    assign arith_opt_1713 = ({1'h0, arith_opt_1663}); // decl: <none>; prim: <none>
    assign arith_opt_1714 = ({7'h0, arith_opt_1674}); // decl: <none>; prim: <none>
    assign arith_opt_1715 = ({23'h0, arith_opt_1677}); // decl: <none>; prim: <none>
    assign arith_opt_1716 = a[23:0]; // decl: <none>; prim: <none>
    assign arith_opt_1717 = c[23:0]; // decl: <none>; prim: <none>
    assign arith_opt_1718 = (!arith_opt_1385); // decl: <none>; prim: <none>
    assign arith_opt_1719 = (!arith_opt_1386); // decl: <none>; prim: <none>
    assign arith_opt_1720 = (!arith_opt_1643); // decl: <none>; prim: <none>
    assign arith_opt_1721 = (!arith_opt_1647); // decl: <none>; prim: <none>
    assign arith_opt_1722 = (arith_opt_1684 & arith_opt_1726); // decl: <none>; prim: <none>
    assign arith_opt_1723 = (arith_opt_1720 & arith_opt_1641); // decl: <none>; prim: <none>
    assign arith_opt_1724 = (!arith_opt_1723); // decl: <none>; prim: <none>
    assign arith_opt_1725 = (arith_opt_1724 & arith_opt_1661); // decl: <none>; prim: <none>
    assign arith_opt_1726 = (!arith_opt_1378); // decl: <none>; prim: <none>
    assign arith_opt_1727 = arith_opt_1773; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1728 = (arith_opt_1773 & arith_opt_1698); // decl: <none>; prim: <none>
    assign arith_opt_1729 = a[23]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1730 = a[24]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1731 = (arith_opt_1729 & arith_opt_1730); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1732 = a[25]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1733 = a[26]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1734 = (arith_opt_1732 & arith_opt_1733); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1735 = (arith_opt_1731 & arith_opt_1734); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1736 = a[27]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1737 = a[28]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1738 = (arith_opt_1736 & arith_opt_1737); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1739 = a[29]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1740 = a[30]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1741 = (arith_opt_1739 & arith_opt_1740); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1742 = (arith_opt_1738 & arith_opt_1741); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1743 = (arith_opt_1735 & arith_opt_1742); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1744 = (arith_opt_1743 & arith_opt_1376); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1745 = (arith_opt_1744 & arith_opt_1382); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1746 = c[23]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1747 = c[24]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1748 = (arith_opt_1746 & arith_opt_1747); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1749 = c[25]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1750 = c[26]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1751 = (arith_opt_1749 & arith_opt_1750); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1752 = (arith_opt_1748 & arith_opt_1751); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1753 = c[27]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1754 = c[28]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1755 = (arith_opt_1753 & arith_opt_1754); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1756 = c[29]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1757 = c[30]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1758 = (arith_opt_1756 & arith_opt_1757); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1759 = (arith_opt_1755 & arith_opt_1758); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1760 = (arith_opt_1752 & arith_opt_1759); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1761 = (arith_opt_1760 & arith_opt_1379); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1762 = (arith_opt_1761 & arith_opt_1384); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1763 = (!arith_opt_1815); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1764 = (!arith_opt_1743); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1765 = (!arith_opt_1744); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1766 = (!arith_opt_1760); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1767 = (!arith_opt_1761); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1768 = (arith_opt_1765 & arith_opt_1767); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1769 = (arith_opt_1815 & arith_opt_1770); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:69:5-69:30
    assign arith_opt_1770 = (!arith_opt_1768); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1771 = (!arith_opt_1790); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1772 = (arith_opt_1773 & arith_opt_1790); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1773 = (!arith_opt_1699); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1774 = arith_opt_1637[6]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1775 = arith_opt_1637[7]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1776 = arith_opt_1637[9]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1777 = arith_opt_1637[1]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1778 = arith_opt_1637[8]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1779 = arith_opt_1637[2]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1780 = arith_opt_1637[3]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1781 = arith_opt_1637[4]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1782 = arith_opt_1637[5]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1783 = arith_opt_1637[10]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1784 = arith_opt_1637[11]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1785 = arith_opt_1637[0]; // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1786 = (!arith_opt_1811); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1787 = (arith_opt_1645 & arith_opt_1786); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1788 = (arith_opt_1795 & arith_opt_1812); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1789 = (arith_opt_1697 & arith_opt_1795); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1790 = (arith_opt_1764 & arith_opt_1766); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1791 = (arith_opt_1768 & arith_opt_1794); // decl: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74; prim: /home/zyrv/vulsim/vullib/arithmetic.hpp:94:5-94:74
    assign arith_opt_1792 = (arith_opt_1793 & 32'h1); // decl: <none>; prim: /home/zyrv/vulsim/arithmetic_fp32_template.logic.cpp:2:1-2:10
    assign arith_opt_1793 = ({31'h0, arith_opt_1370}); // decl: <none>; prim: <none>
    assign arith_opt_1794 = (arith_opt_1773 & arith_opt_1771); // decl: <none>; prim: <none>
    assign arith_opt_1795 = (arith_opt_1699 & arith_opt_1790); // decl: <none>; prim: <none>
    assign arith_opt_1796 = (arith_opt_1774 & arith_opt_1775); // decl: <none>; prim: <none>
    assign arith_opt_1797 = (!arith_opt_1777); // decl: <none>; prim: <none>
    assign arith_opt_1798 = (!arith_opt_1778); // decl: <none>; prim: <none>
    assign arith_opt_1799 = (arith_opt_1797 & arith_opt_1798); // decl: <none>; prim: <none>
    assign arith_opt_1800 = (arith_opt_1776 & arith_opt_1799); // decl: <none>; prim: <none>
    assign arith_opt_1801 = (arith_opt_1796 & arith_opt_1800); // decl: <none>; prim: <none>
    assign arith_opt_1802 = (arith_opt_1779 & arith_opt_1780); // decl: <none>; prim: <none>
    assign arith_opt_1803 = (arith_opt_1781 & arith_opt_1782); // decl: <none>; prim: <none>
    assign arith_opt_1804 = (arith_opt_1802 & arith_opt_1803); // decl: <none>; prim: <none>
    assign arith_opt_1805 = (!arith_opt_1783); // decl: <none>; prim: <none>
    assign arith_opt_1806 = (!arith_opt_1784); // decl: <none>; prim: <none>
    assign arith_opt_1807 = (arith_opt_1805 & arith_opt_1806); // decl: <none>; prim: <none>
    assign arith_opt_1808 = (arith_opt_1720 & arith_opt_1785); // decl: <none>; prim: <none>
    assign arith_opt_1809 = (arith_opt_1807 & arith_opt_1808); // decl: <none>; prim: <none>
    assign arith_opt_1810 = (arith_opt_1804 & arith_opt_1809); // decl: <none>; prim: <none>
    assign arith_opt_1811 = (arith_opt_1801 & arith_opt_1810); // decl: <none>; prim: <none>
    assign arith_opt_1812 = (!arith_opt_1787); // decl: <none>; prim: <none>
    assign arith_opt_1813 = (!arith_opt_1745); // decl: <none>; prim: <none>
    assign arith_opt_1814 = (!arith_opt_1762); // decl: <none>; prim: <none>
    assign arith_opt_1815 = (arith_opt_1813 & arith_opt_1814); // decl: <none>; prim: <none>
    assign arith_selection_909 = (arith_opt_1322 ? 5'h0 : arith_opt_1240); // decl: <none>; prim: <none>
    assign arith_selection_910 = (arith_opt_1316 ? 5'h10 : arith_selection_909); // decl: <none>; prim: <none>
    assign arith_selection_911 = (arith_opt_1344 ? 32'h7fc00000 : arith_opt_1235); // decl: <none>; prim: <none>
    assign arith_selection_912 = (arith_opt_1342 ? arith_opt_1234 : arith_selection_911); // decl: <none>; prim: <none>
    assign arith_selection_913 = (arith_opt_1341 ? arith_opt_1235 : arith_selection_912); // decl: <none>; prim: <none>
    assign arith_selection_914 = (arith_opt_1325 ? arith_opt_1231 : arith_selection_913); // decl: <none>; prim: <none>
    assign arith_selection_915 = (arith_opt_1323 ? 32'h7fc00000 : arith_selection_914); // decl: <none>; prim: <none>
    assign arith_selection_916 = (arith_opt_1769 ? 5'h0 : arith_opt_1687); // decl: <none>; prim: <none>
    assign arith_selection_917 = (arith_opt_1763 ? 5'h10 : arith_selection_916); // decl: <none>; prim: <none>
    assign arith_selection_918 = (arith_opt_1791 ? 32'h7fc00000 : arith_opt_1682); // decl: <none>; prim: <none>
    assign arith_selection_919 = (arith_opt_1789 ? arith_opt_1681 : arith_selection_918); // decl: <none>; prim: <none>
    assign arith_selection_920 = (arith_opt_1788 ? arith_opt_1682 : arith_selection_919); // decl: <none>; prim: <none>
    assign arith_selection_921 = (arith_opt_1772 ? arith_opt_1678 : arith_selection_920); // decl: <none>; prim: <none>
    assign arith_selection_922 = (arith_opt_1770 ? 32'h7fc00000 : arith_selection_921); // decl: <none>; prim: <none>
    assign arith_original_923 = 64'(($unsigned(64'($unsigned(arith_opt_920))) * $unsigned(64'($unsigned(arith_opt_921))))); // decl: /home/zyrv/vulsim/interface.logic.cpp:12:38-12:41; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
    always_ff @(posedge clk) begin
        if (!rstn) begin
            rtlzz_pipe_8_s1 <= 37'h107fc00000;
            rtlzz_pipe_8_s2 <= 37'h107fc00000;
            rtlzz_pipe_9_s1 <= 37'h7f800000;
            rtlzz_pipe_9_s2 <= 37'h7f800000;
            rtlzz_pipe_10_s1 <= 64'h0;
            rtlzz_pipe_10_s2 <= 64'h0;
            rtlzz_valid_s1 <= 1'h0;
            rtlzz_valid_s2 <= 1'h0;
        end else begin
        if (iv) begin
        rtlzz_pipe_8_s1 <= arith_4_335; // decl: <none>; prim: <none>
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_8_s2 <= rtlzz_pipe_8_s1; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_9_s1 <= arith_5_335; // decl: <none>; prim: <none>
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_9_s2 <= rtlzz_pipe_9_s1; // decl: <none>; prim: <none>
        end
        if (iv) begin
        rtlzz_pipe_10_s1 <= arith_opt_917; // decl: /home/zyrv/vulsim/interface.logic.cpp:12:38-12:41; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
        end
        if (rtlzz_valid_s1) begin
        rtlzz_pipe_10_s2 <= rtlzz_pipe_10_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:12:38-12:41; prim: /home/zyrv/vulsim/interface.logic.cpp:2:1-2:12
        end
        rtlzz_valid_s1 <= iv; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:37-2:44; prim: /home/zyrv/vulsim/interface.logic.cpp:2:37-2:44
        rtlzz_valid_s2 <= rtlzz_valid_s1; // decl: /home/zyrv/vulsim/interface.logic.cpp:2:37-2:44; prim: /home/zyrv/vulsim/interface.logic.cpp:2:37-2:44
        end
    end
endmodule
