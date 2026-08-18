from __future__ import annotations
from .historical import HistoricalProfilePolicy
class CascadePolicy(HistoricalProfilePolicy):
    policy_id='cascade'; version='1'
    def plan(self,request,resources,profiles):
        p=super().plan(request,resources,profiles)
        # Historical policy already returns up to four fallbacks ordered by cost-per-verified-success.
        return p
