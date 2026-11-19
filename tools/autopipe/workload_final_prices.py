"""Frozen v10 runtime functions; extracted without numerical edits from workload_final_prices.py."""
import math

from unittest.mock import patch

from . import workload_diagnostic as diagnostic

class CachedPrices(diagnostic.DiagnosticPrices):
    def __init__(self,bundle):
        super().__init__(bundle)
        self.cover_function=diagnostic.operator_cover_features
        self.cover_cache={};self.cover_hits=0

    def cached_cover(self,spec,f):
        key=diagnostic.key(spec)
        if key not in self.cover_cache:
            before=set(f);cov,work=self.cover_function(spec,f)
            added={n:f[n] for n in set(f)-before if n not in ('cover_pressure_response','cover_T_response',
                'fanout_repair_pressure','cone_cut_pressure')}
            self.cover_cache[key]=(cov,work,added)
            return cov,work
        self.cover_hits+=1;cov,work,added=self.cover_cache[key];f.update(added)
        f.update(cover_pressure_response=math.log2(1+cov['cells']/64)*f['clock_pressure'],
                 cover_T_response=math.log2(1+cov['cells']/64)*f['log2_target'],
                 fanout_repair_pressure=f['fanout_internal_log2_repair_excess']*f['clock_pressure'],
                 cone_cut_pressure=f['cone_log2_peak_cut']*f['clock_pressure'])
        return cov,work

    def operator_price(self,q):
        with patch.object(diagnostic,'operator_cover_features',self.cached_cover):
            return super().operator_price(q)
