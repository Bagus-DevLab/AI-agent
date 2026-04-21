from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os

# Memastikan tidak ada gangguan proxy sistem
os.environ["no_proxy"] = "*" 

# Inisialisasi LLM
llm = ChatOpenAI(
    # API Key dari enowxai
    api_key="enx-0ffdb0f80efd7d1b8972e84e7037900b4f64b33c0631ea07ed1821db9b7549d2", 
    
    # Base URL mengarah ke proxy di Windows
    # Catatan: Coba hapus '/v1' jika nanti error 404, 
    # tapi standarnya OpenAI pakai '/v1'
    base_url="http://172.20.32.1:1430/v1", 
    
    # Sesuaikan dengan model yang muncul di dashboard enowxai
    model="claude-opus-4.6", 
    
    temperature=0.7,
    # Tambahkan timeout agar tidak stuck selamanya jika koneksi lambat
    timeout=60 
)

messages = [
    SystemMessage(content="You are a helpful coding assistant."),
    HumanMessage(content="Halo, jika kamu bisa mendengar saya, balas dengan kata 'GASKEN'!")
]

try:
    print("AI sedang berpikir (menghubungi enowxai di Windows)...")
    # invoke adalah cara standar LangChain terbaru untuk memanggil model
    response = llm.invoke(messages)
    
    print("\n=== RESPON AI ===")
    print(response.content)

except Exception as e:
    print(f"\n[ERROR] Waduh, ada masalah: \n{e}")