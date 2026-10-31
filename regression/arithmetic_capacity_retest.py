"""Task-scoped limits/checkpoint validation without EDA."""
from pathlib import Path
from types import SimpleNamespace
import json,tempfile,unittest
from experiments.arithmetic_dse.capacity_retest import task,digest
from experiments.arithmetic_dse.budget import POLICY
class RetestContract(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)/'admission.json'
  self.f={'id':'retest','purpose':'mul_capacity_retest_only','policy_sha256':digest(POLICY),'tasks':[{'id':'named','resume_directory':self.temp.name,'grt_walltime_limit_s':3600,'grt_CPU_limit_s':7200,'threads':2,'memory_limit_MiB':8192}],'call_caps':{'synth':0,'grt':1,'final':0}}
  self.args=SimpleNamespace(admission=self.path,admission_id='retest',task_id='named',stage='grt',resume_synth_from=Path(self.temp.name),route_timeout_s=3600,threads=2,memory_limit_mib=8192)
 def write(self):self.path.write_text(json.dumps(self.f))
 def test_exact_named_scope(self):self.write();self.assertEqual(task(self.args)[1]['id'],'named')
 def test_no_final_other_task_or_old_CPU_cap(self):
  for field,value in [('stage','final'),('task_id','other'),('route_timeout_s',1200),('threads',4),('memory_limit_mib',16384),('resume_synth_from',None)]:
   self.write();previous=getattr(self.args,field);setattr(self.args,field,value)
   with self.assertRaises(ValueError):task(self.args)
   setattr(self.args,field,previous)
  self.f['tasks'][0]['grt_CPU_limit_s']=2400;self.write()
  with self.assertRaises(ValueError):task(self.args)
 def test_no_extra_synth_or_second_task(self):
  self.f['call_caps']['synth']=1;self.write()
  with self.assertRaises(ValueError):task(self.args)
  self.f['call_caps']['synth']=0;self.f['tasks']*=2;self.write()
  with self.assertRaises(ValueError):task(self.args)
if __name__=='__main__':unittest.main()
