"""Higher memory/time caps require the exact named step6 admission."""
from pathlib import Path
from types import SimpleNamespace
import json,tempfile,unittest
from experiments.arithmetic_dse.bounded_recheck import limits,sha
from experiments.arithmetic_dse.budget import POLICY

class BoundedRecheck(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'admission.json'
        self.a={'id':'correction','purpose':'arithmetic_capacity_recheck_only','policy_sha256':sha(POLICY),
                'memory_limit_MiB':32768,'threads':2,'synthesis_timeout_s':900,'post_synthesis_through_grt_timeout_s':3600,'automatic_retries':0,
                'call_caps':{'synth':6,'grt':2,'final':0},'tasks':[{'id':str(i),'stage':'grt' if i in (0,3) else 'synth','kernel':'udr_unsigned_128' if i<3 else 'fp32_serial'} for i in range(6)]}
        self.args=SimpleNamespace(admission=self.path,admission_id='correction',task_id='0',stage='grt',resume_synth_from=None,platform='asap7',threads=2,memory_limit_mib=32768,synth_timeout_s=900,route_timeout_s=3600)
    def save(self):self.path.write_text(json.dumps(self.a))
    def test_exact_task(self):self.save();self.assertEqual(limits(self.args)[1]['id'],'0')
    def test_no_implicit_or_global_resource_increase(self):
        for key,value in [('memory_limit_mib',65536),('threads',4),('stage','final'),('synth_timeout_s',1800),('route_timeout_s',7200),('task_id','unknown'),('admission',None),('resume_synth_from',Path('/tmp'))]:
            self.save();prior=getattr(self.args,key);setattr(self.args,key,value)
            with self.subTest(key=key),self.assertRaises(ValueError):limits(self.args)
            setattr(self.args,key,prior)
    def test_list_identity_and_caps(self):
        self.a['call_caps']['grt']=3;self.save()
        with self.assertRaises(ValueError):limits(self.args)
        self.a['call_caps']['grt']=2;self.a['tasks']*=2;self.save()
        with self.assertRaises(ValueError):limits(self.args)

    def test_thread_correction_has_only_three_UDR_tasks(self):
        self.a.update(correction_kind='yosys_thread_limit',yosys_max_threads=2,synthesis_timeout_s=1800,call_caps={'synth':3,'grt':1,'final':0})
        self.a['tasks']=self.a['tasks'][:3];self.args.synth_timeout_s=1800;self.save()
        self.assertEqual(limits(self.args)[1]['kernel'],'udr_unsigned_128')
        self.a['yosys_max_threads']=24;self.save()
        with self.assertRaises(ValueError):limits(self.args)

    def test_explicit_completion_envelope_requires_exact_scope(self):
        self.a.update(correction_kind='yosys_thread_limit',execution_mode='complete_initial_backend',yosys_max_threads=2,synthesis_timeout_s=7200,post_synthesis_through_grt_timeout_s=14400,call_caps={'synth':3,'grt':1,'final':0})
        self.a['tasks']=self.a['tasks'][:3];self.args.synth_timeout_s=7200;self.args.route_timeout_s=14400;self.save()
        self.assertEqual(limits(self.args)[1]['kernel'],'udr_unsigned_128')
        self.args.route_timeout_s=28800
        with self.assertRaises(ValueError):limits(self.args)

if __name__=='__main__':unittest.main()
