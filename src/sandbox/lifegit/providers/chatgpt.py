from __future__ import annotations

from pathlib import Path
from typing import Any

from sandbox.lifegit.models import NormalizedConversation, NormalizedMessage
from sandbox.lifegit.providers.base import Provider
from sandbox.lifegit.util import flatten_text, iso_time, read_json_or_zip, sha256_bytes, stable_id


class ChatGPTProvider(Provider):
    name="chatgpt"

    def parse(self, path: Path) -> tuple[list[NormalizedConversation], str, str]:
        data, raw, member = read_json_or_zip(path, ("conversations.json",))
        if isinstance(data, dict) and isinstance(data.get("conversations"), list):
            data=data["conversations"]
        if not isinstance(data, list):
            raise ValueError("ChatGPT conversations export must be a list")
        out=[]
        for conv in data:
            if not isinstance(conv, dict):
                continue
            cid=str(conv.get("id") or conv.get("conversation_id") or stable_id("conv","chatgpt",conv.get("title"),conv.get("create_time")))
            mapping=conv.get("mapping") if isinstance(conv.get("mapping"), dict) else None
            current_node=conv.get("current_node")
            current_path=set()
            if mapping and current_node in mapping:
                node=current_node
                guard=0
                while node and node in mapping and guard < len(mapping)+2:
                    current_path.add(node)
                    node=mapping[node].get("parent")
                    guard += 1
            msgs=[]
            if mapping:
                for node_id,node in mapping.items():
                    msg=node.get("message") if isinstance(node,dict) else None
                    if not isinstance(msg,dict):
                        continue
                    author=msg.get("author") or {}
                    role=str(author.get("role") or "unknown")
                    text=flatten_text(msg.get("content"))
                    if not text.strip() and role not in {"user","assistant"}:
                        continue
                    metadata=msg.get("metadata") or {}
                    mid=str(msg.get("id") or node_id)
                    msgs.append(NormalizedMessage(
                        provider="chatgpt", conversation_id=cid, message_id=mid,
                        parent_message_id=node.get("parent"), role=role, text=text,
                        created_at=iso_time(msg.get("create_time") or node.get("create_time")),
                        model=metadata.get("model_slug") or metadata.get("default_model_slug"),
                        is_current_path=(not current_path or node_id in current_path),
                        metadata={"node_id":node_id,"content_type":(msg.get("content") or {}).get("content_type") if isinstance(msg.get("content"),dict) else None},
                    ))
            else:
                flat=conv.get("messages") or []
                for i,msg in enumerate(flat):
                    if not isinstance(msg,dict):
                        continue
                    author=msg.get("author") or {}
                    role=str(author.get("role") or msg.get("role") or "unknown")
                    mid=str(msg.get("id") or stable_id("msg",cid,i))
                    msgs.append(NormalizedMessage(
                        provider="chatgpt",conversation_id=cid,message_id=mid,
                        parent_message_id=msg.get("parent"),role=role,text=flatten_text(msg.get("content") or msg.get("text")),
                        created_at=iso_time(msg.get("create_time") or msg.get("created_at")),
                        model=(msg.get("metadata") or {}).get("model_slug"),is_current_path=True,
                    ))
            msgs.sort(key=lambda m: (m.created_at or "", m.message_id))
            out.append(NormalizedConversation(
                provider="chatgpt",conversation_id=cid,title=str(conv.get("title") or "Untitled"),
                created_at=iso_time(conv.get("create_time")),updated_at=iso_time(conv.get("update_time")),
                messages=tuple(msgs),metadata={"current_node":current_node,"conversation_template_id":conv.get("conversation_template_id")},
            ))
        return out, sha256_bytes(raw), member
