# 未完成后端测量项：ABCD的实际RTL拆分与寄存器

快照：2026-11-16 18:07:23 +08:00。

只解释已冻结选中RTL；失败、运行中和未启动都属于尚无合格完整实测。尚未冻结的项目单列，不用中间候选代替最终RTL。
A实际L=1，保留原数学源中的算法展开和原子操作；B不切原子算术，只在它们之间放寄存器；C用静态表选结构／位置；D用本体预算→等效训练T→冻结模型选结构／位置。C/D都可以选不进一步拆分。
块宽b表示将现有乘法展开为b位小乘（末块可更窄）、固定移位和归约树；limb w表示按位段生成add/sub/ADC及进位依赖，高位操作数、carry和部分结果按周期对齐。b=0/w=0是没有继续切对应算术；Karatsuba和NTT源中的算法展开仍存在。
下表逻辑级采用0起编号。每级后capture s=k+1；s=L是外部输出capture，已经计入L。完整图和放置表确定每个节点的所在级；跨级值会被保存，必要时逐级传递。数据位数采用variable_bits，不把已知零位当作触发器位。
服务外壳还含输入保存寄存器l_*及liv，额外服务输入偏移为1周期；它与内部流水寄存器及最终y/ov capture在RTL中分别定位。enable按前级valid、异步／同步reset和保持行为以实际RTL为准。

