"""
agents/cloud.py — Cloud Memory via R2.
"""
import json
import os
import boto3
from config import get_llm, R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET_NAME
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def main():
    print("=== AI CLOUD MEMORY (R2) ===")
    llm = get_llm()
    
    # Setup S3 Client
    s3 = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY
    )
    
    FILE_LOKAL = "temp_cloud.json"
    FILE_REMOTE = "chat_history.json"
    
    chat_history = [SystemMessage(content="Kamu adalah AI asik dengan cloud memory.")]
    
    print("☁️ Mengambil memori dari cloud...")
    try:
        s3.download_file(R2_BUCKET_NAME, FILE_REMOTE, FILE_LOKAL)
        with open(FILE_LOKAL, "r") as f:
            data = json.load(f)
            for item in data:
                if item['role'] == 'user': chat_history.append(HumanMessage(content=item['content']))
                else: chat_history.append(AIMessage(content=item['content']))
        print("✅ Memori sinkron.")
    except:
        print("ℹ️ Memulai obrolan baru.")

    while True:
        user_input = input("\nLu: ").strip()
        if user_input.lower() == 'exit': break
        
        chat_history.append(HumanMessage(content=user_input))
        try:
            response = llm.invoke(chat_history)
            print(f"\nAI: {response.content}")
            chat_history.append(AIMessage(content=response.content))
            
            # Save & Upload
            serializable = [{"role": "user" if isinstance(m, HumanMessage) else "ai", "content": m.content} 
                            for m in chat_history if not isinstance(m, SystemMessage)]
            with open(FILE_LOKAL, "w") as f:
                json.dump(serializable, f)
            s3.upload_file(FILE_LOKAL, R2_BUCKET_NAME, FILE_REMOTE)
            print("☁️ Backup Cloud sukses.")
        except Exception as e:
            print(f"❌ Error: {e}")