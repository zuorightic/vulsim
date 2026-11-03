"""Recompute native interval evidence from typed graphs and original bytes.

Portable verification checks graph-derived features and recorded RTL values.
Actual Q-to-D/area/boundary labels require the retained external run archive.
"""
import hashlib
import json
import random
from .model_mul_intervals import interval,source,key,features


def verify_intervals(index,objects,documents,replay,same):
    metadata=index['interval_evidence'];graphs={};graph_files={};specs={}
    for name,document in metadata['graphs'].items():
        report=documents[document];h=report['graph_sha256']
        same(json.loads(report['graph_identity_text']),report['graph'],'native interval graph serialization')
        same(hashlib.sha256(report['graph_identity_text'].encode()).hexdigest(),h,'native interval graph identity')
        if h in graphs:raise ValueError('duplicate native interval graph identity')
        graphs[h]=report;graph_files[name]=(index['documents'][document],h)
        groups=report['graph']['regions'][0]['legal_groups']
        for first in range(len(groups)):
            for last in range(first,len(groups)):specs[h,first,last]=interval(report,first,last)
    receipt=documents[metadata['functional']]
    same(receipt['version'],'arithmetic-native-interval-functional-v1','actual interval functional receipt schema')
    same({r['file']:(r['sha256'],r['graph_sha256']) for r in receipt['graphs']},graph_files,'functional receipt binds actual native graphs')
    same(receipt['native_graphs'],len(graphs),'functional graph count')
    same(receipt['intervals'],len(specs),'functional interval count')
    from regression.arithmetic_model_intervals import expected,check_trimmed
    seen=set()
    for observation in receipt['observations']:
        h,first,last,trial=(observation[k] for k in ('graph_sha256','first','last','trial'));identity=(h,first,last,trial)
        if identity in seen or type(trial) is not int or not 0<=trial<8:raise ValueError('duplicate or invalid interval functional observation')
        seen.add(identity);s=specs[h,first,last];inputs=[int(v,16) for v in observation['inputs_hex']]
        if len(inputs)!=len(s['input_widths']) or any(v<0 or v>=1<<w for v,w in zip(inputs,s['input_widths'])):raise ValueError('invalid interval functional input shape')
        actual=expected(graphs[h],s,inputs)
        if actual!=int(observation['expected_hex'],16):raise ValueError('independent integer interval output mismatch')
        if actual!=int(observation['observed_hex'],16):raise ValueError('actual RTL interval observation mismatch')
    same(seen,{(*identity,trial) for identity in specs for trial in range(8)},'complete interval/trial observation set')
    same(receipt['RTL_integer_checks'],len(seen),'actual RTL observation count')
    rng=random.Random(receipt['seed']);trim_checks=0
    for name in sorted(metadata['graphs']):
        h=graph_files[name][1]
        for identity,spec in specs.items():
            if identity[0]==h:trim_checks+=check_trimmed(graphs[h],spec,rng)
    same(receipt['untrimmed_integer_checks'],trim_checks,'independent untrimmed boundary checks')
    admission=documents[metadata['admission']];data=documents[metadata['dataset']]
    same(data['admission_sha256'],index['documents'][metadata['admission']],'interval dataset admission identity')
    same(data['protocol_sha256'],admission['supplemental_protocol']['sha256'],'interval dataset sampling protocol')
    same(data['protocol_sha256'],index['text_files']['model_mul_interval_protocol.json'],'archived interval protocol bytes')
    same(data['label_audit_sha256'],index['text_files']['model_mul_interval_labels.json'],'archived boundary label protocol')
    tasks={t['id']:t for t in admission['tasks']};labels={}
    for task_id,refs in metadata['bundles'].items():
        t=tasks[task_id];contract=json.loads(objects[refs['contract']]);items=[]
        same(refs['contract'],t['sample_contract_sha256'],'interval original contract identity')
        same(refs['rtl'],t['rtl_sha256'],'interval original RTL identity')
        same(contract['split'],t['split'],'interval bundle split')
        for label in contract['labels']:
            identity=(label['graph_sha256'],label['first'],label['last']);s=specs[identity]
            items.append((graphs[identity[0]],s));labels[task_id,label['id']]=label
        text,regenerated=source(items)
        same(text,objects[refs['rtl']],'actual interval RTL regenerated from typed graph')
        same(regenerated,contract['labels'],'actual interval bit maps and labels')
    seen_rows=set();raw_count=0
    for row in data['rows']:
        if row['id'] in seen_rows:raise ValueError('duplicate interval dataset row')
        seen_rows.add(row['id']);task_id,sample,stage=row['id'].split('/');t=tasks[task_id];label=labels[task_id,sample]
        same(row['spec'],label,'interval row matches original contract')
        s=specs[label['graph_sha256'],label['first'],label['last']]
        for field,value in row['features'].items():
            if field!='log_width' and type(value) is not int:raise ValueError('interval count/width feature must be a JSON integer')
        for field in ('capture_DFFs','launch_DFFs','elided_or_merged_capture_bits','elided_or_merged_launch_bits'):
            if type(row[field]) is not int or row[field]<0:raise ValueError('interval mapped boundary count must be a nonnegative JSON integer')
        same(row['features'],features(s),'pre-mapping interval features')
        same(row['interval_key'],key(s),'registered interval class')
        for field,task_field in [('platform','platform'),('split','split'),('profile_sha256','profile_sha256'),('source_sha256','rtl_sha256'),('contract_sha256','sample_contract_sha256'),('period_ps','period_ps'),('abc_target_ps','abc_target_ps')]:same(row[field],t[task_field],'interval row '+field)
        same(row['stage'],stage,'interval label stage')
        if stage not in ('synth','grt'):raise ValueError('unregistered interval stage')
        if replay:
            run=replay[row['manifest_sha256']];measured=run['stages'][stage];raw=measured['labels'][sample]
            same(run['rtl_sha256'],t['rtl_sha256'],'measured interval source')
            same(run['contract_sha256'],t['sample_contract_sha256'],'measured interval contract')
            same(run['manifest']['admission_id'],admission['id'],'measured interval admission')
            same(run['manifest']['task_id'],task_id,'measured interval task')
            same(run['manifest']['period_ps'],t['period_ps'],'measured interval SDC context')
            same(run['manifest']['abc_target_ps'],t['abc_target_ps'],'measured interval ABC context')
            same(run['manifest']['platform_profile']['profile_sha256'],t['profile_sha256'],'measured interval profile')
            same(raw['data_delay_ps'],row['delay_ps'],'actual interval Q-D path delay')
            same(raw['points_sha256'],row['points_sha256'],'actual interval path points')
            filename=f'reports/{t["platform"]}/arithmetic_probe/base/vulsim_{stage}_instances.tsv'
            same(run['files'][filename],row['instances_sha256'],'actual interval instance file')
            comb=0.;capture=launch=0
            for name,master in measured['instances']:
                if not name.startswith(label['instance_scope']) or master not in run['cells']:continue
                cell=run['cells'][master]
                if cell['sequential']:
                    capture+=name.startswith(label['instance_scope']+'dst') or name.startswith(label['instance_scope']+'y')
                    launch+=name.startswith(label['instance_scope']+'src')
                elif name.startswith(label['arithmetic_scope']):comb+=cell['area_um2']
            if not 0<capture<=s['capture_width'] or not 0<launch<=sum(s['input_widths']) or comb<=0:raise ValueError('actual interval mapped boundary/area outside declared capacity')
            same(comb,row['comb_area_um2'],'actual unique interval core area')
            same(capture,row['capture_DFFs'],'actual interval capture DFF count');same(launch,row['launch_DFFs'],'actual interval launch DFF count')
            same(s['capture_width']-capture,row['elided_or_merged_capture_bits'],'actual removed/merged capture bits')
            same(sum(s['input_widths'])-launch,row['elided_or_merged_launch_bits'],'actual removed/merged launch bits');raw_count+=1
    same(seen_rows,{task+'/'+sample+'/'+stage for task,sample in labels for stage in ('synth','grt')},'complete archived interval row coverage')
    native_names={r['report'] for r in index['native_reports']}
    for pair in metadata['mechanism_pairs']:
        if pair['D'] not in native_names:raise ValueError('interval mechanism report missing native recomputation')
        d=documents[pair['D']];c=documents[pair['C']]
        same([r['id'] for r in d['selection']['candidates']],[r['id'] for r in c['selection']['candidates']],'same ordered C/D candidate set')
        same([r['id'] for r in d['selection']['candidates']],['candidate/original','candidate/half','candidate/quarter'],'all three registered candidates')
        same(d['selection']['formal_D_selection'],True,'mechanism complete candidate coverage')
        same(d['selection']['candidate_PPA_calls'],0,'mechanism offline selection')
        model=next(r['model'] for r in index['native_reports'] if r['report']==pair['D'])
        if not documents[model]['id'].startswith('TEST_ONLY_'):raise ValueError('artificial interval prices must remain TEST_ONLY mechanism evidence')
    return {'interval_graphs_recomputed':len(graphs),'intervals_recomputed':len(specs),
        'interval_RTL_observations_recomputed':len(seen),'interval_untrimmed_checks_recomputed':trim_checks,
        'interval_feature_rows_recomputed':len(seen_rows),'interval_raw_rows_recomputed':raw_count,
        'interval_mechanism_platforms_recomputed':len(metadata['mechanism_pairs'])}
