# Pure reports on the exact already loaded database; no optimization.
set f [open ${prefix}_reference_connections.tsv w]
puts $f "instance\tpin\tdirection\tnet"
foreach inst [[ord::get_db_block] getInsts] {
    foreach term [$inst getITerms] {
        set net [$term getNet]
        if {$net eq "NULL" || $net eq ""} {set name "<unconnected>"} else {set name [$net getName]}
        puts $f "[$inst getName]\t[[$term getMTerm] getName]\t[[$term getMTerm] getIoType]\t$name"
    }
}
close $f
if {![info exists ::env(VULSIM_REFERENCE_REQUESTS)]} {return}
source $::env(VULSIM_REFERENCE_REQUESTS)
set f [open ${prefix}_reference_paths.tsv w]
puts $f "id\tkind\tstart\tend\tstart_arrival\tend_arrival\tdelay\tpoints\tslack\tsetup_margin_s\tclk_skew_s"
foreach request $vulsim_reference_requests {
    lassign $request id kind from to
    if {$kind eq "port"} {set source_pins [get_ports -quiet $from]} else {
        set source_pins [get_pins -of_objects [get_cells -quiet -hierarchical $from] -filter {direction == output}]
    }
    set target_pins [get_pins -of_objects [get_cells -quiet -hierarchical $to] -filter {direction == input}]
    if {![llength $source_pins] || ![llength $target_pins]} {error "reference boundary missing: $id"}
    set source_names {};foreach pin $source_pins {lappend source_names [get_full_name $pin]}
    set paths [find_timing_paths -from $source_pins -to $target_pins -path_delay max -group_path_count 1]
    if {[llength $paths]!=1} {error "reference path missing: $id"}
    set path [lindex $paths 0];set points [get_property $path points];set found 0
    foreach point $points {
        set name [get_full_name [get_property $point pin]]
        if {[lsearch -exact $source_names $name]>=0} {set start $name;set a [get_property $point arrival];set found 1;break}
    }
    if {!$found} {error "reference launch point missing: $id"}
    set last [lindex $points end];set end [get_full_name [get_property $last pin]];set b [get_property $last arrival]
    set delta [expr {double($b)-double($a)}]
    if {$delta < -1e-6} {error "reference negative delay: $id"}
    puts $f "$id\t$kind\t$start\t$end\t[format %.12g $a]\t[format %.12g $b]\t[format %.12g $delta]\t[llength $points]\t[get_property $path slack]\t[$path margin]\t[$path clk_skew]"
    set detail [open ${prefix}_reference_${id}_points.tsv w]
    foreach point $points {puts $detail "[get_full_name [get_property $point pin]]\t[format %.12g [get_property $point arrival]]"}
    close $detail
    report_checks -from $source_pins -to $target_pins -path_delay max -group_path_count 1 -format full_clock_expanded -digits 9 > ${prefix}_reference_${id}.rpt
}
close $f
puts "VULSIM_REFERENCE_PATHS_COMPLETE [llength $vulsim_reference_requests]"
