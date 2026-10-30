# Preserve the platform's TC wire RC. Its current setRC.tcl only assigns cut
# layer RC in BC/WC; PSM also needs explicit TC cut-layer resistance. The
# selected 5LM_1TM_9K_9t technology LEF gives every default Via1..Via4 4.5 ohm.
# Python preflight checks that basis before allowing this adapter.
if {$::env(CORNER) ne "TC" || $::env(METAL_OPTION) ne "5LM_1TM" || $::env(TRACK_OPTION) ne "9t" || $::env(KVALUE) ne "9"} {
    error "gf180 TC via adapter used with an unvalidated stack/corner"
}
source $::env(PLATFORM_DIR)/setRC.tcl
foreach cut {Via1 Via2 Via3 Via4} {
    set_layer_rc -via $cut -resistance $::env(VULSIM_TC_VIA_RESISTANCE_OHM)
}
