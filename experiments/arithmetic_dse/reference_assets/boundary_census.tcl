# Report-only mapped signal census; does not optimize or write design/SDC.
source $::env(SCRIPTS_DIR)/load.tcl
load_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)
set f [open $::env(REPORTS_DIR)/boundary_instances.tsv w]
set c [open $::env(REPORTS_DIR)/boundary_connections.tsv w]
puts $c "instance\tpin\tdirection\tnet"
foreach inst [[ord::get_db_block] getInsts] {
    set name [$inst getName]
    puts $f "$name\t[[$inst getMaster] getName]"
    foreach term [$inst getITerms] {
        set pin [$term getMTerm]
        if {[$pin getSigType] in {POWER GROUND} || [$pin getIoType] ni {INPUT OUTPUT}} {continue}
        set net [$term getNet]
        if {$net eq "NULL" || $net eq ""} {set wire "<unconnected:$name/[$pin getName]>"} else {set wire [$net getName]}
        puts $c "$name\t[$pin getName]\t[string tolower [$pin getIoType]]\t$wire"
    }
}
close $f
close $c
puts "BOUNDARY_CENSUS_COMPLETE; synthesis only; no node-label qualification"
