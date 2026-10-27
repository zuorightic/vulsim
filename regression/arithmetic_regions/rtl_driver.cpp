#include "VRegionRegression.h"
#include <iostream>
int main() {
    VRegionRegression model;
    unsigned a,b,c,d,iv,rstn;
    while(std::cin>>std::hex>>a>>b>>c>>d>>iv>>rstn) {
        model.clk=0;model.a=a;model.b=b;model.c=c;model.d=d;model.iv=iv;model.rstn=rstn;model.eval();
        model.clk=1;model.eval();model.clk=0;model.eval();
        for(unsigned i=0;i<6;++i) std::cout<<std::hex<<model.y[i]<<' '<<model.z[i]<<' '<<model.py[i]<<' '<<model.pz[i]<<' ';
        std::cout<<unsigned(model.ov)<<'\n';
    }
    model.final();
}
