"""Validated platform identities and explicit physical-unit conversion."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import re

PROFILES = Path(__file__).resolve().parent/'configs/platforms'
TIME_PS = {'ps':1.0, 'ns':1000.0}
CAP_FF = {'ff':1.0, 'pf':1000.0}


def profile(platform):
    if platform not in ('asap7','nangate45','sky130hd','gf180'):
        raise ValueError(f'unsupported platform: {platform}')
    path=PROFILES/(platform+'.json')
    data=json.loads(path.read_text())
    if data['platform'] != platform or data['schema'] != 'arithmetic-platform-v1':
        raise ValueError('platform profile identity mismatch')
    data['profile_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    return data


def unit_scale(value, unit, *, kind):
    scales=TIME_PS if kind=='time' else CAP_FF if kind=='capacitance' else None
    key=unit.lower() if kind=='capacitance' else unit
    if scales is None or key not in scales or not math.isfinite(value) or value <= 0:
        raise ValueError(f'unsupported {kind} unit: {value} {unit}')
    return value*scales[key]


def library_data(paths, selected=None):
    p=selected or profile('asap7')
    libraries,cells=[],{}
    if len(paths)!=p['library_count'] or len(set(map(str,paths)))!=len(paths):
        raise ValueError('unexpected number of selected platform libraries')
    for path in paths:
        path=Path(path)
        text=gzip.open(path,'rt').read() if path.suffix=='.gz' else path.read_text()
        # Remove comments before parsing group headers (Nangate has commented
        # cell examples); quoted cell names are common in Sky130/GF180.
        text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
        def attribute(name):
            m=re.search(r'\b'+name+r'\s*:\s*([^;]+);',text)
            if not m:raise ValueError(f'missing {name}: {path}')
            return m[1].strip().strip('"')
        time=re.fullmatch(r'([\d.eE+-]+)\s*(ps|ns)',attribute('time_unit'))
        cap=re.search(r'capacitive_load_unit\s*\(\s*([\d.eE+-]+)\s*,\s*"?([fp]f)"?\s*\)',text,re.I)
        if not time or not cap:raise ValueError('unrecognized Liberty units')
        time_ps=unit_scale(float(time[1]),time[2],kind='time')
        cap_ff=unit_scale(float(cap[1]),cap[2],kind='capacitance')
        voltage,temperature=float(attribute('nom_voltage')),float(attribute('nom_temperature'))
        if (not re.fullmatch(p['library_name_pattern'],path.name)
                or voltage!=p['voltage_V'] or temperature!=p['temperature_C']
                or time_ps!=unit_scale(1,p['time_unit'],kind='time')
                or cap_ff!=unit_scale(1,p['capacitance_unit'],kind='capacitance')):
            raise ValueError(f'wrong library/PVT/units for {p["platform"]}: {path}')
        lib={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'voltage_V':voltage,'temperature_C':temperature,'time_unit':attribute('time_unit'),
             'capacitance_unit':p['capacitance_unit'],'time_to_ps':time_ps,'capacitance_to_fF':cap_ff}
        libraries.append(lib)
        matches=list(re.finditer(r'\bcell\s*\(\s*"?([^"\s)]+)"?\s*\)\s*\{',text))
        for i,m in enumerate(matches):
            body=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)]
            area=re.search(r'\barea\s*:\s*([\d.eE+-]+)',body)
            if not area:raise ValueError(f'cell without area: {m[1]}')
            value={'area_um2':float(area[1]),'sequential':bool(re.search(r'\b(?:ff|ff_bank|latch|latch_bank)\s*\(',body))}
            if m[1] in cells:raise ValueError('duplicate selected Liberty cell')
            cells[m[1]]=value
    if p['driver_cell'] not in cells:raise ValueError('profile I/O driver absent from selected libraries')
    return libraries,cells


def report_scales(text, selected):
    result={}
    for name,kind,expected in [('time','time',selected['time_unit']),
                               ('capacitance','capacitance',selected['capacitance_unit'])]:
        m=re.search(r'^\s*'+name+r'\s+([\d.eE+-]+)\s*(ps|ns|fF|pF|s|F)\s*$',text,re.M)
        if not m:raise ValueError(f'unknown/missing report_units {name}: {text}')
        value,unit=float(m[1]),m[2]
        # OpenSTA may use scientific SI spellings.
        scale=(value*1e12 if unit=='s' else value*1e15 if unit=='F'
               else unit_scale(value,unit,kind=kind))
        if not math.isclose(scale,unit_scale(1,expected,kind=kind),rel_tol=1e-9):
            raise ValueError(f'STA and selected Liberty disagree on {name}')
        result[name]={'raw_unit':m[0].strip(),'to_ps' if kind=='time' else 'to_fF':scale}
    return result


def resolve_environment(raw):
    """Resolve the same optional assets as ORFS load.tcl/floorplan.tcl.

    Keep raw make output separately: an empty variable is not a missing asset
    when the flow explicitly selects a platform default.
    """
    effective=dict(raw)
    platform_dir=Path(raw['PLATFORM_DIR'])
    origins={}
    key='LAYER_PARASITICS_FILE'
    if not raw.get(key):
        effective[key]=str(platform_dir/'setRC.tcl')
        origins[key]='load.tcl: PLATFORM_DIR/setRC.tcl fallback'
    else:
        origins[key]='explicit make environment'
    key='MAKE_TRACKS'
    if raw.get(key):
        origins[key]='explicit make environment'
    elif (platform_dir/'make_tracks.tcl').is_file():
        effective[key]=str(platform_dir/'make_tracks.tcl')
        origins[key]='floorplan.tcl: PLATFORM_DIR/make_tracks.tcl fallback'
    else:
        effective[key]=''
        origins[key]='floorplan.tcl: OpenROAD make_tracks command (no script)'
    return effective,origins


def validate_environment(effective, selected):
    if effective['PLATFORM']!=selected['platform'] or effective['CORNER']!=selected['corner']:
        raise ValueError('effective platform/corner differs from requested profile')
    for key,value in selected['make_overrides'].items():
        if effective.get(key)!=str(value):
            raise ValueError(f'platform override not effective: {key}: {effective.get(key)} != {value}')
    if effective.get('TEMPERATURE'):
        if float(effective['TEMPERATURE'].lower().rstrip('c'))!=selected['temperature_C']:
            raise ValueError('effective temperature differs from Liberty')
    if effective.get('VOLTAGE') and float(effective['VOLTAGE'])!=selected['voltage_V']:
        raise ValueError('effective voltage differs from Liberty')
    if (effective.get('ABC_DRIVER_CELL')!=selected['driver_cell']
            or not math.isclose(float(effective['ABC_LOAD_IN_FF']),
                                selected.get('abc_load_fF',selected['output_load_fF']),rel_tol=1e-9)):
        raise ValueError('ABC driver/load differs from the selected fF contract')
    required=('TECH_LEF','SC_LEF','RCX_RULES','LAYER_PARASITICS_FILE','PDN_TCL')
    optional=('MAKE_TRACKS','FASTROUTE_TCL','TAPCELL_TCL','ADDER_MAP_FILE',
              'LATCH_MAP_FILE','CLKGATE_MAP_FILE','ADDITIONAL_LEFS')
    for key in required+optional:
        if key in optional and not effective.get(key):continue
        if not effective.get(key) or any(not Path(s).is_file() for s in effective[key].split()):
            raise ValueError(f'missing selected platform asset: {key}')
        platform_dir=Path(effective['PLATFORM_DIR']).resolve()
        if platform_dir.name!=selected['platform']:
            raise ValueError(f'physical asset from wrong platform: {key}')
        for value in effective[key].split():
            asset=Path(value)
            if asset.resolve().is_relative_to(platform_dir):continue
            shared=selected.get('shared_platform_assets',{}).get(key)
            if (not shared or asset!=platform_dir/shared['logical_relative']
                    or asset.resolve()!=(platform_dir/shared['resolved_relative']).resolve()
                    or hashlib.sha256(asset.read_bytes()).hexdigest()!=shared['sha256']):
                raise ValueError(f'physical asset from wrong platform: {key}')
