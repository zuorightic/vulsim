# Read-only arithmetic boundary discovery from the same certified cell census.
# stage67_owners and stage67_masters are checked before a timing query is made.
set stage67_actual [dict create]
foreach inst [[ord::get_db_block] getInsts] {
    set name [string map {\\ ""} [$inst getName]]
    if {![dict exists $stage67_owners $name] || ![dict exists $stage67_masters $name] || [dict get $stage67_masters $name] ne [[$inst getMaster] getName]} {error "stage67 stale ownership certificate"}
    dict set stage67_actual $name 1
}
if {[lsort [dict keys $stage67_actual]] ne [lsort [dict keys $stage67_owners]]} {error "stage67 extra/missing certified cell"}
set dynamic_inputs [dict create];set dynamic_outputs [dict create]
set endpoint_file [open ${stage7_prefix}_endpoints.tsv w]
puts $endpoint_file "node\tkind\tpin\tlogic"
foreach inst [[ord::get_db_block] getInsts] {
    set name [string map {\\ ""} [$inst getName]]
    set owner [dict get $stage67_owners $name]
    if {![dict exists $stage67_node_stages $owner]} {continue}
    foreach term [$inst getITerms] {
        set mt [$term getMTerm]
        if {[$mt getSigType] in {POWER GROUND} || [$mt getIoType] ni {INPUT OUTPUT}} {continue}
        set net [$term getNet]
        if {$net eq "NULL" || $net eq ""} {error "stage67 disconnected arithmetic signal pin"}
        if {[$net getSigType] eq "CLOCK"} {error "clock inside arithmetic owner"}
        set crosses [expr {[llength [$net getBTerms]] > 0}]
        foreach peer [$net getITerms] {
            set other [string map {\\ ""} [[$peer getInst] getName]]
            if {[dict get $stage67_owners $other] ne $owner} {set crosses 1}
        }
        if {!$crosses} {continue}
        set full "[$inst getName]/[$mt getName]"
        set pin [lindex [get_pins [list $full]] 0]
        # get_pins pattern syntax treats brackets specially; the complete index
        # in the frozen reader resolves exact physical names instead.
        if {![info exists stage67_pin_index]} {
            set stage67_pin_index [dict create]
            foreach p [get_pins -of_objects [get_cells -hierarchical *]] {dict lappend stage67_pin_index [string map {\\ ""} [get_full_name $p]] $p}
        }
        set key [string map {\\ ""} $full]
        if {![dict exists $stage67_pin_index $key] || [llength [dict get $stage67_pin_index $key]]!=1} {error "stage67 ambiguous boundary pin"}
        set pin [lindex [dict get $stage67_pin_index $key] 0]
        set logic [sta::pin_sim_logic_value $pin]
        if {$logic ni {0 1}} {set logic X}
        if {$logic ne "X"} {set kind constants} elseif {[$mt getIoType] eq "INPUT"} {set kind inputs} else {set kind outputs}
        puts $endpoint_file "$owner\t$kind\t$full\t$logic"
        if {$kind eq "inputs"} {dict lappend dynamic_inputs $owner $full}
        if {$kind eq "outputs"} {dict lappend dynamic_outputs $owner $full}
    }
}
close $endpoint_file
set stage7_node_requests [dict create]
dict for {node stage} $stage67_node_stages {
    if {![dict exists $dynamic_inputs $node] || ![dict exists $dynamic_outputs $node]} {error "stage67 empty arithmetic boundary needs separate constant/alias proof"}
    dict set stage7_node_requests $node [dict create class independent_node stage $stage from_pins [dict get $dynamic_inputs $node] from_ports {} through_pins {} to_pins [dict get $dynamic_outputs $node]]
}
# The parent adapter supplies per-endpoint max paths and probe invariance.
source $stage67_readout_script
