"""Read-only 300s endpoint reporting; retain the original 120s timeout.

No synthesis/place/CTS/route operation is repeated or extended. Model parameters
and source roles remain frozen. The named extension is recorded externally.
"""
import inspect
from . import nangate45_pipeline_collect as collect
from . import nangate45_pipeline_readout as original
from . import nangate45_pipeline_alias_partial as aliases
from .nangate45_samples import read, sha


class ReportLedger(collect.PipelineLedger):
    def reserve(self, stage, timeout_s, threads, purpose, command, output, *, context=None):
        if stage is not None or timeout_s<=120:
            return super().reserve(stage,timeout_s,threads,purpose,command,output,context=context)
        a = collect.campaign.verify(self.root)
        extension = read(self.root/'report-timeout-amendment.json')
        if threads!=2 or timeout_s!=300 or str(output).split('/')[-1]!='readout-v5':
            raise ValueError('N56 timeout extension is report-only')
        for path,expected in extension['implementation'].items():
            if sha(path)!=expected:
                raise ValueError('N56 report resource successor drift')
        entries = [e for e in read(self.path)['entries'] if e.get('admission_id')==a['id']]
        if sum(e['stage'] is None for e in entries)>=a['call_caps']['support']:
            raise ValueError('N56 report batch support cap')
        if sum(e['stage'] is None and e.get('task_id')==self.task['id'] for e in entries)>=12:
            raise ValueError('N56 report task support cap')
        return collect.runtime.NineLedger.reserve(self,None,300,2,purpose,command,output,context={
            **(context or {}), 'target_platform':'nangate45', 'admission_id':a['id'], 'task_id':self.task['id'],
            'admission_sha256':sha(self.root/'report-timeout-amendment.json'),
            'model_version':'N56-report-only-resource-successor-v2'})


def report(out, source, task, pins, execute, base):
    text = inspect.getsource(original.report).replace('readout-v3', 'readout-v5')
    namespace = dict(original.report.__globals__)
    exec(compile(text,__file__,'exec'),namespace)
    def longer(command, name, *args, **kwargs):
        if name=='readout-v5':
            kwargs['timeout'] = 300
        return execute(command,name,*args,**kwargs)
    return namespace['report'](out,source,task,pins,longer,base)


def complete_saved(root, task):
    text = inspect.getsource(original.complete_saved)
    text = text.replace('collect.PipelineLedger(root,recovery)', 'ReportLedger(root,recovery)')
    text = text.replace("task['id']+'-readout-v3'", "task['id']+'-readout-v5-timeout300-v2'")
    namespace = dict(original.complete_saved.__globals__, ReportLedger=ReportLedger, report=report)
    exec(compile(text,__file__,'exec'),namespace)
    return namespace['complete_saved'](root,task)


def point(root, task):
    namespace = dict(collect.point.__globals__, PipelineLedger=ReportLedger, report=report, mapped_state=aliases.verify)
    exec(compile(inspect.getsource(collect.point),__file__,'exec'),namespace)
    return namespace['point'](root,task)
