"""Joint positive body budgets on a DAG with explicit capture deadlines.

Forward arrivals and backward output requirements include fixed logic/wires.
Every mutation is checked against ALL endpoints. Parallel work is never added
together; shared vertices receive a single budget.
"""
import math


class TimingDAG:
    def __init__(self, children, endpoints, variables, *, fixed=None, groups=None):
        self.children = {i: tuple(sorted(edges)) for i, edges in children.items()}
        self.endpoints = tuple(endpoints)
        self.variables = frozenset(variables)
        self.fixed = dict(fixed or {})
        self.groups = dict(groups or {i: 0 for i in children})
        if self.variables & self.fixed.keys() or not self.variables <= self.children.keys():
            raise ValueError('overlapping or unknown owners')
        if any(n not in self.children or not math.isfinite(w) or w < 0
               for edges in self.children.values() for n, w in edges):
            raise ValueError('invalid timing edge')
        if any(e['node'] not in self.children or not math.isfinite(e['deadline_ps']) for e in endpoints):
            raise ValueError('invalid capture endpoint')
        if any(not math.isfinite(v) or v < 0 for v in self.fixed.values()):
            raise ValueError('invalid fixed cost')
        if any(self.groups[i] != self.groups[n] for i, edges in self.children.items() for n, _ in edges):
            raise ValueError('register cuts must remove cross-group timing edges')
        order, active, seen = [], set(), set()

        def visit(i):
            if i in active:
                raise ValueError('cycle in timing DAG')
            if i in seen:
                return
            active.add(i)
            for n, _ in self.children[i]:
                visit(n)
            active.remove(i); seen.add(i); order.append(i)
        for i in sorted(self.children):
            visit(i)
        self.order = order
        useful = set()

        def mark(i):
            if i in useful:
                return
            useful.add(i)
            for n, _ in self.children[i]:
                mark(n)
        for e in endpoints:
            mark(e['node'])
        if not self.variables <= useful:
            raise ValueError('priced variable without a real capture path')

    def inspect(self, budgets, *, allow_zero=False):
        if set(budgets) != self.variables:
            raise ValueError('budget owner coverage differs')
        if any(not math.isfinite(v) or (v < 0 if allow_zero else v <= 0) for v in budgets.values()):
            raise ValueError('finite positive owner budgets required')
        duration = {i: budgets.get(i, self.fixed.get(i, 0.)) for i in self.order}
        arrival = {}
        for i in self.order:
            arrival[i] = duration[i] + max((arrival[n]+w for n,w in self.children[i]), default=0.)
        required = {i: math.inf for i in self.order}
        endpoints = []
        for e in self.endpoints:
            i=e['node']; required[i]=min(required[i],e['deadline_ps'])
            endpoints.append(dict(e,arrival_ps=arrival[i],slack_ps=e['deadline_ps']-arrival[i]))
        for i in reversed(self.order):
            for n,w in self.children[i]:
                required[n]=min(required[n],required[i]-duration[i]-w)
        slack={i: required[i]-arrival[i] for i in self.variables}
        violation=max([0.]+[-e['slack_ps'] for e in endpoints])
        return dict(feasible=violation<=1e-7,violation_ps=violation,endpoints=endpoints,
                    arrivals_ps=arrival,requirements_ps={i:r for i,r in required.items() if math.isfinite(r)},
                    owner_slack_ps=slack)

    def allocate(self, weights, *, floor_ps=.001):
        if set(weights) != self.variables or any(not math.isfinite(w) or w < 0 for w in weights.values()):
            raise ValueError('reference weights differ from owners')
        budgets={i:floor_ps for i in self.variables}
        if not self.inspect(budgets)['feasible']:
            return dict(status='no_positive_joint_window',budgets_ps=budgets,check=self.inspect(budgets))
        # Independent stages scale separately; all endpoints still participate.
        for group in sorted({self.groups[i] for i in self.variables}):
            selected=sorted(i for i in self.variables if self.groups[i]==group)
            def vector(scale):
                return budgets | {i:floor_ps+scale*max(floor_ps,weights[i]) for i in selected}
            lo,hi=0.,1.
            for _ in range(48):
                if not self.inspect(vector(hi))['feasible']:
                    break
                hi*=2
            else:
                raise ValueError('unbounded budget; missing capture deadline')
            for _ in range(48):
                mid=(lo+hi)/2
                if self.inspect(vector(mid))['feasible']:lo=mid
                else:hi=mid
            budgets=vector(lo*(1-1e-10))
        # Fill slack only where all successor/capture constraints allow it.
        for i in sorted(self.variables):
            slack=self.inspect(budgets)['owner_slack_ps'][i]
            budgets[i]+=max(0.,slack)*(1-1e-10)
        return dict(status='allocated',budgets_ps=budgets,check=self.inspect(budgets))

    def paid_pairs(self):
        pairs=set()
        def upstream(i,seen):
            if i in seen:return set()
            seen=seen|{i}
            if i in self.variables:return {i}
            return set().union(*(upstream(n,seen) for n,_ in self.children[i]))
        for i in self.variables:
            for n,_ in self.children[i]:
                pairs.update((j,i) for j in upstream(n,set()))
        return sorted(pairs)

    def proposals(self, budgets, predicted_delays, *, limit=3, fraction=.125):
        """One response reweight plus actual transfers, with full path checks."""
        result=[]
        reweighted=self.allocate({i:max(.001,predicted_delays[i]) for i in self.variables})
        if reweighted['status']=='allocated':
            result.append(('response_reweight',reweighted['budgets_ps']))
        pairs=sorted(self.paid_pairs(),key=lambda p:(-max(predicted_delays[i]-budgets[i] for i in p),p))
        for a,b in pairs:
            for donor,receiver in ((a,b),(b,a)):
                proposal=dict(budgets); delta=fraction*min(budgets[donor],budgets[receiver])
                proposal[donor]-=delta;proposal[receiver]+=delta
                if self.inspect(proposal)['feasible']:
                    result.append((f'transfer:{donor}->{receiver}',proposal))
                if len(result)>=limit:return result[:limit]
        # Independent branches may also trade unused per-node slack against
        # response pressure. Tightening never violates a budget-path deadline.
        for i in sorted(self.variables,key=lambda n:(-(predicted_delays[n]-budgets[n]),n)):
            proposal=dict(budgets);proposal[i]*=1-fraction
            result.append((f'tighten:{i}',proposal))
            if len(result)>=limit:break
        return result[:limit]
