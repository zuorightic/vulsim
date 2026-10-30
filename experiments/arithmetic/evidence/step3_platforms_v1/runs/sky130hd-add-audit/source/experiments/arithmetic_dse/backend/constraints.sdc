# Convert the common ps/fF interface into the verified Liberty/STA units.
set time_scale $::env(VULSIM_TIME_TO_PS)
set cap_scale $::env(VULSIM_CAP_TO_FF)
set clk_period [expr {$::env(VULSIM_CLOCK_PERIOD_PS) / $time_scale}]
create_clock -name core_clk -period $clk_period [get_ports clk]
create_clock -name io_clk -period $clk_period
set_clock_uncertainty -setup [expr {$::env(VULSIM_SETUP_UNCERTAINTY_PS)/$time_scale}] [all_clocks]
set_clock_uncertainty -hold [expr {$::env(VULSIM_HOLD_UNCERTAINTY_PS)/$time_scale}] [all_clocks]
set_clock_transition [expr {$::env(VULSIM_CLOCK_TRANSITION_PS)/$time_scale}] [get_clocks core_clk]

# rstn is synchronous and remains timed; valid and data have identical I/O rules.
set non_clock_inputs [all_inputs -no_clocks]
set io_max [expr 0.20 * $clk_period]
if { [info exists ::env(VULSIM_IO_DELAY_MAX_PS)] && $::env(VULSIM_IO_DELAY_MAX_PS) ne "" } {
    set io_max [expr {$::env(VULSIM_IO_DELAY_MAX_PS) / $time_scale}]
}
set_input_delay -max $io_max -clock io_clk $non_clock_inputs
set_input_delay -min 0 -clock io_clk $non_clock_inputs
set_output_delay -max $io_max -clock io_clk [all_outputs]
set_output_delay -min 0 -clock io_clk [all_outputs]
set_driving_cell -lib_cell $::env(VULSIM_DRIVER_CELL) -pin $::env(VULSIM_DRIVER_PIN) $non_clock_inputs
set_load [expr {$::env(VULSIM_OUTPUT_LOAD_FF)/$cap_scale}] [all_outputs]
