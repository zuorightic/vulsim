#include "VMulSplitRegression.h"
#include "verilated.h"
#include <fstream>
#include <iostream>
#include <cstdint>
int main(int argc,char**argv) {
    if(argc!=2) return 2;
    std::ifstream input(argv[1]);VMulSplitRegression dut;
    std::uint32_t a,b,iv,rstn;
    while(input>>std::hex>>a>>b>>iv>>rstn) {
        dut.clk=0;dut.a=a;dut.b=b;dut.iv=iv;dut.rstn=rstn;dut.eval();
        dut.clk=1;dut.eval();
        std::cout<<std::hex<<dut.y0<<' '<<unsigned(dut.ov0)<<' '<<dut.y1<<' '<<unsigned(dut.ov1)<<'\n';
    }
    dut.final();return input.eof()?0:3;
}
