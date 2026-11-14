#include <fixint.hpp>
#pragma input_port x0
Int<64> x0;
#pragma input_port x1
Int<64> x1;
#pragma input_port x2
Int<64> x2;
#pragma input_port x3
Int<64> x3;
#pragma input_port x4
Int<64> x4;
#pragma input_port x5
Int<64> x5;
#pragma input_port x6
Int<64> x6;
#pragma input_port x7
Int<64> x7;
#pragma input_port iv
bool iv;
#pragma output_port y0
Int<64> y0;
#pragma output_port y1
Int<64> y1;
#pragma output_port y2
Int<64> y2;
#pragma output_port y3
Int<64> y3;
#pragma output_port y4
Int<64> y4;
#pragma output_port y5
Int<64> y5;
#pragma output_port y6
Int<64> y6;
#pragma output_port y7
Int<64> y7;
#pragma output_port ov
bool ov;
void workload_top() {
    Int<64> n0 = Int<64>(18446744069414584321ULL);
    Int<65> n1 = ((Int<65>(1ULL) << 64) + Int<65>(4294967295ULL));
    Int<65> n2 = Int<65>(x0) + Int<65>(x4);
    Int<65> n3 = (n2 < Int<65>(n0)) ? n2 : (n2 - Int<65>(n0));
    Int<65> n4 = Int<65>(x0) + Int<65>(n0) - Int<65>(x4);
    Int<65> n5 = (n4 < Int<65>(n0)) ? n4 : (n4 - Int<65>(n0));
    Int<64> n6 = Int<64>(n3);
    Int<64> n7 = Int<64>(n5);
    Int<65> n8 = Int<65>(x2) + Int<65>(x6);
    Int<65> n9 = (n8 < Int<65>(n0)) ? n8 : (n8 - Int<65>(n0));
    Int<65> n10 = Int<65>(x2) + Int<65>(n0) - Int<65>(x6);
    Int<65> n11 = (n10 < Int<65>(n0)) ? n10 : (n10 - Int<65>(n0));
    Int<64> n12 = Int<64>(n9);
    Int<64> n13 = Int<64>(n11);
    Int<65> n14 = Int<65>(x1) + Int<65>(x5);
    Int<65> n15 = (n14 < Int<65>(n0)) ? n14 : (n14 - Int<65>(n0));
    Int<65> n16 = Int<65>(x1) + Int<65>(n0) - Int<65>(x5);
    Int<65> n17 = (n16 < Int<65>(n0)) ? n16 : (n16 - Int<65>(n0));
    Int<64> n18 = Int<64>(n15);
    Int<64> n19 = Int<64>(n17);
    Int<65> n20 = Int<65>(x3) + Int<65>(x7);
    Int<65> n21 = (n20 < Int<65>(n0)) ? n20 : (n20 - Int<65>(n0));
    Int<65> n22 = Int<65>(x3) + Int<65>(n0) - Int<65>(x7);
    Int<65> n23 = (n22 < Int<65>(n0)) ? n22 : (n22 - Int<65>(n0));
    Int<64> n24 = Int<64>(n21);
    Int<64> n25 = Int<64>(n23);
    Int<65> n26 = Int<65>(n6) + Int<65>(n12);
    Int<65> n27 = (n26 < Int<65>(n0)) ? n26 : (n26 - Int<65>(n0));
    Int<65> n28 = Int<65>(n6) + Int<65>(n0) - Int<65>(n12);
    Int<65> n29 = (n28 < Int<65>(n0)) ? n28 : (n28 - Int<65>(n0));
    Int<64> n30 = Int<64>(n27);
    Int<64> n31 = Int<64>(n29);
    Int<64> n32 = Int<64>(281474976710656ULL);
    Int<128> n33 = Int<128>(n13) * Int<128>(n32);
    Int<193> n34 = Int<193>(n33) * Int<193>(n1);
    Int<65> n35 = n34.at<192,128>();
    Int<129> n36 = Int<129>(n35) * Int<129>(n0);
    Int<129> n37 = Int<129>(n33) - n36;
    Int<129> n38 = (n37 < Int<129>(n0)) ? n37 : (n37 - Int<129>(n0));
    Int<64> n39 = Int<64>(n38);
    Int<65> n40 = Int<65>(n7) + Int<65>(n39);
    Int<65> n41 = (n40 < Int<65>(n0)) ? n40 : (n40 - Int<65>(n0));
    Int<65> n42 = Int<65>(n7) + Int<65>(n0) - Int<65>(n39);
    Int<65> n43 = (n42 < Int<65>(n0)) ? n42 : (n42 - Int<65>(n0));
    Int<64> n44 = Int<64>(n41);
    Int<64> n45 = Int<64>(n43);
    Int<65> n46 = Int<65>(n18) + Int<65>(n24);
    Int<65> n47 = (n46 < Int<65>(n0)) ? n46 : (n46 - Int<65>(n0));
    Int<65> n48 = Int<65>(n18) + Int<65>(n0) - Int<65>(n24);
    Int<65> n49 = (n48 < Int<65>(n0)) ? n48 : (n48 - Int<65>(n0));
    Int<64> n50 = Int<64>(n47);
    Int<64> n51 = Int<64>(n49);
    Int<64> n52 = Int<64>(281474976710656ULL);
    Int<128> n53 = Int<128>(n25) * Int<128>(n52);
    Int<193> n54 = Int<193>(n53) * Int<193>(n1);
    Int<65> n55 = n54.at<192,128>();
    Int<129> n56 = Int<129>(n55) * Int<129>(n0);
    Int<129> n57 = Int<129>(n53) - n56;
    Int<129> n58 = (n57 < Int<129>(n0)) ? n57 : (n57 - Int<129>(n0));
    Int<64> n59 = Int<64>(n58);
    Int<65> n60 = Int<65>(n19) + Int<65>(n59);
    Int<65> n61 = (n60 < Int<65>(n0)) ? n60 : (n60 - Int<65>(n0));
    Int<65> n62 = Int<65>(n19) + Int<65>(n0) - Int<65>(n59);
    Int<65> n63 = (n62 < Int<65>(n0)) ? n62 : (n62 - Int<65>(n0));
    Int<64> n64 = Int<64>(n61);
    Int<64> n65 = Int<64>(n63);
    Int<65> n66 = Int<65>(n30) + Int<65>(n50);
    Int<65> n67 = (n66 < Int<65>(n0)) ? n66 : (n66 - Int<65>(n0));
    Int<65> n68 = Int<65>(n30) + Int<65>(n0) - Int<65>(n50);
    Int<65> n69 = (n68 < Int<65>(n0)) ? n68 : (n68 - Int<65>(n0));
    Int<64> n70 = Int<64>(n67);
    Int<64> n71 = Int<64>(n69);
    Int<64> n72 = Int<64>(18446744069397807105ULL);
    Int<128> n73 = Int<128>(n64) * Int<128>(n72);
    Int<193> n74 = Int<193>(n73) * Int<193>(n1);
    Int<65> n75 = n74.at<192,128>();
    Int<129> n76 = Int<129>(n75) * Int<129>(n0);
    Int<129> n77 = Int<129>(n73) - n76;
    Int<129> n78 = (n77 < Int<129>(n0)) ? n77 : (n77 - Int<129>(n0));
    Int<64> n79 = Int<64>(n78);
    Int<65> n80 = Int<65>(n44) + Int<65>(n79);
    Int<65> n81 = (n80 < Int<65>(n0)) ? n80 : (n80 - Int<65>(n0));
    Int<65> n82 = Int<65>(n44) + Int<65>(n0) - Int<65>(n79);
    Int<65> n83 = (n82 < Int<65>(n0)) ? n82 : (n82 - Int<65>(n0));
    Int<64> n84 = Int<64>(n81);
    Int<64> n85 = Int<64>(n83);
    Int<64> n86 = Int<64>(281474976710656ULL);
    Int<128> n87 = Int<128>(n51) * Int<128>(n86);
    Int<193> n88 = Int<193>(n87) * Int<193>(n1);
    Int<65> n89 = n88.at<192,128>();
    Int<129> n90 = Int<129>(n89) * Int<129>(n0);
    Int<129> n91 = Int<129>(n87) - n90;
    Int<129> n92 = (n91 < Int<129>(n0)) ? n91 : (n91 - Int<129>(n0));
    Int<64> n93 = Int<64>(n92);
    Int<65> n94 = Int<65>(n31) + Int<65>(n93);
    Int<65> n95 = (n94 < Int<65>(n0)) ? n94 : (n94 - Int<65>(n0));
    Int<65> n96 = Int<65>(n31) + Int<65>(n0) - Int<65>(n93);
    Int<65> n97 = (n96 < Int<65>(n0)) ? n96 : (n96 - Int<65>(n0));
    Int<64> n98 = Int<64>(n95);
    Int<64> n99 = Int<64>(n97);
    Int<64> n100 = Int<64>(18446742969902956801ULL);
    Int<128> n101 = Int<128>(n65) * Int<128>(n100);
    Int<193> n102 = Int<193>(n101) * Int<193>(n1);
    Int<65> n103 = n102.at<192,128>();
    Int<129> n104 = Int<129>(n103) * Int<129>(n0);
    Int<129> n105 = Int<129>(n101) - n104;
    Int<129> n106 = (n105 < Int<129>(n0)) ? n105 : (n105 - Int<129>(n0));
    Int<64> n107 = Int<64>(n106);
    Int<65> n108 = Int<65>(n45) + Int<65>(n107);
    Int<65> n109 = (n108 < Int<65>(n0)) ? n108 : (n108 - Int<65>(n0));
    Int<65> n110 = Int<65>(n45) + Int<65>(n0) - Int<65>(n107);
    Int<65> n111 = (n110 < Int<65>(n0)) ? n110 : (n110 - Int<65>(n0));
    Int<64> n112 = Int<64>(n109);
    Int<64> n113 = Int<64>(n111);
    y0 = n70;
    y1 = n84;
    y2 = n98;
    y3 = n112;
    y4 = n71;
    y5 = n85;
    y6 = n99;
    y7 = n113;
}
