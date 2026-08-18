from __future__ import annotations

from pathlib import Path

from lifegit.models import NormalizedConversation, NormalizedMessage
from lifegit.providers.base import Provider
from lifegit.util import flatten_text, iso_time, read_json_or_zip, sha256_bytes, stable_id


class ClaudeProvider(Provider):
    name="claude"

    def parse(self, path: Path) -> tuple[list[NormalizedConversation], str, str]:
        data, raw, member = read_json_or_zip(path, ("conversations.json","claude_conversations.json"))
        if isinstance(data, dict):
            data=data.get("conversations") or data.get("data") or []
        if not isinstance(data,list):
            raise ValueError("Claude conversations export must be a list")
        out=[]
        for conv in data:
            if not isinstance(conv,dict):
                continue
            cid=str(conv.get("uuid") or conv.get("id") or stable_id("conv","claude",conv.get("name"),conv.get("created_at")))
            raw_msgs=conv.get("chat_messages") or conv.get("messages") or []
            msgs=[]
            prev=None
            for i,msg in enumerate(raw_msgs):
                if not isinstance(msg,dict):
                    continue
                sender=str(msg.get("sender") or msg.get("role") or "unknown").lower()
                role="user" if sender in {"human","user"} else ("assistant" if sender in {"assistant","claude"} else sender)
                mid=str(msg.get("uuid") or msg.get("id") or stable_id("msg",cid,i))
                text=flatten_text(msg.get("content") if "content" in msg else msg.get("text"))
                if not text and isinstance(msg.get("text"),str):
                    text=msg["text"]
                msgs.append(NormalizedMessage(
                    provider="claude",conversation_id=cid,message_id=mid,parent_message_id=msg.get("parent_uuid") or prev,
                    role=role,text=text,created_at=iso_time(msg.get("created_at") or msg.get("create_time")),
                    model=msg.get("model"),is_current_path=True,metadata={"attachments":len(msg.get("attachments") or [])},
                ))
                prev=mid
            out.append(NormalizedConversation(
                provider="claude",conversation_id=cid,title=str(conv.get("name") or conv.get("title") or "Untitled"),
                created_at=iso_time(conv.get("created_at")),updated_at=iso_time(conv.get("updated_at")),messages=tuple(msgs),
            ))
        return out, sha256_bytes(raw), member
