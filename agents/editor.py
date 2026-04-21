"""
agents/editor.py — Agent dengan kemampuan membaca, membuat, dan mengedit file.
Mendukung operasi [SAVE], [DELETE], [MOVE], dan [RUN].
"""

import os
import re
import shutil
import subprocess
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import get_llm, SYSTEM_PROMPT_EDITOR
from utils.scanner import scan_workspace

def execute_file_operations(ai_response, chat_history):
    """
    Mem-parsing dan mengeksekusi operasi file/terminal dari respons AI.
    """
    struktur_berubah = False
    
    # 1. Logika SAVE (Membuat/Mengedit File)
    save_pattern = r"\[SAVE:\s*(.+?)\]\s*```[a-zA-Z]*\n(.*?)```"
    matches_save = re.findall(save_pattern, ai_response, re.DOTALL)
    for filepath, code_content in matches_save:
        filepath = filepath.strip()
        print(f"⏳ Mengeksekusi SAVE: {filepath}")
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code_content)
            print(f"✅ Berhasil menyimpan: {filepath}")
            struktur_berubah = True
        except Exception as e:
            print(f"❌ Gagal menyimpan {filepath}: {e}")

    # 2. Logika DELETE (Menghapus File)
    delete_pattern = r"\[DELETE:\s*(.+?)\]"
    matches_delete = re.findall(delete_pattern, ai_response)
    for filepath in matches_delete:
        filepath = filepath.strip()
        print(f"⏳ Mengeksekusi DELETE: {filepath}")
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🗑️ Berhasil menghapus: {filepath}")
                struktur_berubah = True
            else:
                print(f"⚠️ File tidak ditemukan: {filepath}")
        except Exception as e:
            print(f"❌ Gagal menghapus {filepath}: {e}")

    # 3. Logika MOVE (Memindahkan/Rename File)
    move_pattern = r"\[MOVE:\s*(.+?)\s*->\s*(.+?)\]"
    matches_move = re.findall(move_pattern, ai_response)
    for old_path, new_path in matches_move:
        old_path, new_path = old_path.strip(), new_path.strip()
        print(f"⏳ Mengeksekusi MOVE dari {old_path} ke {new_path}")
        try:
            if os.path.exists(old_path):
                os.makedirs(os.path.dirname(new_path), exist_ok=True) if os.path.dirname(new_path) else None
                shutil.move(old_path, new_path)
                print(f"🚚 Berhasil memindahkan ke: {new_path}")
                struktur_berubah = True
            else:
                print(f"⚠️ File sumber tidak ditemukan: {old_path}")
        except Exception as e:
            print(f"❌ Gagal memindahkan {old_path}: {e}")

    # 4. Logika RUN (Menjalankan Terminal)
    run_pattern = r"\[RUN:\s*(.+?)\]"
    matches_run = re.findall(run_pattern, ai_response)
    for cmd in matches_run:
        cmd = cmd.strip()
        print(f"\n⚠️  PERINGATAN TERMINAL! AI ingin menjalankan: \033[93m{cmd}\033[0m")
        konfirmasi = input("Izinkan eksekusi? (y/n): ").strip().lower()
        if konfirmasi == 'y':
            try:
                result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
                if result.stdout:
                    print(f"✅ Output:\n{result.stdout.strip()}")
                    chat_history.append(SystemMessage(content=f"Eksekusi '{cmd}' sukses:\n{result.stdout}"))
                if result.stderr:
                    print(f"❌ Error:\n{result.stderr.strip()}")
                    chat_history.append(SystemMessage(content=f"Eksekusi '{cmd}' gagal:\n{result.stderr}"))
                struktur_berubah = True
            except Exception as e:
                print(f"❌ Gagal menjalankan perintah: {e}")
    
    return struktur_berubah

def main(folder_path="."):
    print("=== AI FILE EDITOR & DEVOPS AGENT ===\n")
    
    llm = get_llm(temperature=0.2)
    chat_history = [SystemMessage(content=SYSTEM_PROMPT_EDITOR)]
    
    # Initial scan
    docs, file_count = scan_workspace(folder_path)
    loaded_files = [d['path'] for d in docs]
    
    print(f"✅ Berhasil memuat {file_count} file kodingan.")
    print("Ketik 'exit' untuk keluar.\n")

    while True:
        try:
            user_input = input("Lu: ").strip()
        except KeyboardInterrupt:
            break
            
        if user_input.lower() == "exit":
            break
        if not user_input:
            continue

        # Berikan daftar file ke AI agar dia tahu strukturnya
        file_list_str = "\n".join([f"- {f}" for f in loaded_files])
        prompt = f"STRUKTUR PROJECT SAAT INI:\n{file_list_str}\n\nPertanyaan User: {user_input}"
        
        chat_history.append(HumanMessage(content=prompt))

        print("AI sedang memproses...")
        try:
            response = llm.invoke(chat_history)
            jawaban = response.content
            chat_history.append(AIMessage(content=jawaban))
            
            print(f"\nAI: {jawaban}\n")
            
            # Eksekusi aksi jika ada
            if execute_file_operations(jawaban, chat_history):
                # Refresh workspace jika ada perubahan struktur
                docs, file_count = scan_workspace(folder_path)
                loaded_files = [d['path'] for d in docs]
                print(f"🔄 Workspace di-refresh ({file_count} file sekarang terbaca).")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()