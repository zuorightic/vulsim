# Report-only adapter, sourced in an already loaded, admitted physical snapshot.
# Caller resolves explicit data Q/D pins against Liberty and the complete mapped
# FF/bank census. This file never loads, optimizes or writes an implementation.
# Required: context_prefix, context_nodes (id/scope pairs), context_launch_data
# and context_banks (bank/list-of-data-D-pins pairs).
proc context_points {path filename} {
    set f [open $filename w]
    foreach point [get_property $path points] {
        puts $f "[get_full_name [get_property $point pin]]\t[format %.12g [get_property $point arrival]]"
    }
    close $f
}
proc context_pin_list {names} {
    global context_pin_index
    if {![info exists context_pin_index]} {
        set context_pin_index [dict create]
        foreach pin [get_pins -of_objects [get_cells -hierarchical *]] {
            set key [string map {\\ ""} [get_full_name $pin]]
            dict lappend context_pin_index $key $pin
        }
    }
    set result {}
    foreach name $names {
        set key [string map {\\ ""} $name]
        if {![dict exists $context_pin_index $key]} {error "missing normalized explicit data pin: $name"}
        set pin [dict get $context_pin_index $key]
        if {[llength $pin] != 1} {error "missing explicit data pin: $name"}
        lappend result [lindex $pin 0]
    }
    if {![llength $result]} {error "empty explicit data pins"}
    return $result
}
set f [open ${context_prefix}_instances.tsv w]
set c [open ${context_prefix}_connections.tsv w]
puts $c "instance\tpin\tdirection\tnet"
set dynamic_inputs [dict create];set dynamic_outputs [dict create];set constants [dict create]
set logic [open ${context_prefix}_logic.tsv w];puts $logic "pin\tlogic"
set clocks [open ${context_prefix}_clock_nets.tsv w];puts $clocks "net"
foreach net [[ord::get_db_block] getNets] {
    if {[$net getSigType] eq "CLOCK"} {puts $clocks [$net getName]}
}
close $clocks
set endpoints [open ${context_prefix}_endpoints.tsv w];puts $endpoints "node\tkind\tpin"
set slews [dict create]
foreach inst [[ord::get_db_block] getInsts] {
    set name [$inst getName]
    puts $f "$name\t[[$inst getMaster] getName]"
    foreach term [$inst getITerms] {
        set mt [$term getMTerm]
        if {[$mt getSigType] in {POWER GROUND} || [$mt getIoType] ni {INPUT OUTPUT}} {continue}
        set net [$term getNet]
        set full $name/[$mt getName]
        if {$net eq "NULL" || $net eq ""} {
            puts $c "$name\t[$mt getName]\t[string tolower [$mt getIoType]]\t<unconnected:$full>"
            continue
        }
        puts $c "$name\t[$mt getName]\t[string tolower [$mt getIoType]]\t[$net getName]"
        if {[$net getSigType] eq "CLOCK"} {continue}
        foreach {id scope} $context_nodes {
            if {![string match ${scope}* $name]} {continue}
            set crosses [expr {[llength [$net getBTerms]] > 0}]
            foreach other [$net getITerms] {
                if {![string match ${scope}* [[$other getInst] getName]]} {set crosses 1}
            }
            if {!$crosses} {continue}
            set pin [lindex [context_pin_list [list $full]] 0]
            set value [sta::pin_sim_logic_value $pin]
            if {$value ni {0 1}} {set value X}
            puts $logic "$full\t$value"
            if {$value ne "X"} {set kind constants} elseif {[$mt getIoType] eq "INPUT"} {set kind inputs} else {set kind outputs}
            puts $endpoints "$id\t$kind\t$full"
            if {$kind eq "inputs"} {dict lappend dynamic_inputs $id $full}
            if {$kind eq "outputs"} {dict lappend dynamic_outputs $id $full}
            dict set slews $full [get_property $pin slew_max]
        }
    }
}
close $f;close $c;close $logic;close $endpoints
set from [context_pin_list $context_launch_data]
set context_launch_data {}
foreach pin $from {lappend context_launch_data [get_full_name $pin]}
set through [context_pin_list [dict get $dynamic_outputs producer]]
set requests [open ${context_prefix}_data_requests.tsv w];puts $requests "bank\tkind\tpin"
proc context_data_reports {filename save_points} {
    global context_prefix context_banks context_launch_data from through dynamic_outputs requests
    set f [open $filename w];puts $f "bank\tstart\tend\tslack"
    foreach {bank names} $context_banks {
        set to [context_pin_list $names]
        if {$save_points} {
            foreach kind {from through to} {
                foreach pin [set $kind] {puts $requests "$bank\t$kind\t[get_full_name $pin]"}
            }
        }
        set paths [find_timing_paths -from $from -through $through -to $to -path_delay max -group_path_count 1]
        if {[llength $paths] != 1} {error "missing through-producer functional path: $bank"}
        set path [lindex $paths 0];set points [get_property $path points];set start ""
        foreach point $points {
            set name [get_full_name [get_property $point pin]]
            if {$name in $context_launch_data} {set start $name;break}
        }
        if {$start eq ""} {error "launch Q absent from through-data path"}
        puts $f "$bank\t$start\t[get_full_name [get_property [lindex $points end] pin]]\t[get_property $path slack]"
        if {$save_points} {context_points $path ${context_prefix}_data_${bank}_points.tsv}
    }
    close $f
}
context_data_reports ${context_prefix}_data_paths.tsv 1
close $requests
set paths_table [open ${context_prefix}_node_paths.tsv w];puts $paths_table "node\toutput\tfile"
foreach {id scope} $context_nodes {
    set inputs [context_pin_list [dict get $dynamic_inputs $id]]
    set outputs [context_pin_list [dict get $dynamic_outputs $id]]
    set_max_delay -probe -from $inputs -to $outputs 0
    set index 0
    foreach output $outputs {
        set paths [find_timing_paths -from $inputs -to $output -path_delay max -group_path_count 1]
        if {[llength $paths] != 1} {error "uncovered dynamic output: $id"}
        set file ${context_prefix}_node_${id}_${index}_points.tsv
        context_points [lindex $paths 0] $file
        puts $paths_table "$id\t[get_full_name $output]\t[file tail $file]"
        incr index
    }
}
close $paths_table
context_data_reports ${context_prefix}_data_after.tsv 0
foreach suffix {data_paths data_after} {
    set f [open ${context_prefix}_${suffix}.tsv r];set $suffix [read $f];close $f
}
if {$data_paths ne $data_after} {error "probe changed functional data constraints or paths"}
dict for {name before} $slews {
    if {[get_property [lindex [context_pin_list [list $name]] 0] slew_max] ne $before} {error "probe changed boundary slew"}
}
puts "VULSIM_CONTEXT_READOUT_COMPLETE"
