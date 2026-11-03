# Pure reporting over the exact database loaded by snapshot.tcl. Labels use
# Q->D point arrival differences, excluding clk->Q, setup and clock insertion.
if {![info exists ::env(VULSIM_LABEL_REQUESTS)]} { return }
source $::env(VULSIM_LABEL_REQUESTS)
set label_file [open ${prefix}_model_paths.tsv w]
puts $label_file "sample_id\tstart_pin\tend_pin\tstart_arrival_native\tend_arrival_native\tdata_delay_native\tpoint_count\tslack_native\tsetup_margin_s\tclk_skew_s"
foreach request $vulsim_label_requests {
    lassign $request sample_id src_pattern dst_pattern
    set sources [get_cells -quiet -hierarchical $src_pattern]
    set targets [get_cells -quiet -hierarchical $dst_pattern]
    if {[llength $sources] == 0 || [llength $targets] == 0} {
        error "missing characterization boundary: $sample_id $src_pattern $dst_pattern"
    }
    set source_pins [get_pins -of_objects $sources -filter {direction == output}]
    set target_pins [get_pins -of_objects $targets -filter {direction == input}]
    set paths [find_timing_paths -from $source_pins -to $target_pins -path_delay max -group_path_count 1]
    if {[llength $paths] != 1} {error "missing characterization path: $sample_id"}
    set path [lindex $paths 0]
    set points [get_property $path points]
    set first [lindex $points 0]
    set last [lindex $points end]
    set a [get_property $first arrival]
    set b [get_property $last arrival]
    set start_pin [get_full_name [get_property $first pin]]
    set end_pin [get_full_name [get_property $last pin]]
    # find_timing_paths may include the launch DFF's clock point even when
    # selected by Q. Select the first actual requested source Q explicitly.
    set found 0
    foreach point $points {
        set pin [get_property $point pin]
        if {[lsearch -exact $source_pins $pin] >= 0} {
            set a [get_property $point arrival]
            set start_pin [get_full_name $pin]
            set found 1
            break
        }
    }
    if {!$found} {error "launch Q absent from characterization path: $sample_id"}
    set delay [expr {double($b)-double($a)}]
    if {$delay < -1e-6} {error "negative characterization data delay: $sample_id"}
    puts $label_file "$sample_id\t$start_pin\t$end_pin\t[format %.12g $a]\t[format %.12g $b]\t[format %.12g $delay]\t[llength $points]\t[get_property $path slack]\t[$path margin]\t[$path clk_skew]"
    set detail [open ${prefix}_model_${sample_id}_points.tsv w]
    foreach point $points {
        puts $detail "[get_full_name [get_property $point pin]]\t[format %.12g [get_property $point arrival]]"
    }
    close $detail
    # report_checks invalidates borrowed OpenSTA path/point handles. Consume
    # every point first, then request the independent human-readable report.
    report_checks -from $source_pins -to $target_pins -path_delay max -group_path_count 1 \
        -format full_clock_expanded -digits 9 > ${prefix}_model_${sample_id}.rpt
}
close $label_file
puts "VULSIM_MODEL_LABELS_COMPLETE [llength $vulsim_label_requests]"
