# GF180 TC wire resistances fitted to independently extracted routed segments.
# Values are OHM/um in the verified1ohm STA context; capacitances retain native
# pF/um values. Original native coefficients remain in historical snapshots.
if {$::env(CORNER) ne "TC" || $::env(METAL_OPTION) ne "5LM_1TM" || $::env(TRACK_OPTION) ne "9t" || $::env(KVALUE) ne "9"} {
    error "gf180 RC calibration used with an unvalidated stack/corner"
}
source $::env(PLATFORM_DIR)/setRC.tcl
set_layer_rc -layer Metal2 -resistance 0.32502850540936595 -capacitance 0.00013535700000000001
set_layer_rc -layer Metal3 -resistance 0.3250333828878646 -capacitance 0.000146141
set_layer_rc -layer Metal4 -resistance 0.32502708223006027 -capacitance 0.000150688
set_layer_rc -layer Metal5 -resistance 0.093199897118860439 -capacitance 0.00015559499999999999
set_wire_rc -signal -layer Metal2
set_wire_rc -clock -layer Metal4
foreach cut {Via1 Via2 Via3 Via4} {
    set_layer_rc -via $cut -resistance $::env(VULSIM_TC_VIA_RESISTANCE_OHM)
}
