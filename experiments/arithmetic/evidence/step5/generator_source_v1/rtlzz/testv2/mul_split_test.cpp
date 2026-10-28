#include "pipelinev2/PipelineV2.h"
#include "backend/arithmetic_regions.hpp"
#include "backend/mul_split.hpp"
#include "backend/simple_cost.hpp"
#include "backend/rtlgen.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <cstdlib>
using namespace pred;
using namespace beir;
#define CHECK(x) do { if(!(x)) { std::cerr<<__LINE__<<": "<<#x<<"\n";std::exit(1); } } while(false)
template<class F> static void rejects(F f) { bool bad=false;try{f();}catch(const std::runtime_error&){bad=true;} CHECK(bad); }
static Operand ref(const beir::Program& p,NodeId id) {Operand v;v.node=id;v.type=p.signal(id).type;return v;}
static NodeId node(beir::Program& p,int width,OperationKind k,std::vector<Operand> args={},OpCode code=OpCode::None) {
    Signal s;s.id=p.signals.size();s.name="n"+std::to_string(s.id);s.type.width=width;
    Operation d;d.kind=k;d.type=s.type;d.op=code;d.operands=std::move(args);s.driver=d;p.signals.push_back(s);return s.id;
}
static void port(beir::Program& p,NodeId id,const std::string& name,PortDirection dir) {
    auto& s=p.signal(id);s.name=name;s.port_name=name;Port v;v.name=name;v.type=s.type;v.direction=dir;v.element_nodes={id};p.ports.push_back(v);
    (dir==PortDirection::Input?p.inputs:p.outputs).push_back(name);
}
static void structural(std::ostream& evidence) {
    // A zero-cost two-node group narrows a shared 32-bit input to 8 bits.
    // Moving both members from stage 0 to stage 1 saves eight register bits;
    // the other output keeps the shared input chain alive in both schedules.
    beir::Program p;p.function_name="move";
    Operand external;external.kind=OperandKind::Port;external.text="a";external.type.width=32;
    auto a=node(p,32,OperationKind::PortRead,{external});port(p,a,"a",PortDirection::Input);
    auto x=node(p,8,OperationKind::Slice,{ref(p,a)});p.signal(x).driver->hi=7;p.signal(x).driver->lo=0;
    auto y=node(p,8,OperationKind::Assign,{ref(p,x)});
    ArithmeticRegion r;r.id="move/group";r.members={x,y};r.inputs={ref(p,a)};r.outputs={y};p.arithmetic_regions={r};
    auto o=node(p,8,OperationKind::Assign,{ref(p,y)});port(p,o,"short",PortDirection::Output);
    auto o2=node(p,32,OperationKind::Assign,{ref(p,a)});port(p,o2,"shared",PortDirection::Output);
    pipeline::Options opt;opt.register_stages=1;opt.use_simple_cost=true;
    auto q=pipeline::build(p,opt);pipeline::validateProgram(q);
    CHECK(q.report.accepted_group_moves>0);CHECK(q.stages[x]==q.stages[y]);
    CHECK(q.report.baseline_register_bits==40 && q.report.register_bits==32);
    evidence<<"legal group move accepted: baseline bits=40 final bits=32; shared chain charged once\n";
    auto bad=q;bad.stages[x]=0;rejects([&]{pipeline::validateProgram(bad);});
    // Selection result-type exception is shared with frozen Python contracts.
    auto mux=node(p,32,OperationKind::Ite,{ref(p,x),ref(p,a),ref(p,a)});
    for(auto id:{a,mux}) {auto& f=p.signal(id).value;f.valid=true;f.known_zero={0xffffff00};}
    auto c=simple_cost::node(p,mux);CHECK(c.delay==1 && c.area==32);
    p.signal(mux).driver->kind=OperationKind::Call;p.signal(mux).value.constant=true;
    rejects([&]{simple_cost::node(p,mux);});
}
int main(int argc,char**argv) {
    CHECK(argc==3);std::filesystem::create_directories(argv[2]);
    const std::string out=argv[2];std::ofstream evidence(out+"/schedule.txt");structural(evidence);
    const std::string source="#include \"fixint.hpp\"\nInt<32> a,b; Int<64> y; bool iv,ov;\n#pragma input_port a\n#pragma input_port b\n#pragma input_port iv\n#pragma output_port y\n#pragma output_port ov\nvoid mul_kernel(){y=a*b;}\n";
    std::ofstream(out+"/mul_kernel.logic.cpp")<<source;
    std::ofstream json(out+"/candidates.json");json<<"[\n";bool first=true;
    for(const std::string candidate:{"original","mul32_split16"}) {
        pipelinev2::PipelineConfig cfg;cfg.source_name="mul_kernel.logic.cpp";cfg.source_text=source;cfg.top_function="mul_kernel";
        cfg.clang_args={"-std=c++20",std::string("-I")+argv[1]};cfg.arithmetic_candidate=candidate;
        cfg.output_kind=pipelinev2::OutputKind::Rtl;cfg.pipeline.emplace();auto& opt=*cfg.pipeline;
        opt.register_stages=1;opt.use_simple_cost=true;opt.input_valid_name="iv";opt.output_valid_name="ov";opt.reset_enabled=true;
        opt.input_reset_values={{"a",{0}},{"b",{0}},{"iv",{0}}};
        auto result=pipelinev2::compile(cfg);
        if(!result.ok()) {std::cerr<<result.error<<"\n"<<result.error_debug_text<<"\n";return 1;}
        CHECK(result.pipeline_program);auto q=*result.pipeline_program;pipeline::validateProgram(q);
        std::ofstream(out+"/"+candidate+".beir.txt")<<pipeline::emitText(q);
        unsigned multipliers=0;for(const auto& s:q.combinational.signals) if(s.driver && s.driver->op==OpCode::Mul) {
            ++multipliers;CHECK(candidate=="original" || s.driver->operands[0].type.width==16);
        }
        CHECK(multipliers==(candidate=="original"?1:4));
        unsigned internal_registers=0;
        if(candidate!="original") {
            CHECK(q.combinational.arithmetic_regions.size()==1);
            const auto& region=q.combinational.arithmetic_regions[0];CHECK(region.legal_cut_groups.size()==3);
            std::set<int> stages;for(const auto& group:region.legal_cut_groups) {
                auto at=q.stages.at(group[0]);stages.insert(at);
                for(auto id:group) CHECK(q.stages.at(id)==at);
            }CHECK(stages.size()>1);
            internal_registers=q.rtl_program.arithmetic_regions[0].internal_registers.size();CHECK(internal_registers>0);
            auto bad=q;bad.stages[region.legal_cut_groups[0][0]]=1-q.stages[region.legal_cut_groups[0][0]];
            rejects([&]{pipeline::validateProgram(bad);});
            bad=q;bad.rtl_program.arithmetic_regions.clear();rejects([&]{pipeline::validateProgram(bad);});
            bad=q;bad.rtl_program.arithmetic_regions[0].internal_registers.clear();rejects([&]{pipeline::validateProgram(bad);});
            auto broken=q.combinational;broken.arithmetic_regions[0].legal_cut_groups[0].pop_back();rejects([&]{regions::validate(broken);});
            broken=q.combinational;broken.arithmetic_regions[0].legal_cut_groups[0].push_back(region.legal_cut_groups[1][0]);rejects([&]{regions::validate(broken);});
            rejects([&]{opt::optimizeProgram(q.combinational);});
        }
        evidence<<"candidate="<<candidate<<"\n"<<pipeline::emitText(q);
        const auto& report=q.report;
        if(!first) json<<",\n";first=false;
        json<<"{\"id\":\""<<candidate<<"\",\"L\":2,\"II\":1,\"delay\":"<<report.final_delay
            <<",\"combinational_cost\":"<<report.combinational_cost<<",\"register_bits\":"<<report.register_bits
            <<",\"register_count\":"<<report.register_count<<",\"accepted_group_moves\":"<<report.accepted_group_moves
            <<",\"internal_region_registers\":"<<internal_registers<<"}";
        q.rtl_program.function_name=candidate+"_core";
        std::ofstream sv(out+"/"+candidate+".sv");sv<<rtlgen::emitSystemVerilog(q);
        sv<<"\nmodule "<<candidate<<"(input logic clk,rstn,input logic [31:0] a,b,input logic iv,output logic [63:0] y,output logic ov);\n"
          <<"logic [31:0] aq,bq;logic ivq,ovd;logic [63:0] yd;\n"
          <<candidate<<"_core core(.clk(clk),.rstn(rstn),.a(aq),.b(bq),.iv(ivq),.y(yd),.ov(ovd));\n"
          <<"always_ff @(posedge clk) if(!rstn) begin aq<=0;bq<=0;ivq<=0;y<=0;ov<=0;end else begin aq<=a;bq<=b;ivq<=iv;ov<=ovd;if(ovd) y<=yd;end\nendmodule\n";
    }
    json<<"\n]\n";
    std::cout<<"PASS automatic mul split, group moves, cut metadata, frozen simple cost and schedule validation\n";
}
