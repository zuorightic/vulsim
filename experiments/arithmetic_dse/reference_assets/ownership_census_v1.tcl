# Exact report-only census of the loaded physical stage. No optimization/write.
set block [ord::get_db_block]
set f [open ${ownership_prefix}_instances.tsv w]
set c [open ${ownership_prefix}_connections.tsv w];puts $c "instance\tpin\tdirection\tnet"
foreach inst [$block getInsts] {
    set name [$inst getName];puts $f "$name\t[[$inst getMaster] getName]"
    foreach term [$inst getITerms] {
        set mt [$term getMTerm]
        if {[$mt getSigType] in {POWER GROUND} || [$mt getIoType] ni {INPUT OUTPUT}} {continue}
        set net [$term getNet]
        if {$net eq "NULL" || $net eq ""} {set n <unconnected:$name/[$mt getName]>} else {set n [$net getName]}
        puts $c "$name\t[$mt getName]\t[string tolower [$mt getIoType]]\t$n"
    }
}
close $f;close $c
set f [open ${ownership_prefix}_ports.tsv w];puts $f "port\tdirection\tnet"
foreach term [$block getBTerms] {
    set net [$term getNet]
    if {$net eq "NULL" || $net eq ""} {error "disconnected top terminal"}
    puts $f "[$term getName]\t[string tolower [$term getIoType]]\t[$net getName]"
}
close $f
set f [open ${ownership_prefix}_clock_nets.tsv w];puts $f "net"
foreach net [$block getNets] {if {[$net getSigType] eq "CLOCK"} {puts $f [$net getName]}}
close $f
puts VULSIM_OWNERSHIP_CENSUS_COMPLETE
