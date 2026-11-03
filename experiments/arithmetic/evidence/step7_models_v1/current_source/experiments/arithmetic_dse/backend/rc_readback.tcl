# Report physical SI quantities independently of Liberty's display units.
set rc_file [open ${prefix}_layer_rc.tsv w]
puts $rc_file "layer\tresistance_ohm_per_um\tcapacitance_fF_per_um"
set tech [ord::get_db_tech]
for {set level 1} {$level <= [$tech getRoutingLayerCount]} {incr level} {
    set layer [$tech findRoutingLayer $level]
    lassign [est::dblayer_wire_rc $layer] r c
    puts $rc_file "[$layer getName]\t[format %.17g [expr {$r/1e6}]]\t[format %.17g [expr {$c*1e9}]]"
}
close $rc_file
