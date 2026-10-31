#include "VArithmeticInterfaces.h"
#include "verilated.h"
#include <fstream>
#include <iomanip>
#include <iostream>
int main(int argc,char** argv){
    if(argc!=2)return 2;Verilated::commandArgs(argc,argv);VArithmeticInterfaces top;std::ifstream in(argv[1]);unsigned a[4],b[4],c[4],iv,rst;
    auto read=[&](unsigned* words){for(int i=0;i<4;++i)if(!(in>>std::hex>>words[i]))return false;return true;};
    auto wide=[&](const auto& value){for(int i=7;i>=0;--i)std::cout<<std::hex<<std::setw(8)<<std::setfill('0')<<value[i];};
    while(read(a)&&read(b)&&read(c)&&(in>>std::hex>>iv>>rst)){
        top.clk=0;top.iv=iv;top.rstn=rst;for(int i=0;i<4;++i){top.a[i]=a[i];top.b[i]=b[i];top.c[i]=c[i];}top.eval();top.clk=1;top.eval();
        std::cout<<std::hex<<static_cast<unsigned>(top.ovs)<<' '<<static_cast<unsigned>(top.fov);
        for(int i=0;i<9;++i){std::cout<<' ';wide(top.ys[i]);std::cout<<' ';wide(top.zs[i]);}
        std::cout<<' '<<top.fy<<' '<<top.fz<<' '<<top.fm<<' '<<top.fcy<<' '<<top.fcz<<' '<<top.fcm<<'\n';
    }
}
