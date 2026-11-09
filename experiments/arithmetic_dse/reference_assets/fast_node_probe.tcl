# Report-only experiment on a reopened saved database. No placement, sizing,
# routing, synthesis, or stored-SDC edits. Internal -probe paths preserve normal
# launch/capture paths; compare them and boundary slews before/after below.
source $::env(SCRIPTS_DIR)/load.tcl
load_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)
set_propagated_clock [all_clocks]
estimate_parasitics -global_routing
set prefix $::env(VULSIM_NODE_PREFIX)_before
source $::env(VULSIM_REFERENCE_ASSET)

set scope $::env(VULSIM_NODE_SCOPE)
set inputs {}; set outputs {}; set constants {}
set block [ord::get_db_block]
foreach inst [$block getInsts] {
    set name [$inst getName]
    if {![string match ${scope}* $name]} {continue}
    foreach term [$inst getITerms] {
        set master_term [$term getMTerm]
        if {[$master_term getSigType] in {POWER GROUND}} {continue}
        set direction [$master_term getIoType]
        if {$direction ni {INPUT OUTPUT}} {continue}
        set net [$term getNet]
        if {$net eq "NULL" || $net eq ""} {continue}
        set crosses 0
        foreach other [$net getITerms] {
            if {![string match ${scope}* [[$other getInst] getName]]} {set crosses 1}
        }
        if {[llength [$net getBTerms]]} {set crosses 1}
        if {!$crosses} {continue}
        set full $name/[[$term getMTerm] getName]
        set pin [get_pins -quiet [list $full]]
        if {[llength $pin]!=1} {error "node boundary pin missing or ambiguous: $full"}
        if {$direction eq "INPUT"} {
            set logic [sta::pin_sim_logic_value $pin]
            if {$logic eq "0" || $logic eq "1"} {lappend constants $pin} else {lappend inputs $pin}
        } elseif {$direction eq "OUTPUT"} {lappend outputs $pin}
    }
}
if {![llength $inputs] || ![llength $outputs]} {error "empty node input/output boundary"}
set f [open $::env(VULSIM_NODE_PREFIX)_boundaries.tsv w]
puts $f "pin\tkind\tslew_before"
foreach kind {inputs outputs constants} {
    foreach pin [set $kind] {puts $f "[get_full_name $pin]\t$kind\t[get_property $pin slew_max]"}
}
close $f
set_max_delay -probe -from $inputs -to $outputs $::env(VULSIM_NODE_TARGET)
set paths [find_timing_paths -from $inputs -to $outputs -path_delay max -group_path_count 1]
if {[llength $paths]!=1} {error "missing unique worst internal node path"}
set path [lindex $paths 0]; set points [get_property $path points]
set f [open $::env(VULSIM_NODE_PREFIX)_points.tsv w]
foreach point $points {puts $f "[get_full_name [get_property $point pin]]\t[format %.12g [get_property $point arrival]]"}
close $f
set first [lindex $points 0]; set last [lindex $points end]
set f [open $::env(VULSIM_NODE_PREFIX)_node.tsv w]
puts $f "inputs\toutputs\tconstants\tstart\tend\tstart_arrival\tend_arrival\tslack"
puts $f "[llength $inputs]\t[llength $outputs]\t[llength $constants]\t[get_full_name [get_property $first pin]]\t[get_full_name [get_property $last pin]]\t[get_property $first arrival]\t[get_property $last arrival]\t[get_property $path slack]"
close $f
report_checks -from $inputs -to $outputs -path_delay max -group_path_count 1 -format full_clock_expanded -digits 9 > $::env(VULSIM_NODE_PREFIX)_node.rpt
set f [open $::env(VULSIM_NODE_PREFIX)_slews_after.tsv w]
puts $f "pin\tslew_after"
foreach pin [concat $inputs $outputs $constants] {puts $f "[get_full_name $pin]\t[get_property $pin slew_max]"}
close $f
set prefix $::env(VULSIM_NODE_PREFIX)_after
source $::env(VULSIM_REFERENCE_ASSET)
puts "VULSIM_FAST_NODE_PROBE_COMPLETE"
