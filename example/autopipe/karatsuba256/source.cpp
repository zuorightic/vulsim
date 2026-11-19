#include <fixint.hpp>
#pragma input_port a
Int<256> a;
#pragma input_port b
Int<256> b;
#pragma input_port c
Int<512> c;
#pragma input_port iv
bool iv;
#pragma output_port y
Int<513> y;
#pragma output_port ov
bool ov;
void workload_top() {
    Int<128> n0 = a.at<127,0>();
    Int<128> n1 = b.at<127,0>();
    Int<128> n2 = a.at<255,128>();
    Int<128> n3 = b.at<255,128>();
    Int<64> n4 = n0.at<63,0>();
    Int<64> n5 = n1.at<63,0>();
    Int<64> n6 = n0.at<127,64>();
    Int<64> n7 = n1.at<127,64>();
    Int<128> n8 = Int<128>(n4) * Int<128>(n5);
    Int<128> n9 = Int<128>(n6) * Int<128>(n7);
    Int<65> n10 = Int<65>(n4) + Int<65>(n6);
    Int<65> n11 = Int<65>(n5) + Int<65>(n7);
    Int<33> n12 = n10.at<32,0>();
    Int<33> n13 = n11.at<32,0>();
    Int<32> n14 = n10.at<64,33>();
    Int<32> n15 = n11.at<64,33>();
    Int<66> n16 = Int<66>(n12) * Int<66>(n13);
    Int<64> n17 = Int<64>(n14) * Int<64>(n15);
    Int<34> n18 = Int<34>(n12) + Int<34>(n14);
    Int<34> n19 = Int<34>(n13) + Int<34>(n15);
    Int<68> n20 = Int<68>(n18) * Int<68>(n19);
    Int<68> n21 = n20 - Int<68>(n16) - Int<68>(n17);
    Int<130> n22 = Int<130>(n16) + (Int<130>(n21) << 33) + (Int<130>(n17) << 66);
    Int<130> n23 = n22 - Int<130>(n8) - Int<130>(n9);
    Int<256> n24 = Int<256>(n8) + (Int<256>(n23) << 64) + (Int<256>(n9) << 128);
    Int<64> n25 = n2.at<63,0>();
    Int<64> n26 = n3.at<63,0>();
    Int<64> n27 = n2.at<127,64>();
    Int<64> n28 = n3.at<127,64>();
    Int<128> n29 = Int<128>(n25) * Int<128>(n26);
    Int<128> n30 = Int<128>(n27) * Int<128>(n28);
    Int<65> n31 = Int<65>(n25) + Int<65>(n27);
    Int<65> n32 = Int<65>(n26) + Int<65>(n28);
    Int<33> n33 = n31.at<32,0>();
    Int<33> n34 = n32.at<32,0>();
    Int<32> n35 = n31.at<64,33>();
    Int<32> n36 = n32.at<64,33>();
    Int<66> n37 = Int<66>(n33) * Int<66>(n34);
    Int<64> n38 = Int<64>(n35) * Int<64>(n36);
    Int<34> n39 = Int<34>(n33) + Int<34>(n35);
    Int<34> n40 = Int<34>(n34) + Int<34>(n36);
    Int<68> n41 = Int<68>(n39) * Int<68>(n40);
    Int<68> n42 = n41 - Int<68>(n37) - Int<68>(n38);
    Int<130> n43 = Int<130>(n37) + (Int<130>(n42) << 33) + (Int<130>(n38) << 66);
    Int<130> n44 = n43 - Int<130>(n29) - Int<130>(n30);
    Int<256> n45 = Int<256>(n29) + (Int<256>(n44) << 64) + (Int<256>(n30) << 128);
    Int<129> n46 = Int<129>(n0) + Int<129>(n2);
    Int<129> n47 = Int<129>(n1) + Int<129>(n3);
    Int<65> n48 = n46.at<64,0>();
    Int<65> n49 = n47.at<64,0>();
    Int<64> n50 = n46.at<128,65>();
    Int<64> n51 = n47.at<128,65>();
    Int<33> n52 = n48.at<32,0>();
    Int<33> n53 = n49.at<32,0>();
    Int<32> n54 = n48.at<64,33>();
    Int<32> n55 = n49.at<64,33>();
    Int<66> n56 = Int<66>(n52) * Int<66>(n53);
    Int<64> n57 = Int<64>(n54) * Int<64>(n55);
    Int<34> n58 = Int<34>(n52) + Int<34>(n54);
    Int<34> n59 = Int<34>(n53) + Int<34>(n55);
    Int<68> n60 = Int<68>(n58) * Int<68>(n59);
    Int<68> n61 = n60 - Int<68>(n56) - Int<68>(n57);
    Int<130> n62 = Int<130>(n56) + (Int<130>(n61) << 33) + (Int<130>(n57) << 66);
    Int<128> n63 = Int<128>(n50) * Int<128>(n51);
    Int<66> n64 = Int<66>(n48) + Int<66>(n50);
    Int<66> n65 = Int<66>(n49) + Int<66>(n51);
    Int<33> n66 = n64.at<32,0>();
    Int<33> n67 = n65.at<32,0>();
    Int<33> n68 = n64.at<65,33>();
    Int<33> n69 = n65.at<65,33>();
    Int<66> n70 = Int<66>(n66) * Int<66>(n67);
    Int<66> n71 = Int<66>(n68) * Int<66>(n69);
    Int<34> n72 = Int<34>(n66) + Int<34>(n68);
    Int<34> n73 = Int<34>(n67) + Int<34>(n69);
    Int<68> n74 = Int<68>(n72) * Int<68>(n73);
    Int<68> n75 = n74 - Int<68>(n70) - Int<68>(n71);
    Int<132> n76 = Int<132>(n70) + (Int<132>(n75) << 33) + (Int<132>(n71) << 66);
    Int<132> n77 = n76 - Int<132>(n62) - Int<132>(n63);
    Int<258> n78 = Int<258>(n62) + (Int<258>(n77) << 65) + (Int<258>(n63) << 130);
    Int<258> n79 = n78 - Int<258>(n24) - Int<258>(n45);
    Int<512> n80 = Int<512>(n24) + (Int<512>(n79) << 128) + (Int<512>(n45) << 256);
    Int<513> n81 = Int<513>(n80) + Int<513>(c);
    y = n81;
}
