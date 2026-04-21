from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, SYSTEM_PROMPT_BASIC

def main():
    print("=== TEST KONEKSI LLM ===")
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT_BASIC), HumanMessage(content="Halo!")]
    print("🔌 Menghubungi AI...")
    try:
        response = llm.invoke(messages)
        print(f"\n✅ AI: {response.content}")
    except Exception as e:
        print(f"❌ Gagal: {e}")