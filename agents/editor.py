"""
agents/editor.py — Agent dengan kemampuan membaca, menulis, dan mengelola file.
Mendukung operasi otomatis via tag [SAVE], [DELETE], dan [MOVE] dengan konfirmasi user.
"""

import os
import sys
import re
import shutil
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import get_llm, SYSTEM_PROMPT_EDITOR
from utils.scanner import scan_workspace

def execute_file_operations(ai_response):
    """
    Mencari dan mengeksekusi perintah manipulasi file dari jawaban AI dengan konfirmasi manual.
    Format yang didukung: [SAVE: path], [DELETE: path], [MOVE: old -> new]
    """
    changes_made = []

    # 1. Logika SAVE (Simpan/Update File)
    # Mencari pola: [SAVE: path/file.py] ```code```
    save_pattern = r"\[SAVE:\s*(.+?)\]\s*```[a-zA-Z]*\n(.*?)```"
    save_matches = re.findall(save_pattern, ai_response, re.DOTALL)
    
    for filepath, content in save_matches:
        filepath = filepath.strip()
        konfirmasi = input(f"\n💾 Simpan perubahan ke '{filepath}'? (y/n): ").strip().lower()
        
        if konfirmasi == 'y':
            try:
                # Buat folder jika belum ada
                os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"✅ Berhasil mengupdate {filepath}")
                changes_made.append(f"SAVE: {filepath}")
            except Exception as e:
                print(f"❌ Gagal menyimpan {filepath}: {e}")
        else:
            print(f"⏭️  Perubahan pada {filepath} dibatalkan.")

    # 2. Logika DELETE (Hapus File)
    delete_pattern = r"\[DELETE:\s*(.+?)\]"
    delete_matches = re.findall(delete_pattern, ai_response)
    for filepath in delete_matches:
        filepath = filepath.strip()
        konfirmasi = input(f"\n🗑️  Hapus file '{filepath}' secara permanen? (y/n): ").strip().lower()
        
        if konfirmasi == 'y':
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"✅ Berhasil menghapus {filepath}")
                    changes_made.append(f"DELETE: {filepath}")
                else:
                    print(f"⚠️  File tidak ditemukan: {filepath}")
            except Exception as e:
                print(f"❌ Gagal menghapus {filepath}: {e}")
        else:
            print(f"⏭️  Penghapusan {filepath} dibatalkan.")

    # 3. Logika MOVE (Pindah/Rename File)
    move_pattern = r"\[MOVE:\s*(.+?)\s*->\s*(.+?)\]"
    move_matches = re.findall(move_pattern, ai_response)
    for old_path, new_path in move_matches:
        old_path, new_path = old_path.strip(), new_path.strip()
        konfirmasi = input(f"\n🚚 Pindahkan '{old_path}' -> '{new_path}'? (y/n): ").strip().lower()
        
        if konfirmasi == 'y':
            try:
                if os.path.exists(old_path):
                    os.makedirs(os.path.dirname(new_path), exist_ok=True) if os.path.dirname(new_path) else None
                    shutil.move(old_path, new_path)
                    print(f"✅ Berhasil memindahkan ke {new_path}")
                    changes_made.append(f"MOVE: {old_path} -> {new_path}")
                else:
                    print(f"⚠️  Sumber tidak ditemukan: {old_path}")
            except Exception as e:
                print(f"❌ Gagal memindahkan {old_path}: {e}")
        else:
            print(f"⏭️  Pemindahan {old_path} dibatalkan.")

    return changes_made

def main():
    print("=== 🛠️ AI FILE EDITOR (READ & WRITE) READY! ===")
    
    # Ambil folder target dari argumen atau default ke folder saat ini
    folder_path = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"📂 Workspace: {folder_path}")

    llm = get_llm(temperature=0.2)
    
    # 1. SCAN SELURUH ISI KODE (Agar AI bisa 'Membaca')
    print("📥 Membaca seluruh isi kodingan...")
    docs, count = scan_workspace(folder_path)
    
    # Gabungkan semua kode ke dalam satu string konteks
    context_code = ""
    for d in docs:
        context_code += f"\n--- FILE: {d['path']} ---\n{d['content']}\n"

    # Inisialisasi percakapan dengan System Prompt + Konteks Kode
    messages = [
        SystemMessage(content=SYSTEM_PROMPT_EDITOR + "\n\nBERIKUT ADALAH ISI KODE SAAT INI:\n" + context_code)
    ]

    print(f"✅ {count} file berhasil dimuat ke memori AI.")
    print("Ketik 'exit' untuk keluar.\n")

    while True:
        user_input = input("Lu: ").strip()
        if user_input.lower() == "exit":
            print("Bye! 👋")
            break
        if not user_input:
            continue

        messages.append(HumanMessage(content=user_input))

        print("AI sedang menganalisis dan bekerja...")
        try:
            response = llm.invoke(messages)
            ai_text = response.content
            print(f"\nAI:\n{ai_text}\n")

            # 2. EKSEKUSI PERUBAHAN (Agar AI bisa 'Menulis/Mengubah')
            ops = execute_file_operations(ai_text)
            if ops:
                print(f"\n🎉 Selesai! Berhasil melakukan {len(ops)} perubahan file.")
            
            messages.append(AIMessage(content=ai_text))
            
        except Exception as e:
            print(f"❌ Terjadi kesalahan: {e}")

if __name__ == "__main__":
    main()