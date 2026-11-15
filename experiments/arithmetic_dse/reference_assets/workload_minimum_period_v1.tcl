# Derived from the frozen MAC32 stage9 fixed-DB full-setup readout.
# Profile values are substituted by the nine-workload runner. No optimization.

source $::env(SCRIPTS_DIR)/load.tcl
load_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)
set_propagated_clock [get_clocks core_clk]
estimate_parasitics -global_routing
set inputs {}
foreach p [all_inputs] {if {[get_full_name $p] ne "clk"} {lappend inputs $p}}
set outputs [all_outputs]
set dpins [all_registers -data_pins -edge_triggered]
set qpins [all_registers -output_pins -edge_triggered]
if {![llength $inputs] || ![llength $outputs] || ![llength $dpins] || ![llength $qpins]} {error "empty exact clock boundary"}
proc cp_worst {from to} {
    set best INF
    foreach path [find_timing_paths -from $from -to $to -path_delay max -group_path_count 1] {
        set s [get_property $path slack]
        if {$s<$best} {set best $s}
    }
    return $best
}
set rr [cp_worst $qpins $dpins]
set ir [cp_worst $inputs $dpins]
set ro [cp_worst $qpins $outputs]
set io [cp_worst $inputs $outputs]
if {$rr eq "INF" || $ir eq "INF" || $ro eq "INF" || $io ne "INF"} {error "incomplete fixed implementation path partition"}
set T @PERIOD@
set limit_rr [expr {$T-$rr}]
set limit_ir [expr {$T-$ir/0.8}]
set limit_ro [expr {$T-$ro/0.8}]
set threshold [expr {max($limit_rr,$limit_ir,$limit_ro)}]
set f [open {@OUTPUT@} w]
puts $f "class\tslack_ps\trequired_period_ps"
puts $f "register_to_register\t$rr\t$limit_rr"
puts $f "input_to_register\t$ir\t$limit_ir"
puts $f "register_to_output\t$ro\t$limit_ro"
puts $f "full_setup_threshold\t[expr {min($rr,$ir,$ro)}]\t$threshold"
foreach delta {-0.1 0.1} {
    set period [expr {$threshold+$delta}]
    create_clock -name core_clk -period $period [get_ports clk]
    create_clock -name io_clk -period $period
    set_clock_transition @TRANSITION@ [get_clocks core_clk]
    foreach clock {core_clk io_clk} {
        set_clock_uncertainty -setup @SETUP@ [get_clocks $clock]
        set_clock_uncertainty -hold @HOLD@ [get_clocks $clock]
    }
    set_propagated_clock [get_clocks core_clk]
    set_input_delay -clock [get_clocks io_clk] -max [expr {0.2*$period}] $inputs
    set_input_delay -clock [get_clocks io_clk] -min 0 $inputs
    set_output_delay -clock [get_clocks io_clk] -max [expr {0.2*$period}] $outputs
    set_output_delay -clock [get_clocks io_clk] -min 0 $outputs
    set s [expr {min([cp_worst $qpins $dpins],[cp_worst $inputs $dpins],[cp_worst $qpins $outputs])}]
    puts $f "threshold_check_$delta\t$s\t$period"
    if {($delta<0 && $s>=0) || ($delta>0 && $s<0)} {error "setup threshold bracket did not reproduce"}
}
close $f
puts "ABCD_MINIMUM_PERIOD_FIXED_DB_PASS"
