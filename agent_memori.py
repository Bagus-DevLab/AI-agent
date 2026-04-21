import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Konfigurasi Awal
os.environ["no_proxy"] = "*"
MEMORY_FILE = "memory.json"

# Inisialisasi LLM (Tetap pake config enowxai lu)
llm = ChatOpenAI(
    api_key="enx-0ffdb0f80efd7d1b8972e84e7037900b4f64b33c0631ea07ed1821db9b7549d2", 
    base_url="http://172.20.32.1:1430/v1", 
    model="claude-opus-4.6", 
    temperature=0.7
)

def load_memori_dari_file():
    """Fungsi untuk mengambil history dari file JSON"""
    if not os.path.exists(MEMORY_FILE):
        # Kalau file belum ada, kasih instruksi dasar
        return [SystemMessage(content="Kamu adalah asisten handal yang selalu ingat nama user.")]
    
    with open(MEMORY_FILE, "r") as f:
        data = json.load(f)
        
    history = [SystemMessage(content="Kamu adalah asisten handal yang selalu ingat nama user.")]
    for item in data:
        if item["role"] == "user":
            history.append(HumanMessage(content=item["content"]))
        elif item["role"] == "ai":
            history.append(AIMessage(content=item["content"]))
    return history

def simpan_memori_ke_file(history):
    """Fungsi untuk menyimpan history ke file JSON"""
    serializable_history = []
    for msg in history:
        if isinstance(msg, HumanMessage):
            serializable_history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            serializable_history.append({"role": "ai", "content": msg.content})
            
    with open(MEMORY_FILE, "w") as f:
        json.dump(serializable_history, f, indent=4)

# --- MAIN PROGRAM ---
print("=== AI DENGAN MEMORI PERMANEN ===")
print("Ketik 'exit' untuk keluar.\n")

# 1. Load history yang lama (kalau ada)
chat_history = load_memori_dari_file()

# Cek apakah sudah ada percakapan sebelumnya
if len(chat_history) > 1:
    print(f"--- [INFO] Melanjutkan obrolan terakhir (ada {len(chat_history)-1} pesan tersimpan) ---")

while True:
    user_input = input("Lu: ")
    if user_input.lower() == 'exit':
        print("Bye!")
        break
    
    # 2. Tambah ke history & Kirim ke AI
    chat_history.append(HumanMessage(content=user_input))
    
    print("AI sedang berpikir...")
    try:
        response = llm.invoke(chat_history)
        
        # 3. Simpan jawaban AI ke history
        chat_history.append(AIMessage(content=response.content))
        
        # 4. Tulis ke file biar permanen
        simpan_memori_ke_file(chat_history)
        
        print(f"\nAI: {response.content}\n")
    except Exception as e:
        print(f"Error: {e}")