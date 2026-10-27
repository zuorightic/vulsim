# Liberty time/capacitance units are verified as ps/fF before a run starts.
set clk_period $::env(VULSIM_CLOCK_PERIOD_PS)
create_clock -name core_clk -period $clk_period [get_ports clk]
create_clock -name io_clk -period $clk_period
set_clock_uncertainty -setup 20 [all_clocks]
set_clock_uncertainty -hold 5 [all_clocks]
set_clock_transition 10 [get_clocks core_clk]

# rstn is synchronous and remains timed; valid and data have identical I/O rules.
set non_clock_inputs [all_inputs -no_clocks]
set io_max [expr 0.20 * $clk_period]
if { [info exists ::env(VULSIM_IO_DELAY_MAX_PS)] && $::env(VULSIM_IO_DELAY_MAX_PS) ne "" } {
    set io_max $::env(VULSIM_IO_DELAY_MAX_PS)
}
set_input_delay -max $io_max -clock io_clk $non_clock_inputs
set_input_delay -min 0 -clock io_clk $non_clock_inputs
set_output_delay -max $io_max -clock io_clk [all_outputs]
set_output_delay -min 0 -clock io_clk [all_outputs]
set_driving_cell -lib_cell BUFx2_ASAP7_75t_R -pin Y $non_clock_inputs
set_load 3.898 [all_outputs]
