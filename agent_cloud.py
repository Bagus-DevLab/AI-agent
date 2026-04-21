import json
import os
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 1. Bersihkan ENV Proxy sebelum load dotenv
if "http_proxy" in os.environ: del os.environ["http_proxy"]
if "https_proxy" in os.environ: del os.environ["https_proxy"]
if "HTTP_PROXY" in os.environ: del os.environ["HTTP_PROXY"]
if "HTTPS_PROXY" in os.environ: del os.environ["HTTPS_PROXY"]

load_dotenv()

# 2. Setup Koneksi ke Cloudflare R2 dengan HTTP biasa (Bypass SSL sementara)
# Karena ini cuma nyimpen chat history lu, HTTP biasa aman buat testing.
endpoint_http = os.getenv("R2_ENDPOINT").replace("https://", "http://")

s3 = boto3.client(
    's3',
    endpoint_url=endpoint_http, # Pakai HTTP biasa
    aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
    region_name='auto',
    config=Config(signature_version='s3v4')
)

BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
FILE_NAME_DI_CLOUD = "memori_bagus.json"
FILE_NAME_DI_LOKAL = "temp_memori.json"

# 3. Setup LLM
llm = ChatOpenAI(
    api_key=os.getenv("ENOWXAI_KEY"), 
    base_url=os.getenv("ENOWXAI_URL"), 
    model="claude-opus-4.6", 
    temperature=0.7
)

def load_memori_dari_cloud():
    print("☁️ Mengecek memori di Cloudflare R2...")
    try:
        s3.download_file(BUCKET_NAME, FILE_NAME_DI_CLOUD, FILE_NAME_DI_LOKAL)
        with open(FILE_NAME_DI_LOKAL, "r") as f:
            data = json.load(f)
            
        history = [SystemMessage(content="Kamu adalah asisten asik yang selalu ingat nama user.")]
        for item in data:
            if item["role"] == "user":
                history.append(HumanMessage(content=item["content"]))
            elif item["role"] == "ai":
                history.append(AIMessage(content=item["content"]))
        print("✅ Memori berhasil di-load dari Cloud!")
        return history
    except ClientError as e:
        print("ℹ️ Belum ada memori di Cloud, memulai lembaran baru.")
        return [SystemMessage(content="Kamu adalah asisten asik yang selalu ingat nama user.")]

def simpan_memori_ke_cloud(history):
    serializable_history = []
    for msg in history:
        if isinstance(msg, HumanMessage):
            serializable_history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            serializable_history.append({"role": "ai", "content": msg.content})
            
    with open(FILE_NAME_DI_LOKAL, "w") as f:
        json.dump(serializable_history, f, indent=4)
        
    print("\n☁️ Sedang membackup obrolan ke R2...")
    s3.upload_file(FILE_NAME_DI_LOKAL, BUCKET_NAME, FILE_NAME_DI_CLOUD)
    print("✅ Backup Cloud Selesai!")

# --- MAIN PROGRAM ---
print("=== AI DENGAN CLOUD MEMORY (R2) ===")
print("Ketik 'exit' untuk keluar.\n")

chat_history = load_memori_dari_cloud()

while True:
    user_input = input("\nLu: ")
    if user_input.lower() == 'exit':
        break
    
    chat_history.append(HumanMessage(content=user_input))
    
    print("AI sedang berpikir...")
    try:
        response = llm.invoke(chat_history)
        chat_history.append(AIMessage(content=response.content))
        
        print(f"\nAI: {response.content}")
        simpan_memori_ke_cloud(chat_history)
        
    except Exception as e:
        print(f"Error: {e}")