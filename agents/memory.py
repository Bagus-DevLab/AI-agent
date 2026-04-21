from langchain_core.messages import HumanMessage, AIMessage
from config import get_llm, SYSTEM_PROMPT_MEMORY
from utils.memory import load_memori_lokal, simpan_memori_lokal

def main():
    print("=== AI DENGAN MEMORI LOKAL ===")
    llm = get_llm()
    chat_history = load_memori_lokal(SYSTEM_PROMPT_MEMORY)
    
    print("Ketik 'exit' untuk keluar.")
    while True:
        user_input = input("\nLu: ").strip()
        if user_input.lower() == 'exit': break
        
        chat_history.append(HumanMessage(content=user_input))
        try:
            response = llm.invoke(chat_history)
            print(f"\nAI: {response.content}")
            chat_history.append(AIMessage(content=response.content))
            simpan_memori_lokal(chat_history)
        except Exception as e:
            print(f"❌ Error: {e}")