import os
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def load_memori_lokal(system_prompt, path="chat_memory.json"):
    history = [SystemMessage(content=system_prompt)]
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                for item in data:
                    if item['role'] == 'user': history.append(HumanMessage(content=item['content']))
                    else: history.append(AIMessage(content=item['content']))
        except: pass
    return history

def simpan_memori_lokal(history, path="chat_memory.json"):
    data = [{"role": "user" if isinstance(m, HumanMessage) else "ai", "content": m.content} 
            for m in history if not isinstance(m, SystemMessage)]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)