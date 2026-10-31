    logic [63:0] __vul_port_s1reg; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    logic __vul_port_s1valid; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24
    logic [63:0] __vul_port_s3reg; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:18:1-18:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:36:1-36:58
    logic __vul_port_s3valid; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24
    logic __vul_pipeline_rstn; // decl: <none>; prim: <none>
    logic __vul_pipeline_clk; // decl: <none>; prim: <none>

    logic [63:0] vul_port_s1reg; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    logic vul_port_s1valid; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24
    logic [63:0] s6_helper___vul_compute_0_a__v0; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:22:5-22:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:29:1-29:143
    logic [127:0] s8_norm_mul_6_v0; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28
    logic [63:0] s6_helper___vul_compute_0_product__v0; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:5-24:29; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28
    logic [63:0] vul_port_s3reg; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:18:1-18:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:36:1-36:58
    logic vul_port_s3valid; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24
    logic [31:0] __beopt_width_36; // decl: <none>; prim: <none>
    logic [63:0] __beopt_width_13; // decl: <none>; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    logic [63:0] __beopt_width_11; // decl: <none>; prim: <none>
    logic [127:0] arith_original_10; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28
    logic [63:0] rtlzz_pipe_2_s1; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:22:5-22:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:29:1-29:143
    logic [63:0] rtlzz_pipe_8_s1; // decl: <none>; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    logic rtlzz_valid_s1; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24

    assign __vul_port_s1reg = __vul_pipeline_q_s1reg;
    assign __vul_port_s1valid = __vul_pipeline_q_s1valid;
    assign __vul_pipeline_d_s3reg = __vul_port_s3reg;
    assign __vul_pipeline_d_s3valid = __vul_port_s3valid;
    assign __vul_pipeline_rstn = rstn;
    assign __vul_pipeline_clk = clk;

    assign vul_port_s1reg = __vul_port_s1reg; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    assign vul_port_s1valid = __vul_port_s1valid; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24
    assign __vul_port_s3reg = vul_port_s3reg; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:18:1-18:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:36:1-36:58
    assign __vul_port_s3valid = vul_port_s3valid; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:20:1-20:24

    assign s6_helper___vul_compute_0_a__v0 = (vul_port_s1reg & 64'hffffffff); // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:22:5-22:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:29:1-29:143
    assign s8_norm_mul_6_v0 = arith_original_10; // decl: <none>; prim: <none>
    assign s6_helper___vul_compute_0_product__v0 = s8_norm_mul_6_v0[63:0]; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:5-24:29; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28
    assign vul_port_s3reg = s6_helper___vul_compute_0_product__v0; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:18:1-18:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:36:1-36:58
    assign vul_port_s3valid = rtlzz_valid_s1; // decl: <none>; prim: <none>
    assign __beopt_width_36 = vul_port_s1reg[63:32]; // decl: <none>; prim: <none>
    assign __beopt_width_13 = (__beopt_width_11 & 64'hffffffff); // decl: <none>; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
    assign __beopt_width_11 = ({32'h0, __beopt_width_36}); // decl: <none>; prim: <none>
    assign arith_original_10 = 128'(($unsigned(128'($unsigned(rtlzz_pipe_2_s1))) * $unsigned(128'($unsigned(rtlzz_pipe_8_s1))))); // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:24:23-24:28
    always_ff @(posedge __vul_pipeline_clk) begin
        if (!__vul_pipeline_rstn) begin
            rtlzz_pipe_2_s1 <= 64'h0;
            rtlzz_pipe_8_s1 <= 64'h0;
            rtlzz_valid_s1 <= 1'h0;
        end else begin
        if (vul_port_s1valid) begin
        rtlzz_pipe_2_s1 <= s6_helper___vul_compute_0_a__v0; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:22:5-22:25; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:29:1-29:143
        end
        if (vul_port_s1valid) begin
        rtlzz_pipe_8_s1 <= __beopt_width_13; // decl: <none>; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:14:1-14:25
        end
        rtlzz_valid_s1 <= vul_port_s1valid; // decl: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24; prim: /home/zyrv/vulsim/build/step4-review-20261031/vul-native/sim/top.logic.cpp.pipeline_multiply.cpp:16:1-16:24
        end
    end