| 案例 | 比较L/T ps | 方法 | 后端状态 | 实际L | 乘法块/加法limb | 冻结RTL |
| --- | --- | --- | --- | ---: | --- | --- |
| mac32 | 2/950 | A | not_started | 1 | 0/0 | [实现 073243214bc6](#rtl-073243214bc6) |
| mac32 | 2/950 | B | not_started | 2 | 0/0 | [实现 c218c9843815](#rtl-c218c9843815) |
| mac32 | 2/950 | C | not_started | 2 | 8/0 | [实现 1ae18b2a6206](#rtl-1ae18b2a6206) |
| mac32 | 2/950 | D | not_started | 2 | 8/0 | [实现 1ae18b2a6206](#rtl-1ae18b2a6206) |
| mac32 | 2/1100 | A | not_started | 1 | 0/0 | [实现 073243214bc6](#rtl-073243214bc6) |
| mac32 | 2/1100 | B | not_started | 2 | 0/0 | [实现 c218c9843815](#rtl-c218c9843815) |
| mac32 | 2/1100 | C | not_started | 2 | 8/0 | [实现 1ae18b2a6206](#rtl-1ae18b2a6206) |
| mac32 | 2/1100 | D | not_started | 2 | 16/0 | [实现 dce41e76e019](#rtl-dce41e76e019) |
| mul128 | 2/1200 | A | not_started | 1 | 0/0 | [实现 6d72e638cd85](#rtl-6d72e638cd85) |
| mul128 | 2/1200 | B | not_started | 2 | 0/0 | [实现 78f923426662](#rtl-78f923426662) |
| mul128 | 2/1200 | C | not_started | 2 | 8/0 | [实现 a2c5d3c0f979](#rtl-a2c5d3c0f979) |
| mul128 | 2/1200 | D | not_started | 2 | 16/0 | [实现 797e2a4ef532](#rtl-797e2a4ef532) |
| mul128 | 2/1450 | A | not_started | 1 | 0/0 | [实现 6d72e638cd85](#rtl-6d72e638cd85) |
| mul128 | 2/1450 | B | not_started | 2 | 0/0 | [实现 78f923426662](#rtl-78f923426662) |
| mul128 | 2/1450 | C | not_started | 2 | 8/0 | [实现 a2c5d3c0f979](#rtl-a2c5d3c0f979) |
| mul128 | 2/1450 | D | not_started | 2 | 32/0 | [实现 4cb62746f4c5](#rtl-4cb62746f4c5) |
| mul128 | 4/600 | C | not_started | 4 | 4/0 | [实现 78374d7545b6](#rtl-78374d7545b6) |
| mul128 | 4/600 | D | not_started | 4 | 4/0 | [实现 78374d7545b6](#rtl-78374d7545b6) |
| mul128 | 4/750 | C | not_started | 4 | 4/0 | [实现 78374d7545b6](#rtl-78374d7545b6) |
| mul128 | 4/750 | D | not_started | 4 | 4/0 | [实现 78374d7545b6](#rtl-78374d7545b6) |
| dot16 | 4/850 | A | failed | 1 | 0/0 | [实现 2776e286ec00](#rtl-2776e286ec00) |
| dot16 | 4/850 | B | failed | 4 | 0/0 | [实现 5d322a4d43a9](#rtl-5d322a4d43a9) |
| dot16 | 4/850 | C | failed | 4 | 8/0 | [实现 8327002228a5](#rtl-8327002228a5) |
| dot16 | 4/850 | D | failed | 4 | 8/0 | [实现 13041929dd25](#rtl-13041929dd25) |
| dot16 | 4/1050 | A | failed | 1 | 0/0 | [实现 2776e286ec00](#rtl-2776e286ec00) |
| dot16 | 4/1050 | B | failed | 4 | 0/0 | [实现 5d322a4d43a9](#rtl-5d322a4d43a9) |
| dot16 | 4/1050 | C | failed | 4 | 8/0 | [实现 8327002228a5](#rtl-8327002228a5) |
| dot16 | 4/1050 | D | failed | 4 | 8/0 | [实现 13041929dd25](#rtl-13041929dd25) |
| dot16 | 5/700 | A | failed | 1 | 0/0 | [实现 2776e286ec00](#rtl-2776e286ec00) |
| dot16 | 5/700 | B | failed | 5 | 0/0 | [实现 8bbe5fa52f58](#rtl-8bbe5fa52f58) |
| dot16 | 5/700 | C | failed | 5 | 8/64 | [实现 b6a28e166624](#rtl-b6a28e166624) |
| dot16 | 5/700 | D | failed | 5 | 16/0 | [实现 4c2ee7748c79](#rtl-4c2ee7748c79) |
| dot16 | 5/850 | A | failed | 1 | 0/0 | [实现 2776e286ec00](#rtl-2776e286ec00) |
| dot16 | 5/850 | B | failed | 5 | 0/0 | [实现 8bbe5fa52f58](#rtl-8bbe5fa52f58) |
| dot16 | 5/850 | C | running | 5 | 8/64 | [实现 b6a28e166624](#rtl-b6a28e166624) |
| dot16 | 5/850 | D | running | 5 | 16/0 | [实现 4c2ee7748c79](#rtl-4c2ee7748c79) |
| horner64 | 4/1900 | A | running | 1 | 0/0 | [实现 6c415b9cf3b2](#rtl-6c415b9cf3b2) |
| horner64 | 4/2250 | A | running | 1 | 0/0 | [实现 6c415b9cf3b2](#rtl-6c415b9cf3b2) |
| horner64 | 4/2250 | C | running | 4 | 8/0 | [实现 c4d9a155e3c4](#rtl-c4d9a155e3c4) |
| horner64 | 8/1150 | D | not_started | 8 | 16/0 | [实现 4f83e78449a4](#rtl-4f83e78449a4) |
| barrett64 | 4/1800 | A | failed | 1 | 0/0 | [实现 fe0456a5a32c](#rtl-fe0456a5a32c) |
| barrett64 | 4/2150 | A | running | 1 | 0/0 | [实现 fe0456a5a32c](#rtl-fe0456a5a32c) |
| barrett64 | 4/2150 | C | running | 4 | 8/0 | [实现 83a434da7745](#rtl-83a434da7745) |
| barrett64 | 8/900 | A | failed | 1 | 0/0 | [实现 fe0456a5a32c](#rtl-fe0456a5a32c) |
| barrett64 | 8/1100 | A | failed | 1 | 0/0 | [实现 fe0456a5a32c](#rtl-fe0456a5a32c) |
| karatsuba256 | 4/2300 | A | not_started | 1 | 0/0 | [实现 c1a64d59e07d](#rtl-c1a64d59e07d) |
| karatsuba256 | 4/2300 | B | not_started | 4 | 0/0 | [实现 afb74d898573](#rtl-afb74d898573) |
| karatsuba256 | 4/2300 | C | not_started | 4 | 8/0 | [实现 1de0ecb23206](#rtl-1de0ecb23206) |
| karatsuba256 | 4/2300 | D | not_started | 4 | 0/0 | [实现 8f7d78972cbb](#rtl-8f7d78972cbb) |
| karatsuba256 | 4/2750 | A | not_started | 1 | 0/0 | [实现 c1a64d59e07d](#rtl-c1a64d59e07d) |
| karatsuba256 | 4/2750 | B | not_started | 4 | 0/0 | [实现 afb74d898573](#rtl-afb74d898573) |
| karatsuba256 | 4/2750 | C | not_started | 4 | 8/0 | [实现 1de0ecb23206](#rtl-1de0ecb23206) |
| karatsuba256 | 4/2750 | D | not_started | 4 | 0/0 | [实现 8f7d78972cbb](#rtl-8f7d78972cbb) |
| karatsuba256 | 8/1150 | A | not_started | 1 | 0/0 | [实现 c1a64d59e07d](#rtl-c1a64d59e07d) |
| karatsuba256 | 8/1150 | B | not_started | 8 | 0/0 | [实现 d82729a2bd2b](#rtl-d82729a2bd2b) |
| karatsuba256 | 8/1150 | C | not_started | 8 | 8/0 | [实现 f3011704032a](#rtl-f3011704032a) |
| karatsuba256 | 8/1150 | D | not_started | 8 | 0/0 | [实现 b5e7a118e6c3](#rtl-b5e7a118e6c3) |
| karatsuba256 | 8/1400 | A | not_started | 1 | 0/0 | [实现 c1a64d59e07d](#rtl-c1a64d59e07d) |
| karatsuba256 | 8/1400 | B | not_started | 8 | 0/0 | [实现 d82729a2bd2b](#rtl-d82729a2bd2b) |
| karatsuba256 | 8/1400 | C | not_started | 8 | 8/0 | [实现 f3011704032a](#rtl-f3011704032a) |
| karatsuba256 | 8/1400 | D | not_started | 8 | 0/0 | [实现 b5e7a118e6c3](#rtl-b5e7a118e6c3) |
| montgomery256 | 16/待定 | A | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 16/待定 | B | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 16/待定 | C | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 16/待定 | D | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 16/待定 | A | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 16/待定 | B | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 16/待定 | C | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 16/待定 | D | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 32/待定 | A | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 32/待定 | B | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 32/待定 | C | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 32/待定 | D | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 32/待定 | A | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 32/待定 | B | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 32/待定 | C | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| montgomery256 | 32/待定 | D | awaiting_A_reference | — | 待冻结 | 尚无最终RTL |
| ntt8x64 | 8/1550 | A | not_registered | — | 待冻结 | 尚无最终RTL |
| ntt8x64 | 8/1550 | B | not_registered | — | 待冻结 | 尚无最终RTL |
| ntt8x64 | 8/1550 | C | not_registered | — | 待冻结 | 尚无最终RTL |
| ntt8x64 | 8/1550 | D | not_registered | — | 待冻结 | 尚无最终RTL |
| ntt8x64 | 8/1850 | A | not_registered | — | 待冻结 | 尚无最终RTL |
| ntt8x64 | 8/1850 | B | not_registered | — | 待冻结 | 尚无最终RTL |
| ntt8x64 | 8/1850 | C | not_registered | — | 待冻结 | 尚无最终RTL |
| ntt8x64 | 8/1850 | D | not_registered | — | 待冻结 | 尚无最终RTL |
| ntt8x64 | 16/800 | A | not_started | 1 | 0/0 | [实现 0cc5456aa719](#rtl-0cc5456aa719) |
| ntt8x64 | 16/800 | B | not_started | 16 | 0/0 | [实现 4b0b80f5dba8](#rtl-4b0b80f5dba8) |
| ntt8x64 | 16/800 | C | not_started | 16 | 8/0 | [实现 ada50437924b](#rtl-ada50437924b) |
| ntt8x64 | 16/800 | D | not_started | 16 | 0/0 | [实现 a6689a6712c6](#rtl-a6689a6712c6) |
| ntt8x64 | 16/950 | A | not_started | 1 | 0/0 | [实现 0cc5456aa719](#rtl-0cc5456aa719) |
| ntt8x64 | 16/950 | B | not_started | 16 | 0/0 | [实现 4b0b80f5dba8](#rtl-4b0b80f5dba8) |
| ntt8x64 | 16/950 | C | not_started | 16 | 8/0 | [实现 ada50437924b](#rtl-ada50437924b) |
| ntt8x64 | 16/950 | D | not_started | 16 | 0/0 | [实现 a6689a6712c6](#rtl-a6689a6712c6) |

<a id="rtl-073243214bc6"></a>

## 实现 073243214bc6：L1，块/limb=[0, 0]

对应记录：mac32 L2 T950 A（not_started）；mac32 L2 T1100 A（not_started）；mac32 L3 T500 A（measured_grt）；mac32 L3 T750 A（measured_grt）；mac32 L3 T1000 A（measured_grt）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mac32/T1000-L1/A/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mac32/T1000-L1/A/workload.sv:53)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(64,64)->64 ×1; mul(32,32)->64 ×1 | — | 64/1 | [y←#6 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mac32/T1000-L1/A/workload.sv:60); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mac32/T1000-L1/A/workload.sv:60) |

全部2个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-0cc5456aa719"></a>

## 实现 0cc5456aa719：L1，块/limb=[0, 0]

对应记录：ntt8x64 L16 T800 A（not_started）；ntt8x64 L16 T950 A（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L1/A/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L1/A/workload.sv:2153)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(64,64)->65 ×4; ult(65,65)->1 ×24; sub(65,65)->65 ×24; mux(65,65)->65 ×16; add(64,65)->65 ×4; sub(65,64)->65 ×4; add(65,65)->65 ×16; sub(129,129)->129 ×5; ult(129,129)->1 ×5; sub(129,129)->65 ×5; mux(129,129)->65 ×5; sub(65,65)->64 ×8; mux(65,65)->64 ×8; mul(64,49)->113 ×3; mul(128,65)->193 ×5; mul(65,64)->129 ×5; mul(64,64)->128 ×2 | — | 512/1 | [y0←#209 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L1/A/workload.sv:2172); [y1←#210 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L1/A/workload.sv:2172); [y2←#211 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L1/A/workload.sv:2172) |

全部9个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-13041929dd25"></a>

## 实现 13041929dd25：L4，块/limb=[8, 0]

对应记录：dot16 L4 T850 D（failed）；dot16 L4 T1050 D（failed）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:30132)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(8,8)->16 ×1024 | — | 16384/1 | [rtlzz_pipe_1038_s1←#1038 mul（16位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:15995); [rtlzz_pipe_1042_s1←#1042 concat（16位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:15998); [rtlzz_pipe_1046_s1←#1046 concat（16位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:16001) |
| 1 | 无独立正价算术 | 64项/128bit ×16 | 2048/1 | [rtlzz_pipe_33_s2←#33 wire（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:15797); [rtlzz_pipe_34_s2←#34 wire（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:15992); [rtlzz_pipe_35_s2←#35 wire（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:16187) |
| 2 | 无独立正价算术 | 4项/130bit ×4 | 520/1 | [rtlzz_pipe_57_s3←#57 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:16385); [rtlzz_pipe_58_s3←#58 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:17168); [rtlzz_pipe_59_s3←#59 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:17951) |
| 3 | 无独立正价算术 | 4项/132bit ×1 | 132/1 | [y←#64 wire（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:30168); [ov←#32 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/D/workload.sv:30168) |

全部1049个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-1ae18b2a6206"></a>

## 实现 1ae18b2a6206：L2，块/limb=[8, 0]

对应记录：mac32 L2 T950 C（not_started）；mac32 L2 T950 D（not_started）；mac32 L2 T1100 C（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/C/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/C/workload.sv:512)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(8,8)->16 ×16 | — | 320/1 | [rtlzz_pipe_2_s1←#2 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/C/workload.sv:275); [rtlzz_pipe_15_s1←#15 mul（16位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/C/workload.sv:278); [rtlzz_pipe_19_s1←#19 concat（16位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/C/workload.sv:281) |
| 1 | 无独立正价算术 | 17项/64bit ×1 | 64/1 | [y←#6 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/C/workload.sv:519); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/C/workload.sv:519) |

全部20个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-1de0ecb23206"></a>

## 实现 1de0ecb23206：L4，块/limb=[8, 0]

对应记录：karatsuba256 L4 T2300 C（not_started）；karatsuba256 L4 T2750 C（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:17606)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(65,65)->65 ×4; add(34,34)->34 ×8; add(129,129)->129 ×2; add(66,66)->66 ×2; mul(8,8)->16 ×512; mul(8,1)->9 ×20; mul(1,8)->9 ×20; mul(1,1)->2 ×5; mul(8,2)->10 ×16; mul(2,8)->10 ×16; mul(2,2)->4 ×4; add(16,24)->25 ×5; add(32,40)->41 ×15; add(42,24)->43 ×3; add(48,50)->51 ×3; add(48,56)->57 ×10; add(58,40)->59 ×3; add(64,66)->67 ×3; add(42,50)->51 ×3; add(58,66)->67 ×3; add(41,24)->42 ×2; add(48,49)->50 ×2; add(57,40)->58 ×2; add(64,65)->66 ×2; add(41,49)->50 ×2; add(57,65)->66 ×2 | 4项/128bit ×1; 4项/98bit ×2; 4项/122bit ×1; 4项/90bit ×2; 4项/114bit ×1; 4项/82bit ×2; 4项/106bit ×1; 4项/74bit ×2; 4项/66bit ×7; 4项/58bit ×4; 4项/50bit ×4; 4项/42bit ×7; 4项/64bit ×3; 4项/59bit ×3; 4项/51bit ×3; 4项/43bit ×3; 8项/128bit ×4; 8项/123bit ×4; 8项/115bit ×4; 8项/107bit ×4; 8项/99bit ×4; 8项/91bit ×4; 8项/83bit ×4; 8项/75bit ×4 | 10169/1 | [rtlzz_pipe_156_s1←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:8888); [rtlzz_pipe_1227_s1←#1227 adc（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:8945); [rtlzz_pipe_2125_s1←#2125 adc（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:9050) |
| 1 | sub(68,68)->68 ×8; add(256,256)->256 ×2; add(132,132)->132 ×1 | 16项/128bit ×1; 3项/130bit ×3; 13项/66bit ×2; 25项/68bit ×1; 4项/64bit ×3; 7项/66bit ×3; 13项/68bit ×3; 8项/128bit ×4 | 2706/1 | [rtlzz_pipe_156_s2←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:8891); [rtlzz_pipe_145_s2←#145 shl（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:9290); [rtlzz_pipe_220_s2←#220 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:9083) |
| 2 | sub(130,130)->130 ×4; sub(132,130)->132 ×1; sub(132,132)->132 ×1; sub(258,256)->258 ×2; add(256,256)->256 ×2; add(132,132)->132 ×1 | 3项/512bit ×1; 3项/258bit ×1 | 1024/1 | [rtlzz_pipe_155_s3←#155 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:9452); [rtlzz_pipe_156_s3←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:8894); [rtlzz_valid_s3←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:9456) |
| 3 | add(512,512)->513 ×1 | — | 513/1 | [y←#158 wire（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:17613); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/C/workload.sv:17613) |

其他功能逻辑另列在详细JSON中，不因算术表为空而忽略。

全部194个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-2776e286ec00"></a>

## 实现 2776e286ec00：L1，块/limb=[0, 0]

对应记录：dot16 L4 T850 A（failed）；dot16 L4 T1050 A（failed）；dot16 L5 T700 A（failed）；dot16 L5 T850 A（failed）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L1/A/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L1/A/workload.sv:436)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(64,64)->128 ×16 | 16项/132bit ×1 | 132/1 | [y←#64 wire（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L1/A/workload.sv:472); [ov←#32 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L1/A/workload.sv:472) |

全部2个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-4b0b80f5dba8"></a>

## 实现 4b0b80f5dba8：L16，块/limb=[0, 0]

对应记录：ntt8x64 L16 T800 B（not_started）；ntt8x64 L16 T950 B（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:2955)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(64,64)->65 ×4; ult(65,65)->1 ×14; sub(65,65)->65 ×15; mux(65,65)->65 ×12; add(64,65)->65 ×4; sub(65,64)->65 ×4; add(65,65)->65 ×9; sub(65,65)->64 ×2; mux(65,65)->64 ×2; mul(64,49)->113 ×3 | — | 1193/1 | [rtlzz_pipe_105_s1←#105 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1185); [rtlzz_pipe_166_s1←#166 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1275); [rtlzz_pipe_256_s1←#256 slice（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1140) |
| 1 | mul(128,65)->193 ×3 | — | 1049/1 | [rtlzz_pipe_105_s2←#105 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1188); [rtlzz_pipe_166_s2←#166 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1278); [rtlzz_pipe_71_s2←#71 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1134) |
| 2 | mul(65,64)->129 ×3 | — | 1241/1 | [rtlzz_pipe_104_s3←#104 wire（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1200); [rtlzz_pipe_165_s3←#165 wire（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1290); [rtlzz_pipe_70_s3←#70 wire（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1146) |
| 3 | sub(129,129)->129 ×3; ult(129,129)->1 ×3; sub(129,129)->65 ×3; mux(129,129)->65 ×3; add(65,65)->65 ×5; ult(65,65)->1 ×6; sub(65,65)->65 ×7; mux(65,65)->65 ×4; sub(65,65)->64 ×2; mux(65,65)->64 ×2; mul(64,64)->128 ×2 | — | 1026/1 | [rtlzz_pipe_141_s4←#141 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1203); [rtlzz_pipe_191_s4←#191 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1365); [rtlzz_pipe_274_s4←#274 slice（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1212) |
| 4 | mul(128,65)->193 ×2 | — | 900/1 | [rtlzz_pipe_141_s5←#141 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1206); [rtlzz_pipe_191_s5←#191 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1368); [rtlzz_pipe_152_s5←#152 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1161) |
| 5 | mul(65,64)->129 ×2 | — | 1028/1 | [rtlzz_pipe_140_s6←#140 wire（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1218); [rtlzz_pipe_190_s6←#190 wire（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1380); [rtlzz_pipe_141_s6←#141 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1209) |
| 6 | sub(129,129)->129 ×2; ult(129,129)->1 ×2; sub(129,129)->65 ×2; mux(129,129)->65 ×2; add(65,65)->65 ×2; ult(65,65)->1 ×4; sub(65,65)->64 ×4; mux(65,65)->64 ×4; sub(65,65)->65 ×2 | — | 512/1 | [rtlzz_pipe_132_s7←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1041); [rtlzz_pipe_133_s7←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1086); [rtlzz_pipe_157_s7←#157 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1221) |
| 7 | 无独立正价算术 | — | 512/1 | [rtlzz_pipe_132_s8←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1044); [rtlzz_pipe_133_s8←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1089); [rtlzz_pipe_157_s8←#157 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1224) |
| 8 | 无独立正价算术 | — | 512/1 | [rtlzz_pipe_132_s9←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1047); [rtlzz_pipe_133_s9←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1092); [rtlzz_pipe_157_s9←#157 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1227) |
| 9 | 无独立正价算术 | — | 512/1 | [rtlzz_pipe_132_s10←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1050); [rtlzz_pipe_133_s10←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1095); [rtlzz_pipe_157_s10←#157 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1230) |
| 10 | 无独立正价算术 | — | 512/1 | [rtlzz_pipe_132_s11←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1053); [rtlzz_pipe_133_s11←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1098); [rtlzz_pipe_157_s11←#157 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1233) |
| 11 | 无独立正价算术 | — | 512/1 | [rtlzz_pipe_132_s12←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1056); [rtlzz_pipe_133_s12←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1101); [rtlzz_pipe_157_s12←#157 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1236) |
| 12 | 无独立正价算术 | — | 512/1 | [rtlzz_pipe_132_s13←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1059); [rtlzz_pipe_133_s13←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1104); [rtlzz_pipe_157_s13←#157 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1239) |
| 13 | 无独立正价算术 | — | 512/1 | [rtlzz_pipe_132_s14←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1062); [rtlzz_pipe_133_s14←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1107); [rtlzz_pipe_157_s14←#157 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1242) |
| 14 | 无独立正价算术 | — | 512/1 | [rtlzz_pipe_132_s15←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1065); [rtlzz_pipe_133_s15←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1110); [rtlzz_pipe_157_s15←#157 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:1245) |
| 15 | 无独立正价算术 | — | 512/1 | [y0←#209 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:2974); [y1←#210 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:2974); [y2←#211 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/B/workload.sv:2974) |

全部174个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-4c2ee7748c79"></a>

## 实现 4c2ee7748c79：L5，块/limb=[16, 0]

对应记录：dot16 L5 T700 D（failed）；dot16 L5 T850 D（running）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:8307)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(16,16)->32 ×256 | — | 8192/1 | [rtlzz_pipe_1020_s1←#1020 mul（32位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:4652); [rtlzz_pipe_1024_s1←#1024 concat（32位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:4655); [rtlzz_pipe_1028_s1←#1028 concat（32位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:4658) |
| 1 | 无独立正价算术 | 8项/128bit ×16; 8项/99bit ×16 | 3680/1 | [rtlzz_pipe_1013_s2←#1013 adc（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:4643); [rtlzz_pipe_1122_s2←#1122 adc（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:4703); [rtlzz_pipe_1231_s2←#1231 adc（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:4760) |
| 2 | add(99,131)->128 ×16 | — | 2048/1 | [rtlzz_pipe_33_s3←#33 wire（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:4247); [rtlzz_pipe_34_s3←#34 wire（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:4304); [rtlzz_pipe_35_s3←#35 wire（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:4361) |
| 3 | 无独立正价算术 | 8项/131bit ×2 | 262/1 | [rtlzz_pipe_61_s4←#61 add（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:4649); [rtlzz_pipe_62_s4←#62 add（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:5108); [rtlzz_valid_s4←#32 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:5113) |
| 4 | add(131,131)->132 ×1 | — | 132/1 | [y←#64 wire（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:8343); [ov←#32 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/D/workload.sv:8343) |

全部312个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-4cb62746f4c5"></a>

## 实现 4cb62746f4c5：L2，块/limb=[32, 0]

对应记录：mul128 L2 T1450 D（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/D/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/D/workload.sv:504)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(32,32)->64 ×16 | — | 1024/1 | [rtlzz_pipe_13_s1←#13 mul（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/D/workload.sv:271); [rtlzz_pipe_17_s1←#17 concat（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/D/workload.sv:274); [rtlzz_pipe_21_s1←#21 concat（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/D/workload.sv:277) |
| 1 | 无独立正价算术 | 16项/256bit ×1 | 256/1 | [y←#4 wire（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/D/workload.sv:510); [ov←#2 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/D/workload.sv:510) |

全部19个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-4f83e78449a4"></a>

## 实现 4f83e78449a4：L8，块/limb=[16, 0]

对应记录：horner64 L8 T950 D（measured_grt）；horner64 L8 T1150 D（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1810)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(16,16)->32 ×6; mul(16,16)->16 ×4 | — | 832/1 | [rtlzz_pipe_0_s1←#0 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1069); [rtlzz_pipe_1_s1←#1 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1087); [rtlzz_pipe_2_s1←#2 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1108) |
| 1 | 无独立正价算术 | 11项/64bit ×1 | 320/1 | [rtlzz_pipe_0_s2←#0 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1072); [rtlzz_pipe_1_s2←#1 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1090); [rtlzz_pipe_2_s2←#2 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1111) |
| 2 | mul(16,16)->32 ×6; mul(16,16)->16 ×4 | — | 768/1 | [rtlzz_pipe_0_s3←#0 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1075); [rtlzz_pipe_1_s3←#1 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1093); [rtlzz_pipe_2_s3←#2 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1114) |
| 3 | 无独立正价算术 | 11项/64bit ×1 | 256/1 | [rtlzz_pipe_0_s4←#0 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1078); [rtlzz_pipe_10_s4←#10 add（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1234); [rtlzz_pipe_1_s4←#1 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1096) |
| 4 | mul(16,16)->32 ×6; mul(16,16)->16 ×4 | — | 704/1 | [rtlzz_pipe_0_s5←#0 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1081); [rtlzz_pipe_1_s5←#1 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1099); [rtlzz_pipe_2_s5←#2 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1120) |
| 5 | 无独立正价算术 | 11项/64bit ×1 | 192/1 | [rtlzz_pipe_0_s6←#0 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1084); [rtlzz_pipe_12_s6←#12 add（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1285); [rtlzz_pipe_1_s6←#1 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1102) |
| 6 | mul(16,16)->32 ×6; mul(16,16)->16 ×4 | — | 576/1 | [rtlzz_pipe_1_s7←#1 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1105); [rtlzz_pipe_350_s7←#350 mul（32位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1288); [rtlzz_pipe_354_s7←#354 concat（32位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1291) |
| 7 | 无独立正价算术 | 11项/64bit ×1 | 64/1 | [y←#15 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1820); [ov←#6 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L8/D/workload.sv:1820) |

全部98个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-5d322a4d43a9"></a>

## 实现 5d322a4d43a9：L4，块/limb=[0, 0]

对应记录：dot16 L4 T850 B（failed）；dot16 L4 T1050 B（failed）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:680)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(128,128)->129 ×8; mul(64,64)->128 ×16 | — | 1032/1 | [rtlzz_pipe_49_s1←#49 add（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:307); [rtlzz_pipe_50_s1←#50 add（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:310); [rtlzz_pipe_51_s1←#51 add（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:316) |
| 1 | add(129,129)->130 ×4 | — | 520/1 | [rtlzz_pipe_57_s2←#57 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:313); [rtlzz_pipe_58_s2←#58 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:322); [rtlzz_pipe_59_s2←#59 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:334) |
| 2 | add(130,130)->131 ×2 | — | 262/1 | [rtlzz_pipe_61_s3←#61 add（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:325); [rtlzz_pipe_62_s3←#62 add（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:346); [rtlzz_valid_s3←#32 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:350) |
| 3 | add(131,131)->132 ×1 | — | 132/1 | [y←#64 wire（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:716); [ov←#32 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/B/workload.sv:716) |

全部19个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-6c415b9cf3b2"></a>

## 实现 6c415b9cf3b2：L1，块/limb=[0, 0]

对应记录：horner64 L4 T1900 A（running）；horner64 L4 T2250 A（running）；horner64 L8 T950 A（measured_grt）；horner64 L8 T1150 A（measured_grt）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L1/A/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L1/A/workload.sv:129)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(64,64)->64 ×4; mul(64,64)->64 ×4 | — | 64/1 | [y←#15 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L1/A/workload.sv:139); [ov←#6 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/horner64/T1150-L1/A/workload.sv:139) |

全部2个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-6d72e638cd85"></a>

## 实现 6d72e638cd85：L1，块/limb=[0, 0]

对应记录：mul128 L2 T1200 A（not_started）；mul128 L2 T1450 A（not_started）；mul128 L4 T600 A（measured_grt）；mul128 L4 T750 A（measured_grt）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L1/A/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L1/A/workload.sv:39)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(128,128)->256 ×1 | — | 256/1 | [y←#4 wire（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L1/A/workload.sv:45); [ov←#2 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L1/A/workload.sv:45) |

全部2个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-78374d7545b6"></a>

## 实现 78374d7545b6：L4，块/limb=[4, 0]

对应记录：mul128 L4 T600 C（not_started）；mul128 L4 T600 D（not_started）；mul128 L4 T750 C（not_started）；mul128 L4 T750 D（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:33679)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(4,4)->8 ×1024; add(8,12)->13 ×1; add(16,20)->21 ×2; add(24,28)->29 ×3; add(32,36)->37 ×4; add(40,44)->45 ×5; add(48,52)->53 ×6; add(56,60)->61 ×7; add(64,68)->69 ×8; add(72,76)->77 ×9; add(80,84)->85 ×10; add(88,92)->93 ×11; add(96,100)->101 ×12; add(104,108)->109 ×13; add(112,116)->117 ×14; add(120,124)->125 ×15; add(128,132)->133 ×16; add(12,16)->17 ×1; add(20,24)->25 ×2; add(28,32)->33 ×3; add(36,40)->41 ×4; add(44,48)->49 ×5; add(52,56)->57 ×6; add(60,64)->65 ×7; add(68,72)->73 ×8; add(76,80)->81 ×9; add(84,88)->89 ×10; add(92,96)->97 ×11; add(100,104)->105 ×12; add(108,112)->113 ×13; add(116,120)->121 ×14; add(124,128)->129 ×15; add(132,136)->137 ×16; add(136,140)->141 ×15; add(140,144)->145 ×15; add(144,148)->149 ×14; add(148,152)->153 ×14; add(152,156)->157 ×13; add(156,160)->161 ×13; add(160,164)->165 ×12; add(164,168)->169 ×12; add(168,172)->173 ×11; add(172,176)->177 ×11; add(176,180)->181 ×10; add(180,184)->185 ×10; add(184,188)->189 ×9; add(188,192)->193 ×9; add(192,196)->197 ×8; add(196,200)->201 ×8; add(200,204)->205 ×7; add(204,208)->209 ×7; add(208,212)->213 ×6; add(212,216)->217 ×6; add(216,220)->221 ×5; add(220,224)->225 ×5; add(224,228)->229 ×4; add(228,232)->233 ×4; add(232,236)->237 ×3; add(236,240)->241 ×3; add(240,244)->245 ×2; add(244,248)->249 ×2; add(248,252)->253 ×1; add(252,256)->256 ×1 | — | 69120/1 | [rtlzz_pipe_5641_s1←#5641 adc（257位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:16633); [rtlzz_pipe_5593_s1←#5593 adc（253位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:16585); [rtlzz_pipe_5545_s1←#5545 adc（249位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:16537) |
| 1 | 无独立正价算术 | 8项/256bit ×2; 8项/196bit ×2; 8项/192bit ×2; 8项/252bit ×1; 8项/188bit ×2; 8项/248bit ×1; 8项/184bit ×2; 8项/244bit ×1; 8项/180bit ×2; 8项/240bit ×1; 8项/176bit ×2; 8项/236bit ×1; 8项/172bit ×2; 8项/232bit ×1; 8项/168bit ×2; 8项/228bit ×1; 8项/164bit ×2; 8项/224bit ×1; 8项/160bit ×2; 8项/220bit ×1; 8项/156bit ×2; 8项/216bit ×1; 8项/152bit ×2; 8项/212bit ×1; 8项/148bit ×2; 8项/208bit ×1; 8项/144bit ×2; 8项/204bit ×1; 8项/140bit ×2; 8项/200bit ×1; 8项/136bit ×2; 8项/132bit ×1; 8项/128bit ×1; 8项/124bit ×1; 8项/120bit ×1; 8项/116bit ×1; 8项/112bit ×1; 8项/108bit ×1; 8项/104bit ×1; 8项/100bit ×1; 8项/96bit ×1; 8项/92bit ×1; 8项/88bit ×1; 8项/84bit ×1; 8项/80bit ×1; 8项/76bit ×1; 8项/72bit ×1 | 10624/1 | [rtlzz_pipe_6985_s2←#6985 adc（260位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:16825); [rtlzz_pipe_6979_s2←#6979 adc（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:16819); [rtlzz_pipe_6973_s2←#6973 adc（252位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:16813) |
| 2 | 无独立正价算术 | 8项/256bit ×1; 8项/247bit ×1; 8项/231bit ×1; 8项/215bit ×1; 8项/199bit ×1; 8项/183bit ×1; 8项/167bit ×1; 8项/151bit ×1 | 1656/1 | [rtlzz_pipe_7153_s3←#7153 adc（263位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:16849); [rtlzz_pipe_7150_s3←#7150 adc（247位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:16846); [rtlzz_pipe_7147_s3←#7147 adc（231位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:16843) |
| 3 | 无独立正价算术 | 8项/256bit ×1 | 256/1 | [y←#4 wire（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:33685); [ov←#2 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T750-L4/D/workload.sv:33685) |

全部589个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-78f923426662"></a>

## 实现 78f923426662：L2，块/limb=[0, 0]

对应记录：mul128 L2 T1200 B（not_started）；mul128 L2 T1450 B（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/B/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/B/workload.sv:54)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(128,128)->256 ×1 | — | 256/1 | [rtlzz_pipe_3_s1←#3 wire（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/B/workload.sv:37); [rtlzz_valid_s1←#2 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/B/workload.sv:39) |
| 1 | 无独立正价算术 | — | 256/1 | [y←#4 wire（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/B/workload.sv:60); [ov←#2 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/B/workload.sv:60) |

全部4个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-797e2a4ef532"></a>

## 实现 797e2a4ef532：L2，块/limb=[16, 0]

对应记录：mul128 L2 T1200 D（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1200-L2/D/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1200-L2/D/workload.sv:1896)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(16,16)->32 ×64 | — | 2048/1 | [rtlzz_pipe_101_s1←#101 concat（32位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1200-L2/D/workload.sv:1057); [rtlzz_pipe_105_s1←#105 concat（32位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1200-L2/D/workload.sv:1060); [rtlzz_pipe_109_s1←#109 concat（32位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1200-L2/D/workload.sv:1063) |
| 1 | 无独立正价算术 | 64项/256bit ×1 | 256/1 | [y←#4 wire（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1200-L2/D/workload.sv:1902); [ov←#2 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1200-L2/D/workload.sv:1902) |

全部67个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-8327002228a5"></a>

## 实现 8327002228a5：L4，块/limb=[8, 0]

对应记录：dot16 L4 T850 C（failed）；dot16 L4 T1050 C（failed）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:30820)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(8,8)->16 ×1024 | — | 16384/1 | [rtlzz_pipe_1038_s1←#1038 mul（16位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:16173); [rtlzz_pipe_1042_s1←#1042 concat（16位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:16176); [rtlzz_pipe_1046_s1←#1046 concat（16位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:16179) |
| 1 | 无独立正价算术 | 16项/128bit ×16; 16项/116bit ×16; 16项/100bit ×16; 16项/84bit ×16 | 6912/1 | [rtlzz_pipe_1025_s2←#1025 adc（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:16170); [rtlzz_pipe_1470_s2←#1470 adc（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:16374); [rtlzz_pipe_1915_s2←#1915 adc（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:16578) |
| 2 | 无独立正价算术 | 4项/130bit ×4; 4项/128bit ×16 | 520/1 | [rtlzz_pipe_57_s3←#57 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:16581); [rtlzz_pipe_58_s3←#58 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:17400); [rtlzz_pipe_59_s3←#59 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:18219) |
| 3 | 无独立正价算术 | 4项/132bit ×1 | 132/1 | [y←#64 wire（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:30856); [ov←#32 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L4/software/selected/dot16/T1050-L4/C/workload.sv:30856) |

全部1097个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-83a434da7745"></a>

## 实现 83a434da7745：L4，块/limb=[8, 0]

对应记录：barrett64 L4 T1800 C（measured_grt）；barrett64 L4 T2150 C（running）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:7622)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(8,8)->16 ×64 | 32项/128bit ×1; 32项/101bit ×1 | 427/1 | [rtlzz_pipe_480_s1←#480 adc（133位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:3905); [rtlzz_pipe_477_s1←#477 adc（101位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:3902); [rtlzz_pipe_32_s1←#32 slice（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:3893) |
| 1 | add(101,133)->128 ×1; mul(8,8)->16 ×128; mul(8,1)->9 ×16 | 16项/193bit ×1; 16项/181bit ×1; 16项/165bit ×1; 16项/149bit ×1; 16项/140bit ×1; 16项/125bit ×1; 16项/109bit ×1; 16项/93bit ×1; 16项/77bit ×1 | 1492/1 | [rtlzz_pipe_1464_s2←#1464 adc（197位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:3938); [rtlzz_pipe_1461_s2←#1461 adc（181位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:3935); [rtlzz_pipe_1458_s2←#1458 adc（165位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:3932) |
| 2 | mul(8,8)->16 ×64; mul(1,8)->9 ×8; add(16,24)->25 ×1; add(32,40)->41 ×2; add(48,56)->57 ×3; add(64,72)->73 ×4; add(24,32)->33 ×1; add(40,48)->49 ×2; add(56,64)->65 ×3; add(72,80)->81 ×4; add(80,88)->89 ×3; add(88,96)->97 ×3; add(96,104)->105 ×2; add(104,112)->113 ×2; add(112,120)->121 ×1; add(120,128)->129 ×1; add(73,81)->82 ×1; add(89,97)->98 ×1; add(105,113)->114 ×1; add(121,129)->129 ×1 | 9项/193bit ×1 | 3080/1 | [rtlzz_pipe_1884_s3←#1884 adc（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:4046); [rtlzz_pipe_1872_s3←#1872 adc（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:4034); [rtlzz_pipe_15_s3←#15 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:3911) |
| 3 | sub(129,129)->129 ×1; ult(129,64)->1 ×1; sub(129,64)->64 ×1; mux(129,129)->64 ×1 | 36项/129bit ×1 | 64/1 | [y←#21 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:7630); [ov←#4 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/barrett64/L4/software/selected/barrett64/T2150-L4/C/workload.sv:7630) |

全部60个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-8bbe5fa52f58"></a>

## 实现 8bbe5fa52f58：L5，块/limb=[0, 0]

对应记录：dot16 L5 T700 B（failed）；dot16 L5 T850 B（failed）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:763)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(64,64)->128 ×16 | — | 2048/1 | [rtlzz_pipe_33_s1←#33 wire（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:341); [rtlzz_pipe_34_s1←#34 wire（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:344); [rtlzz_pipe_35_s1←#35 wire（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:350) |
| 1 | add(128,128)->129 ×8 | — | 1032/1 | [rtlzz_pipe_49_s2←#49 add（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:347); [rtlzz_pipe_50_s2←#50 add（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:356); [rtlzz_pipe_51_s2←#51 add（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:368) |
| 2 | add(129,129)->130 ×4 | — | 520/1 | [rtlzz_pipe_57_s3←#57 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:359); [rtlzz_pipe_58_s3←#58 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:380); [rtlzz_pipe_59_s3←#59 add（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:404) |
| 3 | add(130,130)->131 ×2 | — | 262/1 | [rtlzz_pipe_61_s4←#61 add（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:383); [rtlzz_pipe_62_s4←#62 add（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:428); [rtlzz_valid_s4←#32 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:433) |
| 4 | add(131,131)->132 ×1 | — | 132/1 | [y←#64 wire（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:799); [ov←#32 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/B/workload.sv:799) |

全部36个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-8f7d78972cbb"></a>

## 实现 8f7d78972cbb：L4，块/limb=[0, 0]

对应记录：karatsuba256 L4 T2300 D（not_started）；karatsuba256 L4 T2750 D（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:1646)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(65,65)->65 ×4; add(34,34)->34 ×8; add(129,129)->129 ×2; add(66,66)->66 ×2; add(256,256)->256 ×2; add(130,130)->130 ×3; mul(64,64)->128 ×5; mul(33,33)->66 ×5; mul(32,32)->64 ×3; mul(34,34)->68 ×3 | — | 3304/1 | [rtlzz_pipe_156_s1←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:819); [rtlzz_pipe_145_s1←#145 shl（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:921); [rtlzz_pipe_220_s1←#220 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:873) |
| 1 | sub(68,68)->68 ×8; sub(130,130)->130 ×2; add(258,130)->258 ×1; add(130,130)->130 ×3; mul(34,34)->68 ×1 | 3项/132bit ×1 | 2188/1 | [rtlzz_pipe_156_s2←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:822); [rtlzz_pipe_218_s2←#218 add（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:924); [rtlzz_pipe_220_s2←#220 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:876) |
| 2 | sub(130,130)->130 ×2; sub(132,130)->132 ×1; sub(132,132)->132 ×1; sub(258,256)->258 ×1; add(256,512)->512 ×1; add(258,258)->258 ×1; add(256,256)->256 ×2 | — | 1538/1 | [rtlzz_pipe_156_s3←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:825); [rtlzz_pipe_216_s3←#216 add（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:897); [rtlzz_pipe_147_s3←#147 sub（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:942) |
| 3 | sub(258,256)->258 ×1; add(512,512)->513 ×1; add(512,512)->512 ×1 | — | 513/1 | [y←#158 wire（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:1653); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/D/workload.sv:1653) |

其他功能逻辑另列在详细JSON中，不因算术表为空而忽略。

全部47个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-a2c5d3c0f979"></a>

## 实现 a2c5d3c0f979：L2，块/limb=[8, 0]

对应记录：mul128 L2 T1200 C（not_started）；mul128 L2 T1450 C（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/C/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/C/workload.sv:6952)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(8,8)->16 ×256 | 4项/256bit ×1; 4项/226bit ×2; 4项/194bit ×3; 4项/162bit ×4; 4项/250bit ×1; 4项/218bit ×2; 4项/186bit ×3; 4项/154bit ×4; 4项/242bit ×1; 4项/210bit ×2; 4项/178bit ×3; 4项/146bit ×4; 4项/234bit ×1; 4项/202bit ×2; 4项/170bit ×3; 4项/138bit ×4; 4项/130bit ×3; 4项/122bit ×3; 4项/114bit ×3; 4项/106bit ×3; 4项/98bit ×2; 4项/90bit ×2; 4项/82bit ×2; 4项/74bit ×2; 4项/66bit ×1; 4项/58bit ×1; 4项/50bit ×1; 4项/42bit ×1 | 9600/1 | [rtlzz_pipe_1609_s1←#1609 adc（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/C/workload.sv:3740); [rtlzz_pipe_1597_s1←#1597 adc（250位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/C/workload.sv:3728); [rtlzz_pipe_1585_s1←#1585 adc（242位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/C/workload.sv:3716) |
| 1 | 无独立正价算术 | 64项/256bit ×1 | 256/1 | [y←#4 wire（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/C/workload.sv:6958); [ov←#2 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mul128/L2/software/selected/mul128/T1450-L2/C/workload.sv:6958) |

全部67个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-a6689a6712c6"></a>

## 实现 a6689a6712c6：L16，块/limb=[0, 0]

对应记录：ntt8x64 L16 T800 D（not_started）；ntt8x64 L16 T950 D（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:3025)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(64,64)->65 ×4; add(64,65)->65 ×4 | — | 776/1 | [rtlzz_pipe_11_s1←#11 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1018); [rtlzz_pipe_15_s1←#15 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1021); [rtlzz_pipe_22_s1←#22 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1030) |
| 1 | ult(65,65)->1 ×4; sub(65,65)->65 ×4; mux(65,65)->65 ×4; sub(65,64)->65 ×4 | — | 516/1 | [rtlzz_pipe_16_s2←#16 sub（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1024); [rtlzz_pipe_27_s2←#27 sub（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1036); [rtlzz_pipe_38_s2←#38 sub（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1048) |
| 2 | ult(65,65)->1 ×4; sub(65,65)->65 ×4; mux(65,65)->65 ×4; add(65,65)->65 ×4; mul(64,49)->113 ×2 | — | 968/1 | [rtlzz_pipe_105_s3←#105 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1351); [rtlzz_pipe_256_s3←#256 slice（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1264); [rtlzz_pipe_265_s3←#265 slice（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1360) |
| 3 | ult(65,65)->1 ×2; sub(65,65)->65 ×4; mux(65,65)->65 ×2; add(65,65)->65 ×2; mul(128,65)->193 ×2 | — | 872/1 | [rtlzz_pipe_105_s4←#105 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1354); [rtlzz_pipe_71_s4←#71 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1258); [rtlzz_pipe_116_s4←#116 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1141) |
| 4 | ult(65,65)->1 ×2; sub(65,65)->65 ×2; mux(65,65)->65 ×2; add(65,65)->65 ×2; mul(65,64)->129 ×2; mul(64,49)->113 ×1 | — | 1226/1 | [rtlzz_pipe_104_s5←#104 wire（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1366); [rtlzz_pipe_70_s5←#70 wire（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1270); [rtlzz_pipe_105_s5←#105 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1357) |
| 5 | sub(129,129)->129 ×2; ult(65,65)->1 ×1; sub(65,65)->64 ×1; mux(65,65)->64 ×1; sub(65,65)->65 ×1; add(65,65)->65 ×1; mul(128,65)->193 ×1 | — | 952/1 | [rtlzz_pipe_106_s6←#106 sub（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1369); [rtlzz_pipe_72_s6←#72 sub（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1273); [rtlzz_pipe_166_s6←#166 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1420) |
| 6 | ult(129,129)->1 ×2; sub(129,129)->65 ×2; mux(129,129)->65 ×2; ult(65,65)->1 ×1; sub(65,65)->64 ×1; mux(65,65)->64 ×1; mul(65,64)->129 ×1 | — | 885/1 | [rtlzz_pipe_165_s7←#165 wire（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1432); [rtlzz_pipe_166_s7←#166 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1423); [rtlzz_pipe_116_s7←#116 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1150) |
| 7 | add(65,65)->65 ×2; sub(65,65)->65 ×2; sub(129,129)->129 ×1 | — | 646/1 | [rtlzz_pipe_167_s8←#167 sub（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1435); [rtlzz_pipe_112_s8←#112 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1375); [rtlzz_pipe_117_s8←#117 sub（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1378) |
| 8 | ult(65,65)->1 ×4; sub(65,65)->65 ×4; mux(65,65)->65 ×4; ult(129,129)->1 ×1; sub(129,129)->65 ×1; mux(129,129)->65 ×1 | — | 577/1 | [rtlzz_pipe_177_s9←#177 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1252); [rtlzz_pipe_132_s9←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1180); [rtlzz_pipe_133_s9←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1207) |
| 9 | add(65,65)->65 ×3; sub(65,65)->65 ×1; mul(64,64)->128 ×2 | — | 1028/1 | [rtlzz_pipe_141_s10←#141 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1387); [rtlzz_pipe_191_s10←#191 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1477); [rtlzz_pipe_274_s10←#274 slice（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1396) |
| 10 | ult(65,65)->1 ×2; sub(65,65)->64 ×2; mux(65,65)->64 ×2; mul(128,65)->193 ×2 | — | 900/1 | [rtlzz_pipe_141_s11←#141 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1390); [rtlzz_pipe_191_s11←#191 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1480); [rtlzz_pipe_152_s11←#152 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1306) |
| 11 | mul(65,64)->129 ×2 | — | 1028/1 | [rtlzz_pipe_140_s12←#140 wire（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1402); [rtlzz_pipe_190_s12←#190 wire（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1492); [rtlzz_pipe_141_s12←#141 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1393) |
| 12 | sub(129,129)->129 ×2 | — | 772/1 | [rtlzz_pipe_142_s13←#142 sub（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1405); [rtlzz_pipe_192_s13←#192 sub（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1495); [rtlzz_pipe_152_s13←#152 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1312) |
| 13 | ult(129,129)->1 ×2; sub(129,129)->65 ×2; mux(129,129)->65 ×2 | — | 642/1 | [rtlzz_pipe_152_s14←#152 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1315); [rtlzz_pipe_202_s14←#202 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1348); [rtlzz_pipe_132_s14←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1195) |
| 14 | add(65,65)->65 ×2; sub(65,65)->65 ×2 | — | 516/1 | [rtlzz_pipe_148_s15←#148 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1411); [rtlzz_pipe_153_s15←#153 sub（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1414); [rtlzz_pipe_198_s15←#198 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:1501) |
| 15 | ult(65,65)->1 ×4; sub(65,65)->64 ×4; mux(65,65)->64 ×4 | — | 512/1 | [y0←#209 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:3044); [y1←#210 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:3044); [y2←#211 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/D/workload.sv:3044) |

全部188个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-ada50437924b"></a>

## 实现 ada50437924b：L16，块/limb=[8, 0]

对应记录：ntt8x64 L16 T800 C（not_started）；ntt8x64 L16 T950 C（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:39715)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(64,64)->65 ×4; ult(65,65)->1 ×12; sub(65,65)->65 ×14; mux(65,65)->65 ×10; add(64,65)->65 ×4; sub(65,64)->65 ×4; add(65,65)->65 ×6 | — | 776/1 | [rtlzz_pipe_116_s1←#116 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20027); [rtlzz_pipe_60_s1←#60 sub（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:19946); [rtlzz_pipe_62_s1←#62 sub（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:19952) |
| 1 | mux(65,65)->65 ×2; add(65,65)->65 ×3; ult(65,65)->1 ×2; sub(65,65)->64 ×2; mux(65,65)->64 ×2; sub(65,65)->65 ×1; mul(8,8)->16 ×144; mul(8,1)->9 ×24; add(16,24)->25 ×1; add(32,40)->41 ×3; add(48,56)->57 ×5; add(57,24)->58 ×1; add(64,65)->66 ×1; add(64,72)->73 ×5; add(73,40)->74 ×1; add(80,81)->82 ×1; add(80,88)->89 ×4; add(89,56)->90 ×1; add(96,97)->98 ×1; add(96,104)->105 ×2; add(105,72)->106 ×1; add(112,113)->113 ×1 | 4项/113bit ×2; 4项/107bit ×2; 4项/106bit ×2; 4项/99bit ×2; 4项/90bit ×2; 4项/91bit ×2; 4项/74bit ×4; 4项/83bit ×2; 4项/75bit ×2; 4项/67bit ×2; 4项/58bit ×2; 4项/59bit ×2; 4项/42bit ×2 | 4847/1 | [rtlzz_pipe_2556_s2←#2556 adc（115位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20528); [rtlzz_pipe_661_s2←#661 adc（115位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20219); [rtlzz_pipe_6360_s2←#6360 adc（114位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21038) |
| 2 | 无独立正价算术 | 28项/113bit ×1; 14项/113bit ×2 | 1193/1 | [rtlzz_pipe_105_s3←#105 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20531); [rtlzz_pipe_166_s3←#166 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21041); [rtlzz_pipe_256_s3←#256 slice（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20234) |
| 3 | mul(8,8)->16 ×360; mul(8,1)->9 ×45 | 3项/187bit ×3; 4项/170bit ×9; 4项/179bit ×3; 4项/171bit ×3; 4项/138bit ×15; 4项/163bit ×3; 4项/155bit ×3; 4项/147bit ×3; 4项/139bit ×3; 4项/106bit ×15; 4项/131bit ×3; 4项/123bit ×3; 4项/115bit ×3; 4项/107bit ×3; 4项/74bit ×15; 4项/99bit ×3; 4项/91bit ×3; 4项/83bit ×3; 4项/75bit ×3; 4项/42bit ×3 | 13175/1 | [rtlzz_pipe_1594_s4←#1594 adc（187位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20336); [rtlzz_pipe_3489_s4←#3489 adc（187位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20645); [rtlzz_pipe_7335_s4←#7335 adc（187位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21155) |
| 4 | 无独立正价算术 | 34项/193bit ×3 | 1040/1 | [rtlzz_pipe_105_s5←#105 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20537); [rtlzz_pipe_166_s5←#166 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21047); [rtlzz_pipe_71_s5←#71 and（113位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20228) |
| 5 | mul(8,8)->16 ×192 | 4项/129bit ×3; 4项/98bit ×6; 4项/122bit ×3; 4项/90bit ×6; 4项/114bit ×3; 4项/82bit ×6; 4项/106bit ×3; 4项/74bit ×6; 4项/66bit ×3; 4项/58bit ×3; 4项/50bit ×3; 4项/42bit ×3 | 4982/1 | [rtlzz_pipe_2149_s6←#2149 adc（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20393); [rtlzz_pipe_4044_s6←#4044 adc（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20702); [rtlzz_pipe_7890_s6←#7890 adc（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21212) |
| 6 | sub(129,129)->129 ×3 | 16项/129bit ×3 | 902/1 | [rtlzz_pipe_106_s7←#106 sub（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20711); [rtlzz_pipe_167_s7←#167 sub（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21221); [rtlzz_pipe_72_s7←#72 sub（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20402) |
| 7 | ult(129,129)->1 ×3; sub(129,129)->65 ×3; mux(129,129)->65 ×3; add(65,65)->65 ×5; ult(65,65)->1 ×6; sub(65,65)->65 ×7; mux(65,65)->65 ×4; sub(65,65)->64 ×2; mux(65,65)->64 ×2 | — | 642/1 | [rtlzz_pipe_152_s8←#152 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20426); [rtlzz_pipe_202_s8←#202 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20468); [rtlzz_pipe_132_s8←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20072) |
| 8 | mul(8,8)->16 ×128 | 4项/128bit ×2; 4项/98bit ×4; 4项/122bit ×2; 4项/90bit ×4; 4项/114bit ×2; 4项/82bit ×4; 4项/106bit ×2; 4项/74bit ×4; 4项/66bit ×2; 4项/58bit ×2; 4项/50bit ×2; 4项/42bit ×2 | 3266/1 | [rtlzz_pipe_4501_s9←#4501 adc（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20765); [rtlzz_pipe_8347_s9←#8347 adc（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21317); [rtlzz_pipe_4495_s9←#4495 adc（122位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20759) |
| 9 | 无独立正价算术 | 16项/128bit ×2 | 1026/1 | [rtlzz_pipe_141_s10←#141 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20768); [rtlzz_pipe_191_s10←#191 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21320); [rtlzz_pipe_274_s10←#274 slice（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20780) |
| 10 | mul(8,8)->16 ×256; mul(8,1)->9 ×32 | 4项/193bit ×2; 4项/170bit ×8; 4项/187bit ×2; 4项/179bit ×2; 4项/171bit ×2; 4项/138bit ×10; 4项/163bit ×2; 4项/155bit ×2; 4项/147bit ×2; 4项/139bit ×2; 4项/106bit ×10; 4项/131bit ×2; 4项/123bit ×2; 4项/115bit ×2; 4项/107bit ×2; 4项/74bit ×10; 4项/99bit ×2; 4项/91bit ×2; 4项/83bit ×2; 4项/75bit ×2; 4项/42bit ×2 | 9714/1 | [rtlzz_pipe_5446_s11←#5446 adc（195位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20888); [rtlzz_pipe_9292_s11←#9292 adc（195位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21440); [rtlzz_pipe_5440_s11←#5440 adc（187位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20882) |
| 11 | 无独立正价算术 | 36项/193bit ×2 | 900/1 | [rtlzz_pipe_141_s12←#141 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20774); [rtlzz_pipe_191_s12←#191 and（128位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21326); [rtlzz_pipe_152_s12←#152 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20438) |
| 12 | mul(8,8)->16 ×128; mul(1,8)->9 ×16 | 4项/129bit ×4; 4项/99bit ×2; 4项/98bit ×4; 4项/122bit ×2; 4项/90bit ×4; 4项/114bit ×2; 4项/82bit ×4; 4项/106bit ×2; 4项/74bit ×4; 4项/66bit ×2; 4项/58bit ×2; 4项/50bit ×2; 4项/42bit ×2 | 3982/1 | [rtlzz_pipe_6001_s13←#6001 adc（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20945); [rtlzz_pipe_9847_s13←#9847 adc（131位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21497); [rtlzz_pipe_5995_s13←#5995 adc（130位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20939) |
| 13 | sub(129,129)->129 ×2 | 18项/129bit ×2 | 772/1 | [rtlzz_pipe_142_s14←#142 sub（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20948); [rtlzz_pipe_192_s14←#192 sub（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:21500); [rtlzz_pipe_152_s14←#152 add（65位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20444) |
| 14 | ult(129,129)->1 ×2; sub(129,129)->65 ×2; mux(129,129)->65 ×2; add(65,65)->65 ×2; ult(65,65)->1 ×4; sub(65,65)->64 ×4; mux(65,65)->64 ×4; sub(65,65)->65 ×2 | — | 512/1 | [rtlzz_pipe_132_s15←#132 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20093); [rtlzz_pipe_133_s15←#133 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20135); [rtlzz_pipe_157_s15←#157 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:20951) |
| 15 | 无独立正价算术 | — | 512/1 | [y0←#209 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:39734); [y1←#210 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:39734); [y2←#211 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/parallel-software/ntt8x64/selected/ntt8x64/T950-L16/C/workload.sv:39734) |

全部545个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-afb74d898573"></a>

## 实现 afb74d898573：L4，块/limb=[0, 0]

对应记录：karatsuba256 L4 T2300 B（not_started）；karatsuba256 L4 T2750 B（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:1686)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(65,65)->65 ×4; add(34,34)->34 ×8; add(129,129)->129 ×2; add(66,66)->66 ×2; mul(64,64)->128 ×4; mul(32,32)->64 ×3 | — | 3104/1 | [rtlzz_pipe_156_s1←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:860); [rtlzz_pipe_45_s1←#45 shl（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:935); [rtlzz_pipe_83_s1←#83 shl（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:977) |
| 1 | add(256,256)->256 ×2; mul(33,33)->66 ×5; mul(34,34)->68 ×4; mul(64,64)->128 ×1 | — | 3502/1 | [rtlzz_pipe_156_s2←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:863); [rtlzz_pipe_145_s2←#145 shl（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:1034); [rtlzz_pipe_220_s2←#220 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:986) |
| 2 | sub(68,68)->68 ×8; sub(130,130)->130 ×4; sub(132,130)->132 ×1; sub(132,132)->132 ×1; sub(258,256)->258 ×2; add(512,512)->513 ×1; add(256,256)->256 ×2 | 3项/512bit ×1; 3项/258bit ×1; 3项/130bit ×3; 3项/132bit ×1 | 513/1 | [rtlzz_pipe_157_s3←#157 add（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:1052); [rtlzz_valid_s3←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:1056) |
| 3 | 无独立正价算术 | — | 513/1 | [y←#158 wire（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:1693); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/karatsuba256/L4/software/selected/karatsuba256/T2750-L4/same_policy_static/workload.sv:1693) |

其他功能逻辑另列在详细JSON中，不因算术表为空而忽略。

全部70个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-b5e7a118e6c3"></a>

## 实现 b5e7a118e6c3：L8，块/limb=[0, 0]

对应记录：karatsuba256 L8 T1150 D（not_started）；karatsuba256 L8 T1400 D（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1943)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(65,65)->65 ×4; add(34,34)->34 ×6; add(129,129)->129 ×2; add(66,66)->66 ×2; mul(64,64)->128 ×4 | — | 2778/1 | [rtlzz_pipe_156_s1←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:951); [rtlzz_pipe_45_s1←#45 shl（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1074); [rtlzz_pipe_83_s1←#83 shl（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1131) |
| 1 | add(34,34)->34 ×2; add(256,256)->256 ×2; mul(33,33)->66 ×5; mul(32,32)->64 ×3; mul(34,34)->68 ×3; mul(64,64)->128 ×1 | — | 3502/1 | [rtlzz_pipe_156_s2←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:954); [rtlzz_pipe_145_s2←#145 shl（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1218); [rtlzz_pipe_220_s2←#220 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1143) |
| 2 | sub(68,68)->68 ×6; add(132,132)->132 ×1; mul(34,34)->68 ×1 | 3项/130bit ×3 | 2774/1 | [rtlzz_pipe_156_s3←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:957); [rtlzz_pipe_145_s3←#145 shl（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1221); [rtlzz_pipe_220_s3←#220 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1146) |
| 3 | sub(130,130)->130 ×4; sub(68,68)->68 ×2; add(258,130)->258 ×1; add(132,132)->132 ×1 | — | 2184/1 | [rtlzz_pipe_156_s4←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:960); [rtlzz_pipe_218_s4←#218 add（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1224); [rtlzz_pipe_220_s4←#220 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1149) |
| 4 | sub(132,130)->132 ×1; sub(132,132)->132 ×1; add(256,512)->512 ×1; add(256,256)->256 ×2 | — | 2052/1 | [rtlzz_pipe_156_s5←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:963); [rtlzz_pipe_216_s5←#216 add（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1179); [rtlzz_pipe_143_s5←#143 shl（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1257) |
| 5 | sub(258,256)->258 ×1; add(258,258)->258 ×1 | — | 1538/1 | [rtlzz_pipe_156_s6←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:966); [rtlzz_pipe_216_s6←#216 add（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1182); [rtlzz_pipe_147_s6←#147 sub（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1260) |
| 6 | sub(258,256)->258 ×1; add(512,512)->512 ×1 | — | 1024/1 | [rtlzz_pipe_155_s7←#155 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1263); [rtlzz_pipe_156_s7←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:969); [rtlzz_valid_s7←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1271) |
| 7 | add(512,512)->513 ×1 | — | 513/1 | [y←#158 wire（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1950); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/D/workload.sv:1950) |

其他功能逻辑另列在详细JSON中，不因算术表为空而忽略。

全部114个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-b6a28e166624"></a>

## 实现 b6a28e166624：L5，块/limb=[8, 64]

对应记录：dot16 L5 T700 C（failed）；dot16 L5 T850 C（running）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:34478)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(8,8)->16 ×1024; add(16,24)->25 ×16; add(32,40)->41 ×32; add(48,56)->57 ×48; add(64,72)->73 ×64; add(24,32)->33 ×16; add(40,48)->49 ×32; add(56,64)->65 ×48; add(72,80)->81 ×64; add(80,88)->89 ×48; add(88,96)->97 ×48; add(96,104)->105 ×32; add(104,112)->113 ×32; add(112,120)->121 ×16; add(120,128)->128 ×16 | — | 39424/1 | [rtlzz_pipe_1386_s1←#1386 adc（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:16039); [rtlzz_pipe_1831_s1←#1831 adc（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:16135); [rtlzz_pipe_2276_s1←#2276 adc（129位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:16231) |
| 1 | 无独立正价算术 | 32项/128bit ×16 | 2048/1 | [rtlzz_pipe_7268_s2←#7268 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:17290); [rtlzz_pipe_7269_s2←#7269 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:17293); [rtlzz_pipe_7273_s2←#7273 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:17296) |
| 2 | add(64,64)->65 ×12; adc(64,64)->65 ×12; adc(1,1)->1 ×8 | — | 524/1 | [rtlzz_pipe_7407_s3←#7407 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:17434); [rtlzz_pipe_7412_s3←#7412 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:17437); [rtlzz_pipe_7424_s3←#7424 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:17449) |
| 3 | adc(2,2)->2 ×4; add(64,64)->65 ×3; adc(64,64)->65 ×2; adc(3,3)->3 ×2 | — | 199/1 | [rtlzz_pipe_7509_s4←#7509 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:17494); [rtlzz_pipe_7511_s4←#7511 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:17500); [rtlzz_pipe_7512_s4←#7512 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:17503) |
| 4 | adc(64,64)->65 ×1; adc(4,4)->4 ×1 | — | 132/1 | [y←#64 wire（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:34514); [ov←#32 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-dot16-L45-v1/L5/software/selected/dot16/T850-L5/C/workload.sv:34514) |

全部592个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-c1a64d59e07d"></a>

## 实现 c1a64d59e07d：L1，块/limb=[0, 0]

对应记录：karatsuba256 L4 T2300 A（not_started）；karatsuba256 L4 T2750 A（not_started）；karatsuba256 L8 T1150 A（not_started）；karatsuba256 L8 T1400 A（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L1/A/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L1/A/workload.sv:1315)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(65,65)->65 ×4; add(34,34)->34 ×8; sub(68,68)->68 ×8; sub(130,130)->130 ×4; add(129,129)->129 ×2; add(66,66)->66 ×2; sub(132,130)->132 ×1; sub(132,132)->132 ×1; sub(258,256)->258 ×2; add(512,512)->513 ×1; mul(64,64)->128 ×5; mul(33,33)->66 ×5; mul(32,32)->64 ×3; mul(34,34)->68 ×4 | 3项/512bit ×1; 3项/256bit ×2; 3项/258bit ×1; 3项/130bit ×3; 3项/132bit ×1 | 513/1 | [y←#158 wire（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L1/A/workload.sv:1322); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L1/A/workload.sv:1322) |

其他功能逻辑另列在详细JSON中，不因算术表为空而忽略。

全部2个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-c218c9843815"></a>

## 实现 c218c9843815：L2，块/limb=[0, 0]

对应记录：mac32 L2 T950 B（not_started）；mac32 L2 T1100 B（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/B/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/B/workload.sv:73)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(32,32)->64 ×1 | — | 128/1 | [rtlzz_pipe_2_s1←#2 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/B/workload.sv:42); [rtlzz_pipe_4_s1←#4 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/B/workload.sv:45); [rtlzz_valid_s1←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/B/workload.sv:47) |
| 1 | add(64,64)->64 ×1 | — | 64/1 | [y←#6 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/B/workload.sv:80); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/B/workload.sv:80) |

全部5个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-c4d9a155e3c4"></a>

## 实现 c4d9a155e3c4：L4，块/limb=[8, 0]

对应记录：horner64 L4 T1900 C（measured_grt）；horner64 L4 T2250 C（running）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:5069)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(8,8)->16 ×28; mul(8,8)->8 ×8 | 37项/64bit ×1 | 320/1 | [rtlzz_pipe_0_s1←#0 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:3419); [rtlzz_pipe_1_s1←#1 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:3428); [rtlzz_pipe_2_s1←#2 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:3437) |
| 1 | mul(8,8)->16 ×28; mul(8,8)->8 ×8 | 37项/64bit ×1 | 256/1 | [rtlzz_pipe_0_s2←#0 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:3422); [rtlzz_pipe_10_s2←#10 add（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:3449); [rtlzz_pipe_1_s2←#1 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:3431) |
| 2 | mul(8,8)->16 ×28; mul(8,8)->8 ×8 | 37项/64bit ×1 | 192/1 | [rtlzz_pipe_0_s3←#0 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:3425); [rtlzz_pipe_12_s3←#12 add（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:3452); [rtlzz_pipe_1_s3←#1 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:3434) |
| 3 | mul(8,8)->16 ×28; mul(8,8)->8 ×8 | 37项/64bit ×1 | 64/1 | [y←#15 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:5079); [ov←#6 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/horner64/L4/software/selected/horner64/T2250-L4/C/workload.sv:5079) |

全部17个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-d82729a2bd2b"></a>

## 实现 d82729a2bd2b：L8，块/limb=[0, 0]

对应记录：karatsuba256 L8 T1150 B（not_started）；karatsuba256 L8 T1400 B（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1718)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(65,65)->65 ×4; add(34,34)->34 ×8; add(129,129)->129 ×2; add(66,66)->66 ×2; mul(64,64)->128 ×4; mul(32,32)->64 ×3 | — | 3104/1 | [rtlzz_pipe_156_s1←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:876); [rtlzz_pipe_45_s1←#45 shl（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:951); [rtlzz_pipe_83_s1←#83 shl（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:993) |
| 1 | add(256,256)->256 ×2; mul(33,33)->66 ×5; mul(34,34)->68 ×4; mul(64,64)->128 ×1 | — | 3502/1 | [rtlzz_pipe_156_s2←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:879); [rtlzz_pipe_145_s2←#145 shl（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1050); [rtlzz_pipe_220_s2←#220 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1002) |
| 2 | sub(68,68)->68 ×8; sub(130,130)->130 ×4; sub(132,130)->132 ×1; sub(132,132)->132 ×1; sub(258,256)->258 ×2; add(512,512)->513 ×1; add(256,256)->256 ×2 | 3项/512bit ×1; 3项/258bit ×1; 3项/130bit ×3; 3项/132bit ×1 | 513/1 | [rtlzz_pipe_157_s3←#157 add（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1068); [rtlzz_valid_s3←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1084) |
| 3 | 无独立正价算术 | — | 513/1 | [rtlzz_pipe_157_s4←#157 add（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1071); [rtlzz_valid_s4←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1085) |
| 4 | 无独立正价算术 | — | 513/1 | [rtlzz_pipe_157_s5←#157 add（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1074); [rtlzz_valid_s5←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1086) |
| 5 | 无独立正价算术 | — | 513/1 | [rtlzz_pipe_157_s6←#157 add（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1077); [rtlzz_valid_s6←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1087) |
| 6 | 无独立正价算术 | — | 513/1 | [rtlzz_pipe_157_s7←#157 add（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1080); [rtlzz_valid_s7←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1088) |
| 7 | 无独立正价算术 | — | 513/1 | [y←#158 wire（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1725); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/B/workload.sv:1725) |

其他功能逻辑另列在详细JSON中，不因算术表为空而忽略。

全部78个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-dce41e76e019"></a>

## 实现 dce41e76e019：L2，块/limb=[16, 0]

对应记录：mac32 L2 T1100 D（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/D/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/D/workload.sv:164)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | mul(16,16)->32 ×4 | — | 192/1 | [rtlzz_pipe_2_s1←#2 input（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/D/workload.sv:95); [rtlzz_pipe_15_s1←#15 mul（32位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/D/workload.sv:98); [rtlzz_pipe_19_s1←#19 concat（32位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/D/workload.sv:101) |
| 1 | 无独立正价算术 | 5项/64bit ×1 | 64/1 | [y←#6 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/D/workload.sv:171); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/variants/mac32/L2/software/selected/mac32/T1100-L2/D/workload.sv:171) |

全部8个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-f3011704032a"></a>

## 实现 f3011704032a：L8，块/limb=[8, 0]

对应记录：karatsuba256 L8 T1150 C（not_started）；karatsuba256 L8 T1400 C（not_started）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:19238)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | add(65,65)->65 ×4; add(34,34)->34 ×8; add(129,129)->129 ×2; add(66,66)->66 ×2; mul(8,8)->16 ×256 | — | 5530/1 | [rtlzz_pipe_156_s1←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:9811); [rtlzz_pipe_331_s1←#331 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:9880); [rtlzz_pipe_332_s1←#332 slice（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:9883) |
| 1 | mul(8,8)->16 ×256; mul(8,1)->9 ×20; mul(1,8)->9 ×20; mul(1,1)->2 ×5; mul(8,2)->10 ×16; mul(2,8)->10 ×16; mul(2,2)->4 ×4 | 16项/128bit ×4; 16项/116bit ×4; 16项/100bit ×4; 16项/84bit ×4 | 7042/1 | [rtlzz_pipe_156_s2←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:9814); [rtlzz_pipe_1239_s2←#1239 adc（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:10315); [rtlzz_pipe_2137_s2←#2137 adc（132位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:10750) |
| 2 | add(256,256)->256 ×2 | 16项/128bit ×1; 16项/116bit ×1; 16项/100bit ×1; 16项/84bit ×1; 9项/66bit ×5; 16项/61bit ×5; 9项/68bit ×4; 16项/62bit ×4; 16项/64bit ×3; 4项/128bit ×4 | 3728/1 | [rtlzz_pipe_156_s3←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:9817); [rtlzz_pipe_220_s3←#220 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:10969); [rtlzz_pipe_222_s3←#222 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:10324) |
| 3 | sub(68,68)->68 ×8; add(61,69)->66 ×5; add(62,70)->68 ×4 | 4项/128bit ×1; 3项/130bit ×3; 3项/132bit ×1 | 2574/1 | [rtlzz_pipe_156_s4←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:9820); [rtlzz_pipe_145_s4←#145 shl（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:11629); [rtlzz_pipe_220_s4←#220 add（256位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:10972) |
| 4 | sub(130,130)->130 ×4; sub(132,130)->132 ×1; sub(132,132)->132 ×1; sub(258,256)->258 ×1; add(256,512)->512 ×1; add(256,256)->256 ×2 | 3项/258bit ×1 | 1538/1 | [rtlzz_pipe_156_s5←#156 wire（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:9823); [rtlzz_pipe_216_s5←#216 add（512位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:11197); [rtlzz_pipe_147_s5←#147 sub（258位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:11878) |
| 5 | sub(258,256)->258 ×1; add(512,512)->513 ×1; add(512,512)->512 ×1 | — | 513/1 | [rtlzz_pipe_157_s6←#157 add（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:11881); [rtlzz_valid_s6←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:11891) |
| 6 | 无独立正价算术 | — | 513/1 | [rtlzz_pipe_157_s7←#157 add（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:11884); [rtlzz_valid_s7←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:11892) |
| 7 | 无独立正价算术 | — | 513/1 | [y←#158 wire（513位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:19245); [ov←#3 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/karatsuba256/T1400-L8/C/workload.sv:19245) |

其他功能逻辑另列在详细JSON中，不因算术表为空而忽略。

全部701个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

<a id="rtl-fe0456a5a32c"></a>

## 实现 fe0456a5a32c：L1，块/limb=[0, 0]

对应记录：barrett64 L4 T1800 A（failed）；barrett64 L4 T2150 A（running）；barrett64 L8 T900 A（failed）；barrett64 L8 T1100 A（failed）。

实际源码：[workload.sv](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/barrett64/T1100-L1/A/workload.sv)；输入服务外壳：[Workload](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/barrett64/T1100-L1/A/workload.sv:159)。

| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |
| ---: | --- | --- | --- | --- |
| 0 | sub(129,129)->129 ×1; ult(129,64)->1 ×1; sub(129,64)->64 ×1; mux(129,129)->64 ×1; mul(64,64)->128 ×1; mul(128,65)->193 ×1; mul(65,64)->129 ×1 | — | 64/1 | [y←#21 wire（64位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/barrett64/T1100-L1/A/workload.sv:167); [ov←#4 input（1位）](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/barrett64/T1100-L1/A/workload.sv:167) |

全部2个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。

[完整方法清单](rtl-inventory.csv)；[逐节点图／位置／所有者／寄存器JSON](unmeasured-rtl-detail.json.gz)；[全部寄存器CSV](unmeasured-registers.csv.gz)。
未冻结项目只具备A/B/C/D的一般合同，不能预告最终块宽、具体切点或寄存器表。Montgomery两档仍被有效A参考阻塞；NTT8×64 L8的软件状态见快照，后续就绪不改写本报告时间点。
