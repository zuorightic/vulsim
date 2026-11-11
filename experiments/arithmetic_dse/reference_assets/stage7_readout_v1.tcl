# Report-only stage7 adapter. Source ONLY after the admitted snapshot, SDC and
# parasitics have been loaded. A mapped+Liberty resolver supplies exact pins;
# logical names or hierarchy prefixes alone are not endpoint certificates.
# stage7_requests: dict id -> {class stage from_pins from_ports through_pins to_pins}
# stage7_node_requests: same schema, node boundary inputs -> each dynamic output.
# Constants/aliases need their own connectivity certificate, not an empty query.
# Output path points are checked offline by the strict Liberty/net path reader.
proc s7_pins {names} {
    global s7_pin_index
    if {![info exists s7_pin_index]} {
        set s7_pin_index [dict create]
        foreach p [get_pins -of_objects [get_cells -hierarchical *]] {
            dict lappend s7_pin_index [string map {\\ ""} [get_full_name $p]] $p
        }
    }
    set out {}
    foreach name $names {
        set key [string map {\\ ""} $name]
        if {![dict exists $s7_pin_index $key] || [llength [dict get $s7_pin_index $key]] != 1} {error "stage7 missing/ambiguous pin: $name"}
        lappend out [lindex [dict get $s7_pin_index $key] 0]
    }
    return $out
}
proc s7_from {q} {
    set from [s7_pins [dict get $q from_pins]]
    foreach name [dict get $q from_ports] {
        set p [get_ports $name]
        if {[llength $p] != 1 || [get_full_name [lindex $p 0]] ne $name} {error "stage7 missing/ambiguous port: $name"}
        lappend from [lindex $p 0]
    }
    if {![llength $from]} {error "stage7 empty launch inventory"}
    return $from
}
proc s7_report {requests suffix save_points} {
    global stage7_prefix
    set f [open ${stage7_prefix}_${suffix}.tsv w]
    puts $f "request\tclass\tstage\tendpoint\tslack\tpoints"
    dict for {id q} $requests {
        if {![regexp {^[a-zA-Z0-9_]+$} $id]} {error "unsafe stage7 request id"}
        set from [s7_from $q];set targets [s7_pins [dict get $q to_pins]]
        if {![llength $targets]} {error "stage7 empty dynamic capture inventory: $id"}
        set through [s7_pins [dict get $q through_pins]];set index 0
        foreach to $targets {
            set command [list find_timing_paths -from $from -to $to -path_delay max -group_path_count 1]
            if {[llength $through]} {lappend command -through $through}
            set paths [uplevel #0 $command]
            if {[llength $paths] != 1} {error "stage7 uncovered endpoint: $id/[get_full_name $to]"}
            set path [lindex $paths 0];set file ${stage7_prefix}_${id}_${index}_points.tsv
            if {$save_points} {
                set p [open $file w]
                foreach point [get_property $path points] {
                    puts $p "[get_full_name [get_property $point pin]]\t[format %.12g [get_property $point arrival]]"
                }
                close $p
            }
            puts $f "$id\t[dict get $q class]\t[dict get $q stage]\t[get_full_name $to]\t[get_property $path slack]\t[file tail $file]"
            incr index
        }
    }
    close $f
}
if {![info exists stage7_requests] || ![dict size $stage7_requests]} {error "missing stage7 functional requests"}
if {![info exists stage7_node_requests] || ![dict size $stage7_node_requests]} {error "missing stage7 node requests"}
# Preserve actual boundary slew and full-path constraints around node probes.
set s7_slews [dict create]
dict for {id q} $stage7_node_requests {
    foreach p [concat [s7_from $q] [s7_pins [dict get $q to_pins]]] {
        dict set s7_slews $p [get_property $p slew_max]
    }
}
s7_report $stage7_requests full_before 1
dict for {id q} $stage7_node_requests {
    set inputs [s7_from $q];set outputs [s7_pins [dict get $q to_pins]]
    if {![llength $outputs]} {error "empty stage7 dynamic node output"}
    set_max_delay -probe -from $inputs -to $outputs 0
}
s7_report $stage7_node_requests independent_nodes 1
s7_report $stage7_requests full_after 0
set f [open ${stage7_prefix}_full_before.tsv r];set before [read $f];close $f
set f [open ${stage7_prefix}_full_after.tsv r];set after [read $f];close $f
if {$before ne $after} {error "stage7 node probe changed functional paths/constraints"}
dict for {pin before} $s7_slews {
    if {[get_property $pin slew_max] ne $before} {error "stage7 node probe changed boundary slew"}
}
puts "VULSIM_STAGE7_READOUT_COMPLETE"
