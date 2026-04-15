import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json
import random
import os
import sys
from datetime import datetime

# Název souboru s daty
DATA_FILENAME = "otazky.json"

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dependabilita IS - Pro Trainer")
        self.root.geometry("1000x800")
        
        self._setup_styles()
        self.data_path = self.get_data_path()
        self.all_questions = self.load_data()
        
        # Stavové proměnné
        self.current_quiz_list = []
        self.user_answers_history = [] 
        self.current_index = 0
        self.score = 0
        
        # Režimy hry
        self.elimination_mode = False 
        self.sudden_death_mode = False

        # Pomocná proměnná pro klávesové zkratky (aby fungovaly jen při kvízu)
        self.is_quiz_active = False

        # Hlavní kontejner
        self.container = tk.Frame(self.root, bg=self.colors["bg"])
        self.container.pack(fill="both", expand=True)
        
        # --- KLÁVESOVÉ ZKRATKY ---
        self.root.bind("<Key>", self.handle_keypress)
        
        if self.all_questions:
            self.show_menu()
        else:
            tk.Label(self.root, text="Chyba: Data nenalezena!", fg="red").pack()

    def get_data_path(self):
        if getattr(sys, 'frozen', False):
            path = os.path.dirname(sys.executable)
        else:
            path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(path, DATA_FILENAME)

    def _setup_styles(self):
        self.colors = {
            "bg": "#f4f6f9",
            "primary": "#3b82f6",     
            "success": "#22c55e",     
            "danger": "#ef4444",      
            "warning": "#f59e0b",
            "dark": "#111827",        
            "text": "#1f2937",
            "white": "#ffffff",
            "disabled": "#e5e7eb"
        }
        self.fonts = {
            "title": ("Segoe UI", 26, "bold"),
            "subtitle": ("Segoe UI", 14),
            "question": ("Segoe UI", 15, "bold"),
            "option": ("Segoe UI", 12),
            "explanation": ("Segoe UI", 11, "italic"),
            "score": ("Segoe UI", 12, "bold")
        }
        self.root.configure(bg=self.colors["bg"])

    def load_data(self):
        if not os.path.exists(self.data_path):
            messagebox.showerror("Chyba", f"Soubor nenalezen: {self.data_path}")
            return []
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Chyba", f"JSON Error: {e}")
            return []

    def clear_frame(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    # ================= OVLÁDÁNÍ KLÁVESNICÍ =================
    def handle_keypress(self, event):
        """Reaguje na stisk kláves a,b,c a šipek."""
        # Pokud nejsme v kvízu (např. menu, výsledky), nic nedělat
        if not self.is_quiz_active:
            return

        key = event.char.lower()
        keysym = event.keysym

        # 1. Odpovídání (a, b, c)
        if key in ['a', 'b', 'c']:
            # Zkontrolujeme, zda tlačítko existuje a je aktivní (state="normal")
            if hasattr(self, 'btns') and key in self.btns:
                btn = self.btns[key]
                if btn['state'] == 'normal':
                    self.evaluate_answer(key)
        
        # 2. Navigace Další (Enter, Right Arrow)
        elif keysym in ['Return', 'Right','space']:
            if hasattr(self, 'btn_next') and self.btn_next['state'] == 'normal':
                self.next_step()

        # 3. Navigace Zpět (Left Arrow)
        elif keysym == 'Left':
            if hasattr(self, 'btn_prev') and self.btn_prev['state'] == 'normal':
                self.prev_step()

    # ================= HLAVNÍ MENU =================
    def show_menu(self):
        self.clear_frame()
        self.is_quiz_active = False # Deaktivace klávesnice pro kvíz
        self.elimination_mode = False
        self.sudden_death_mode = False
        
        frame = tk.Frame(self.container, bg=self.colors["bg"])
        frame.pack(expand=True)

        tk.Label(frame, text="Dependabilita IS", font=self.fonts["title"], 
                 bg=self.colors["bg"], fg=self.colors["primary"]).pack(pady=20)
        
        info_text = f"Databáze: {len(self.all_questions)} otázek"
        tk.Label(frame, text=info_text, font=self.fonts["subtitle"], bg=self.colors["bg"]).pack(pady=10)

        # Základní styl tlačítek
        btn_opts = {"font": self.fonts["subtitle"], "width": 30, "pady": 8, "bg": "white", "relief": "groove", "cursor": "hand2"}

        tk.Button(frame, text="🚀 Spustit vše (Popořadě)", command=lambda: self.start_quiz_session(self.all_questions), **btn_opts).pack(pady=5)
        tk.Button(frame, text="🎲 Náhodný výběr", command=self.start_random_setup, **btn_opts).pack(pady=5)
        
        # TLAČÍTKO SUDDEN DEATH
        sd_btn_opts = btn_opts.copy()
        sd_btn_opts.update({"bg": self.colors["dark"], "fg": self.colors["danger"]})
        tk.Button(frame, text="💀 Sudden Death (Náhlá smrt)", command=self.choose_sudden_death_mode, 
                  **sd_btn_opts).pack(pady=5)
        
        tk.Button(frame, text="✅ Vybrat konkrétní otázky", command=self.start_manual_selection, **btn_opts).pack(pady=5)
        tk.Button(frame, text="📜 Historie odpovědí (Načíst)", command=self.load_history_file, **btn_opts).pack(pady=5)
        tk.Button(frame, text="❌ Ukončit", command=self.root.quit, **btn_opts).pack(pady=20)

    # ================= PŘÍPRAVA HRY =================
    def start_random_setup(self):
        max_q = len(self.all_questions)
        count = simpledialog.askinteger("Náhodný test", f"Kolik otázek chcete? (1-{max_q})", 
                                        minvalue=1, maxvalue=max_q, parent=self.root)
        if count:
            self.start_quiz_session(random.sample(self.all_questions, count))

    def choose_sudden_death_mode(self):
        win = tk.Toplevel(self.root)
        win.title("Sudden Death - Výběr")
        win.geometry("400x300")
        win.configure(bg=self.colors["dark"])
        
        tk.Label(win, text="💀 Vyberte režim smrti", font=("Segoe UI", 16, "bold"), 
                 bg=self.colors["dark"], fg=self.colors["danger"]).pack(pady=20)
        
        btn_style = {"font": ("Segoe UI", 12), "width": 25, "pady": 10, "cursor": "hand2", "bg": "white"}
        
        tk.Button(win, text="🔀 Náhodné pořadí", 
                  command=lambda: [win.destroy(), self.start_sudden_death(random_order=True)], 
                  **btn_style).pack(pady=10)
        
        tk.Button(win, text="🔢 Popořadě (1 -> Konec)", 
                  command=lambda: [win.destroy(), self.start_sudden_death(random_order=False)], 
                  **btn_style).pack(pady=10)

    def start_sudden_death(self, random_order=True):
        if not self.all_questions: return
        
        if random_order:
            final_list = random.sample(self.all_questions, len(self.all_questions))
        else:
            final_list = sorted(self.all_questions, key=lambda x: x['id'])
            
        messagebox.showwarning("Varování", "V režimu SUDDEN DEATH končí hra při první chybě!\nHodně štěstí.")
        self.start_quiz_session(final_list, sudden_death=True)

    def start_manual_selection(self):
        sel_window = tk.Toplevel(self.root)
        sel_window.title("Výběr otázek")
        sel_window.geometry("600x600")
        
        lbl = tk.Label(sel_window, text="Vyberte otázky (Ctrl+Click):", font=("Segoe UI", 12))
        lbl.pack(pady=10)
        
        frame_list = tk.Frame(sel_window)
        frame_list.pack(fill="both", expand=True, padx=10)
        
        scrollbar = tk.Scrollbar(frame_list)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tk.Listbox(frame_list, selectmode="multiple", font=("Segoe UI", 10), yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        sorted_qs = sorted(self.all_questions, key=lambda x: x['id'])
        for q in sorted_qs:
            listbox.insert(tk.END, f"{q['id']}) {q['question']}")

        def confirm_selection():
            indexes = listbox.curselection()
            if not indexes:
                messagebox.showwarning("Pozor", "Nevybrali jste žádnou otázku!")
                return
            selected_questions = [sorted_qs[i] for i in indexes]
            sel_window.destroy()
            self.start_quiz_session(selected_questions)

        tk.Button(sel_window, text="Spustit vybrané", command=confirm_selection, 
                  bg=self.colors["primary"], fg="white", font=("Segoe UI", 12, "bold"), pady=10).pack(fill="x", padx=20, pady=20)

    def start_quiz_session(self, questions_list, elimination=False, sudden_death=False):
        if not questions_list:
            messagebox.showinfo("Info", "Žádné otázky.")
            self.show_menu()
            return

        self.elimination_mode = elimination
        self.sudden_death_mode = sudden_death
        self.current_quiz_list = questions_list
        self.current_index = 0
        self.score = 0
        self.user_answers_history = [] 
        
        self.is_quiz_active = True # Aktivace klávesnice
        self.show_question()

    # ================= PRŮBĚH HRY =================
    def finish_early(self):
        if not self.user_answers_history:
            if messagebox.askyesno("Ukončit", "Zatím jste neodpověděli na žádnou otázku. Zpět do menu?"):
                self.show_menu()
            return

        if messagebox.askyesno("Ukončit předčasně", "Opravdu chcete test ukončit?\n(Výsledky se vypočítají z dosavadních odpovědí)"):
            self.show_results()

    def show_question(self):
        self.clear_frame()
        q_data = self.current_quiz_list[self.current_index]
        
        # --- 1. Header ---
        top_bg = self.colors["dark"] if self.sudden_death_mode else self.colors["bg"]
        top_fg = self.colors["danger"] if self.sudden_death_mode else "#555"
        
        top = tk.Frame(self.container, bg=top_bg)
        top.pack(fill="x", padx=20, pady=15)
        
        # Texty režimů
        mode_text = ""
        if self.elimination_mode: mode_text = " (Eliminace)"
        if self.sudden_death_mode: mode_text = " (💀 NÁHLÁ SMRT)"

        tk.Label(top, text=f"Otázka {self.current_index + 1} / {len(self.current_quiz_list)}{mode_text}", 
                 font=("Segoe UI", 12, "bold"), bg=top_bg, fg=top_fg).pack(side="left")
        
        correct_count = sum(1 for x in self.user_answers_history if x['is_correct'])
        total_ans = len(self.user_answers_history)
        pct = int((correct_count / total_ans) * 100) if total_ans > 0 else 0
        score_txt = f"Úspěšnost: {pct} %" if total_ans > 0 else "Úspěšnost: - %"
        
        self.lbl_score = tk.Label(top, text=score_txt, font=self.fonts["score"], bg=top_bg, fg=self.colors["primary"])
        self.lbl_score.pack(side="right")
        
        ttk.Separator(self.container, orient="horizontal").pack(fill="x", padx=10)

        # --- 2. Obsah ---
        content_frame = tk.Frame(self.container, bg=self.colors["bg"])
        content_frame.pack(fill="both", expand=True, padx=40, pady=10)

        full_text = f"{q_data['id']}) {q_data['question']}"
        tk.Label(content_frame, text=full_text, font=self.fonts["question"], 
                 bg=self.colors["bg"], wraplength=900, justify="left").pack(anchor="w", pady=(0, 20))

        self.btns = {}
        for key, val in q_data["options"].items():
            # Tlačítka nyní mají text začínající "A) ...", což ladí s klávesovou zkratkou
            b = tk.Button(content_frame, text=f"{key.upper()}) {val}", font=self.fonts["option"], 
                          bg="white", activebackground="#f0f0f0", relief="groove", bd=1, pady=10, anchor="w", padx=15,
                          command=lambda k=key: self.evaluate_answer(k))
            b.pack(fill="x", pady=6)
            self.btns[key] = b

        self.lbl_expl = tk.Label(content_frame, text="", font=self.fonts["explanation"], 
                                 bg=self.colors["bg"], wraplength=900, justify="left")
        self.lbl_expl.pack(pady=20, anchor="w")

        # --- 3. Navigace ---
        nav_frame = tk.Frame(self.container, bg="#e0e0e0", pady=15, padx=20)
        nav_frame.pack(side="bottom", fill="x")

        nav_frame.columnconfigure(0, weight=1)
        nav_frame.columnconfigure(1, weight=1)
        nav_frame.columnconfigure(2, weight=1)

        # Tlačítko Předchozí
        state_prev = "normal" if self.current_index > 0 and not self.sudden_death_mode else "disabled"
        self.btn_prev = tk.Button(nav_frame, text="<< Předchozí (←)", state=state_prev, command=self.prev_step,
                                  font=("Segoe UI", 11), width=15)
        self.btn_prev.grid(row=0, column=0, sticky="w")

        # Tlačítko Ukončit
        self.btn_end = tk.Button(nav_frame, text="🏳 Ukončit předčasně", command=self.finish_early,
                                 bg="#fff3cd", fg="#856404", font=("Segoe UI", 10), relief="flat")
        self.btn_end.grid(row=0, column=1)

        # Tlačítko Další
        self.btn_next = tk.Button(nav_frame, text="Další otázka (→)", state="disabled", command=self.next_step,
                                  bg=self.colors["primary"], fg="white", font=("Segoe UI", 11, "bold"), width=20)
        self.btn_next.grid(row=0, column=2, sticky="e")

        # Obnova stavu
        existing_record = next((item for item in self.user_answers_history if item["id"] == q_data["id"]), None)
        if existing_record:
            self.restore_ui_state(existing_record)

    def restore_ui_state(self, record):
        user_key = record["user_key"]
        correct_key = record["correct_key"]
        is_correct = record["is_correct"]
        
        for k, btn in self.btns.items():
            btn.config(state="disabled", cursor="arrow")
            if k == correct_key:
                btn.config(bg=self.colors["success"], fg="white")
            elif k == user_key and not is_correct:
                btn.config(bg=self.colors["danger"], fg="white")

        status = "✅ SPRÁVNĚ!" if is_correct else "❌ CHYBA!"
        color = self.colors["success"] if is_correct else self.colors["danger"]
        self.lbl_expl.config(text=f"{status} {record['explanation']}", fg=color)
        self.btn_next.config(state="normal")


    def evaluate_answer(self, user_key):
        q_data = self.current_quiz_list[self.current_index]
        correct_key = q_data["correct"]
        is_correct = (user_key == correct_key)

        record = {
            "id": q_data["id"],
            "question": q_data["question"],
            "options": q_data["options"],
            "user_key": user_key,
            "correct_key": correct_key,
            "is_correct": is_correct,
            "explanation": q_data.get("explanation", ""),
            "raw_data": q_data
        }
        
        self.user_answers_history.append(record)
        self.restore_ui_state(record)
        
        correct_count = sum(1 for x in self.user_answers_history if x['is_correct'])
        total_ans = len(self.user_answers_history)
        pct = int((correct_count / total_ans) * 100)
        self.lbl_score.config(text=f"Úspěšnost: {pct} %")

        # LOGIKA SUDDEN DEATH
        if self.sudden_death_mode and not is_correct:
            messagebox.showerror("☠️ GAME OVER", f"Špatná odpověď v režimu Náhlá smrt!\n\nSprávně bylo: {correct_key.upper()}\n\nKonec hry.")
            self.show_results()

    def prev_step(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()

    def next_step(self):
        if self.elimination_mode:
            q_id = self.current_quiz_list[self.current_index]['id']
            record = next((item for item in reversed(self.user_answers_history) if item["id"] == q_id), None)
            if record and record["is_correct"]:
                del self.current_quiz_list[self.current_index]
            else:
                self.current_index += 1
        else:
            self.current_index += 1

        if self.current_index < len(self.current_quiz_list):
            self.show_question()
        else:
            self.show_results()

    # ================= VÝSLEDKY =================
    def show_results(self):
        self.clear_frame()
        self.is_quiz_active = False # Vypnutí klávesnice ve výsledcích
        
        correct = sum(1 for x in self.user_answers_history if x['is_correct'])
        total = len(self.user_answers_history)
        if total == 0: total = 1 
        percent = int((correct / total) * 100)
        
        wrong_ids = set()
        for r in self.user_answers_history:
            if not r['is_correct']:
                wrong_ids.add(r['id'])
        
        wrong_data = [q for q in self.all_questions if q['id'] in wrong_ids]

        frame = tk.Frame(self.container, bg=self.colors["bg"])
        frame.pack(expand=True)
        
        # Titulek výsledků
        if self.sudden_death_mode and not (percent == 100 and total == len(self.current_quiz_list)):
            res_title = "☠️ GAME OVER ☠️"
            title_color = self.colors["danger"]
        elif self.elimination_mode:
            res_title = "Kolo dokončeno!"
            title_color = self.colors["text"]
        else:
            res_title = "Výsledky testu"
            title_color = self.colors["text"]

        tk.Label(frame, text=res_title, font=self.fonts["title"], bg=self.colors["bg"], fg=title_color).pack(pady=10)
        
        col = self.colors["success"] if percent >= 75 else self.colors["danger"]
        tk.Label(frame, text=f"{percent} %", font=("Segoe UI", 60, "bold"), fg=col, bg=self.colors["bg"]).pack(pady=5)
        tk.Label(frame, text=f"(Správně {correct} z {total} zodpovězených)", font=self.fonts["subtitle"], bg=self.colors["bg"]).pack(pady=5)
        
        btn_opts = {"font": self.fonts["subtitle"], "width": 30, "pady": 8, "cursor": "hand2"}

        tk.Button(frame, text="💾 Uložit si svoje odpovědi", command=self.save_results_to_file, bg="#e0f2f1", **btn_opts).pack(pady=5)
        
        played_ids = set(r['id'] for r in self.user_answers_history)
        played_qs = [q for q in self.all_questions if q['id'] in played_ids]
        
        if self.sudden_death_mode:
             tk.Button(frame, text="🔄 Zkusit Sudden Death znovu", 
                  command=self.choose_sudden_death_mode, bg=self.colors["dark"], fg=self.colors["danger"], **btn_opts).pack(pady=5)
        else:
            tk.Button(frame, text="🔄 Restartovat tento výběr", 
                    command=lambda: self.start_quiz_session(played_qs), bg="white", **btn_opts).pack(pady=5)

        if wrong_data and not self.sudden_death_mode:
             tk.Button(frame, text=f"⚠️ Procvičovat jen chyby ({len(wrong_data)})", 
                      command=lambda: self.start_quiz_session(wrong_data, elimination=True), 
                      bg="#ffebee", **btn_opts).pack(pady=5)
        elif self.elimination_mode:
             tk.Label(frame, text="Všechny chyby opraveny!", fg=self.colors["success"], font=self.fonts["subtitle"], bg=self.colors["bg"]).pack()

        tk.Button(frame, text="🏠 Hlavní menu", command=self.show_menu, bg="white", **btn_opts).pack(pady=20)

    # ================= UKLÁDÁNÍ A HISTORIE =================
    def save_results_to_file(self):
        if not self.user_answers_history:
            messagebox.showwarning("Prázdné", "Nemáte žádné odpovědi k uložení.")
            return

        default_name = f"vysledky_{datetime.now().strftime('%Y-%m-%d_%H-%M')}"
        filename = simpledialog.askstring("Uložit", "Zadejte název souboru:", initialvalue=default_name)
        
        if not filename: return
        if not filename.endswith(".json"): filename += ".json"
        
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
        full_path = os.path.join(app_dir, filename)
        
        data_to_save = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "Sudden Death" if self.sudden_death_mode else "Standard",
            "history": self.user_answers_history
        }

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Úspěch", f"Soubor uložen:\n{filename}")
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se uložit soubor:\n{e}")

    def load_history_file(self):
        if getattr(sys, 'frozen', False):
            init_dir = os.path.dirname(sys.executable)
        else:
            init_dir = os.path.dirname(os.path.abspath(__file__))

        filepath = filedialog.askopenfilename(initialdir=init_dir, title="Vybrat soubor historie", filetypes=[("JSON files", "*.json")])
        if not filepath: return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            
            history_list = saved_data.get("history", [])
            self.show_history_grid(history_list, os.path.basename(filepath))
            
        except Exception as e:
            messagebox.showerror("Chyba", f"Soubor nelze přečíst: {e}")

    def show_history_grid(self, history, title):
        self.clear_frame()
        self.is_quiz_active = False # Deaktivace pro grid
        
        top_frame = tk.Frame(self.container, bg=self.colors["bg"])
        top_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Button(top_frame, text="<< Zpět do menu", command=self.show_menu).pack(side="left")
        tk.Label(top_frame, text=f"Historie: {title}", font=self.fonts["subtitle"], bg=self.colors["bg"]).pack(side="left", padx=20)
        
        wrong_ids = set()
        wrong_data = []
        for h in history:
            if not h["is_correct"] and h["id"] not in wrong_ids:
                wrong_ids.add(h["id"])
                wrong_data.append(h["raw_data"])
        
        if wrong_data:
             tk.Button(top_frame, text=f"Procvičit tyto chyby ({len(wrong_data)})", 
                       bg="#ffebee", command=lambda: self.start_quiz_session(wrong_data, elimination=True)).pack(side="right")

        canvas = tk.Canvas(self.container, bg=self.colors["bg"])
        scrollbar = tk.Scrollbar(self.container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors["bg"])

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")

        cols = 10
        for i, record in enumerate(history):
            row = i // cols
            col = i % cols
            color = self.colors["success"] if record["is_correct"] else self.colors["danger"]
            btn = tk.Button(scrollable_frame, text=str(record["id"]), bg=color, fg="white", 
                            font=("Segoe UI", 10, "bold"), width=5, height=2,
                            command=lambda r=record: self.show_history_detail(r))
            btn.grid(row=row, column=col, padx=5, pady=5)

    def show_history_detail(self, record):
        win = tk.Toplevel(self.root)
        win.title(f"Detail otázky {record['id']}")
        win.geometry("600x500")
        
        tk.Label(win, text=f"Otázka {record['id']}:", font=("Segoe UI", 12, "bold")).pack(pady=10)
        tk.Label(win, text=record["question"], wraplength=550, font=("Segoe UI", 11)).pack(pady=5)
        
        user_opt_text = record['options'].get(record['user_key'], 'N/A')
        lbl_u = tk.Label(win, text=f"Vaše odpověď: {user_opt_text}", font=("Segoe UI", 11, "bold"))
        lbl_u.pack(pady=10)
        lbl_u.config(fg="green" if record['is_correct'] else "red")
        
        if not record['is_correct']:
            corr_opt_text = record['options'].get(record['correct_key'], 'N/A')
            tk.Label(win, text=f"Správně mělo být: {corr_opt_text}", font=("Segoe UI", 11, "bold"), fg="green").pack(pady=5)
        
        if record["explanation"]:
            tk.Label(win, text="Vysvětlení:", font=("Segoe UI", 10, "italic")).pack(pady=10)
            tk.Label(win, text=record["explanation"], wraplength=550).pack()
            
        tk.Button(win, text="Zavřít", command=win.destroy).pack(side="bottom", pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()