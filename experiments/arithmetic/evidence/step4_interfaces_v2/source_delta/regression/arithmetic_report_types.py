"""Key-field types must be checked before costs reach a downstream selector."""
from copy import deepcopy
import gzip,json,os,unittest
from pathlib import Path
from experiments.arithmetic_dse.report_types import validate_report_types
ROOT=Path(__file__).resolve().parents[1]

class ReportTypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(os.environ.get('ARITHMETIC_REPORT_TYPES_FIXTURE',str(ROOT/'experiments/arithmetic/evidence/step4_interfaces_v2/reports/asap7.json.gz')))
        cls.report=json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
        cls.schemas=json.loads((ROOT/'experiments/arithmetic_dse/configs/arithmetic_compiler_interfaces_v1.json').read_text())['report_schemas']
    def check(self,r):validate_report_types(r,self.schemas)
    def test_real_generated_report(self):
        self.check(self.report);self.assertIs(type(self.report['pipeline']['register_bits']),int)
    def test_uint64_range(self):
        for bits in (0,128,2**53+1,2**63,2**64-1):
            with self.subTest(bits=bits):
                r=deepcopy(self.report);r['pipeline']['register_bits']=bits;self.check(r)
    def test_counter_wrong_tokens_and_range(self):
        for name in ('register_bits','register_count'):
            for value in ('128',128.0,True,False,None,-1,2**64):
                with self.subTest(field=name,value=value):
                    r=deepcopy(self.report);r['pipeline'][name]=value
                    with self.assertRaisesRegex(ValueError,'pipeline.'+name):self.check(r)
    def test_other_critical_fields(self):
        for path,value in [(('request','L'),'3'),(('request','II'),True),(('request','target_period_ps'),float('nan')),(('pipeline','final_delay'),float('inf')),(('protocol','reset_enabled'),'true'),(('protocol','register_stages'),2.0)]:
            with self.subTest(path=path):
                r=deepcopy(self.report);r[path[0]][path[1]]=value
                with self.assertRaises(ValueError):self.check(r)
        r=deepcopy(self.report);r['stages'][0]=False
        with self.assertRaisesRegex(ValueError,'stages'):self.check(r)
    def test_missing_and_old_format(self):
        r=deepcopy(self.report);del r['pipeline']['register_bits']
        with self.assertRaisesRegex(ValueError,'register_bits missing'):self.check(r)
        r=deepcopy(self.report);r['version']='arithmetic-structure-report-v1'
        with self.assertRaisesRegex(ValueError,'version const'):self.check(r)
    def test_failed_report(self):
        r={'version':'arithmetic-structure-report-v2','status':'failed','failure_stage':'cost','failure_code':'cost_uncovered','failure_reason':'inference unavailable','region_id':'','node_id':''}
        self.check(r);r['failure_code']=0
        with self.assertRaisesRegex(ValueError,'failure_code'):self.check(r)
    def test_unknown_schema_cannot_be_silently_ignored(self):
        schemas=deepcopy(self.schemas);schemas['passed']['mystery_keyword']=True
        with self.assertRaisesRegex(ValueError,'unsupported report schema'):validate_report_types(self.report,schemas)

if __name__=='__main__':unittest.main()
