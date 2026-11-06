# Read-only native control labels: register Q->D and primary valid port->D.
source $::env(VULSIM_NATIVE_STATE_REQUESTS)
set output [open ${prefix}_native_state_paths.tsv w]
puts $output "id\tkind\tstart\tend\tstart_arrival\tend_arrival\tdelay\tpoints\tslack"
foreach request $vulsim_native_state_requests {
    lassign $request id kind from to
    if {$kind eq "port"} {
        set sources [get_ports -quiet $from]
        set source_names {}
        foreach pin $sources {lappend source_names [get_full_name $pin]}
    } elseif {$kind eq "register"} {
        set sources [get_pins -of_objects [get_cells -quiet -hierarchical $from] -filter {direction == output}]
        set source_names {}
        foreach pin $sources {lappend source_names [get_full_name $pin]}
    } else {error "invalid native state label kind: $kind"}
    set targets [get_pins -of_objects [get_cells -quiet -hierarchical $to] -filter {direction == input}]
    if {[llength $sources] == 0 || [llength $targets] == 0} {error "missing native state boundary: $id"}
    set paths [find_timing_paths -from $sources -to $targets -path_delay max -group_path_count 1]
    if {[llength $paths] != 1} {error "missing native state path: $id"}
    set path [lindex $paths 0]
    set points [get_property $path points]
    set last [lindex $points end]
    set end [get_full_name [get_property $last pin]]
    set b [get_property $last arrival]
    set found 0
    foreach point $points {
        set name [get_full_name [get_property $point pin]]
        if {[lsearch -exact $source_names $name] >= 0} {
            set start $name
            set a [get_property $point arrival]
            set found 1
            break
        }
    }
    if {!$found} {error "requested native source absent from path: $id"}
    set delay [expr {double($b)-double($a)}]
    if {$delay < -1e-6} {error "negative native state delay: $id"}
    puts $output "$id\t$kind\t$start\t$end\t[format %.12g $a]\t[format %.12g $b]\t[format %.12g $delay]\t[llength $points]\t[get_property $path slack]"
    set detail [open ${prefix}_native_${id}_points.tsv w]
    foreach point $points {puts $detail "[get_full_name [get_property $point pin]]\t[format %.12g [get_property $point arrival]]"}
    close $detail
    report_checks -from $sources -to $targets -path_delay max -group_path_count 1 \
        -format full_clock_expanded -digits 9 > ${prefix}_native_${id}.rpt
}
close $output
puts "VULSIM_NATIVE_STATE_LABELS_COMPLETE [llength $vulsim_native_state_requests]"
