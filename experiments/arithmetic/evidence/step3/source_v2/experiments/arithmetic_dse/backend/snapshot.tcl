# Reopen the exact stage database; never substitute metrics from another stage.
source $::env(SCRIPTS_DIR)/load.tcl
load_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)
set prefix $::env(REPORTS_DIR)/vulsim_$::env(VULSIM_EVAL_STAGE)
if { $::env(VULSIM_EVAL_STAGE) eq "grt" } {
    set_propagated_clock [all_clocks]
    estimate_parasitics -global_routing
} elseif { $::env(VULSIM_EVAL_STAGE) eq "final" } {
    set_propagated_clock [all_clocks]
    read_spef $::env(RESULTS_DIR)/6_final.spef
}

tee -quiet -file ${prefix}_units.rpt {report_units}
report_worst_slack -max -digits 6 > ${prefix}_setup.rpt
report_worst_slack -min -digits 6 > ${prefix}_hold.rpt
report_tns -max -digits 6 > ${prefix}_setup_tns.rpt
report_tns -min -digits 6 > ${prefix}_hold_tns.rpt
report_clock_min_period -include_port_paths > ${prefix}_period.rpt
check_setup -verbose > ${prefix}_coverage.rpt
report_checks -path_delay max -format full_clock_expanded -digits 6 \
    -fields {slew cap input net fanout} > ${prefix}_paths_max.rpt
report_checks -path_delay min -format full_clock_expanded -digits 6 \
    -fields {slew cap input net fanout} > ${prefix}_paths_min.rpt
report_checks -unconstrained > ${prefix}_unconstrained.rpt
tee -quiet -file ${prefix}_area.rpt {report_design_area}

# Preserve physical master counts and geometry for independent area checks.
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
array set counts {}
array set areas {}
array set fillers {}
array set types {}
foreach inst [$block getInsts] {
    set master [$inst getMaster]
    set name [$master getName]
    if { ![info exists counts($name)] } { set counts($name) 0 }
    incr counts($name)
    set areas($name) [expr {double([$master getWidth]) * [$master getHeight] / ($dbu * $dbu)}]
    set fillers($name) [$master isFiller]
    set types($name) [$master getType]
}
set out [open ${prefix}_cells.tsv w]
foreach name [lsort [array names counts]] {
    puts $out "$name\t$counts($name)\t$areas($name)\t$fillers($name)\t$types($name)"
}
close $out
puts "VULSIM_SNAPSHOT_COMPLETE $::env(VULSIM_EVAL_STAGE)"
