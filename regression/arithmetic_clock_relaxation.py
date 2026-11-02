"""A relaxed capacity clock is a separate frozen diagnostic condition."""
from pathlib import Path
from types import SimpleNamespace
import json,tempfile,unittest
from experiments.arithmetic_dse.clock_relaxation import task,sha
from experiments.arithmetic_dse.budget import POLICY

class ClockRelaxation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'admission.json'
        self.a={'id':'relax','purpose':'arithmetic_clock_relaxation_only','policy_sha256':sha(POLICY),
                'call_caps':{'synth':1,'grt':1,'final':0},'automatic_retries':0,'threads':2,'memory_limit_MiB':32768,
                'synthesis_timeout_s':300,'post_synthesis_through_grt_timeout_s':14400,
                'support_envelope':{'walltime_s':1800,'CPU_time_s':3600},
                'worst_case_walltime_s':16500,'CPU_envelope_s':33000,
                'tasks':[{'id':'UDR','source_run':self.tmp.name}]}
        self.args=SimpleNamespace(admission=self.path,admission_id='relax',task_id='UDR',platform='asap7',stage='grt',period_ps=100000,abc_target_ps=1500,io_delay_max_ps=300,top='Step6UDR128',threads=2,memory_limit_mib=32768,synth_timeout_s=300,route_timeout_s=14400,resume_synth_from=Path(self.tmp.name))
    def save(self):self.path.write_text(json.dumps(self.a))
    def test_exact_separate_clock_axis(self):self.save();self.assertEqual(task(self.args)[1]['id'],'UDR')
    def test_changed_mapping_IO_final_and_resource_requests_rejected(self):
        for key,value in [('abc_target_ps',100000),('io_delay_max_ps',20000),('stage','final'),('period_ps',1500),('period_ps',200000),('memory_limit_mib',65536),('resume_synth_from',None),('task_id','other')]:
            self.save();prior=getattr(self.args,key);setattr(self.args,key,value)
            with self.subTest(key=key),self.assertRaises(ValueError):task(self.args)
            setattr(self.args,key,prior)
    def test_no_extra_task_or_call(self):
        self.a['call_caps']['synth']=2;self.save()
        with self.assertRaises(ValueError):task(self.args)
        self.a['call_caps']['synth']=1;self.a['tasks']*=2;self.save()
        with self.assertRaises(ValueError):task(self.args)
    def test_underfunded_resource_declarations_rejected(self):
        for key,value in [('worst_case_walltime_s',14700),('CPU_envelope_s',29400),('support_envelope',{'walltime_s':0,'CPU_time_s':0})]:
            prior=self.a[key];self.a[key]=value;self.save()
            with self.subTest(key=key),self.assertRaises(ValueError):task(self.args)
            self.a[key]=prior

if __name__=='__main__':unittest.main()
