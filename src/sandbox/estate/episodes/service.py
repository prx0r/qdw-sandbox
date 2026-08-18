from __future__ import annotations
import uuid
from datetime import UTC,datetime
from ..contracts import ExecutionEpisodeRecord,EpisodeStatus
class EpisodeService:
    def __init__(self,store): self.store=store
    def create(self,graph_id,node_id,attempt,request_id,route_decision_id,resource_id,executor_config_hash=None,context_pack_id=None):
        e=ExecutionEpisodeRecord('ep_'+uuid.uuid4().hex[:16],graph_id,node_id,attempt,request_id,route_decision_id,resource_id,executor_config_hash,context_pack_id)
        self.store.create_episode(e); return e
    def start(self,episode_id,sandbox_id): self.store.transition_episode(episode_id,{'CREATED'},EpisodeStatus.RUNNING,sandbox_id=sandbox_id,started_at=datetime.now(UTC).isoformat())
    def submit(self,episode_id,output_hash,wall_ms,**costs): self.store.transition_episode(episode_id,{'RUNNING'},EpisodeStatus.SUBMITTED,output_hash=output_hash,wall_ms=wall_ms,finished_at=datetime.now(UTC).isoformat(),**costs)
    def fail(self,episode_id,failure_class): self.store.transition_episode(episode_id,{'RUNNING','SUBMITTED','VERIFYING'},EpisodeStatus.FAILED,failure_class=failure_class,finished_at=datetime.now(UTC).isoformat())
