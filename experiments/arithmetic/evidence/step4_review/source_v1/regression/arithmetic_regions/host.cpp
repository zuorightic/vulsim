#include "arithmetic.hpp"
#include <iostream>
int main(){unsigned a,b;while(std::cin>>std::hex>>a>>b) std::cout<<std::hex<<vularith::F32MulRNE(Int<32>(a),Int<32>(b)).get_data()[0]<<'\n';}
