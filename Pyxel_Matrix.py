import tkinter as tk
from tkinter import messagebox, filedialog
import json
import csv
import re
import sys
import os


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class PyxelMatrixApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pyxel Matrix")
        self.root.geometry("900x950")

        # Color Palette
        self.bg_color = "#121212"
        self.frame_bg = "#1e1e1e"
        self.fg_color = "#2eb82e"
        self.entry_bg = "#262626"
        self.grid_label_fg = "#4d4d4d"

        self.root.configure(bg=self.bg_color)

        # Use the resolver for the Icon
        try:
            icon_path = resource_path("matlog.ico")
            self.root.iconbitmap(icon_path)
        except:
            pass

            # --- TOP SECTION: LOGO ---
        header_frame = tk.Frame(root, bg=self.bg_color)
        header_frame.pack(fill="x", pady=10)

        # Use the resolver for the PNG
        try:
            logo_path = resource_path("matlog.png")
            self.logo_img = tk.PhotoImage(file=logo_path)
            self.logo_label = tk.Label(header_frame, image=self.logo_img, bg=self.bg_color)
            self.logo_label.pack(pady=5)
        except:
            tk.Label(header_frame, text="PYXEL MATRIX", font=("Courier", 20, "bold"),
                     bg=self.bg_color, fg=self.fg_color).pack()

        # --- 1. SETTINGS & MODE ---
        top_frame = tk.Frame(root, bg=self.bg_color, padx=10, pady=5)
        top_frame.pack(fill="x")

        mode_frame = tk.LabelFrame(top_frame, text="Logic Mode", bg=self.frame_bg, fg=self.fg_color, padx=10, pady=5,
                                   font=("Arial", 9, "bold"))
        mode_frame.pack(side="left", padx=5)
        self.mode_var = tk.StringVar(value="HYBRID")

        for text, mode in [("Hybrid", "HYBRID"), ("Dynamic", "DYNAMIC")]:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=mode,
                           bg=self.frame_bg, fg=self.fg_color, selectcolor=self.bg_color,
                           activebackground=self.frame_bg, activeforeground=self.fg_color).pack(anchor="w")

        sys_var_frame = tk.LabelFrame(top_frame, text="System Symbols", bg=self.frame_bg, fg=self.fg_color, padx=10,
                                      pady=5, font=("Arial", 9, "bold"))
        sys_var_frame.pack(side="left", padx=5)

        self.m_var_ent = self.create_shaded_entry(sys_var_frame, "Mapping", 0, 1, "Mapping:")
        self.o_var_ent = self.create_shaded_entry(sys_var_frame, "Result", 0, 3, "Output:")
        self.prefix_ent = self.create_shaded_entry(sys_var_frame, "MAT", 0, 5, "Prefix:")

        # --- 2. FILE MANAGEMENT ---
        file_frame = tk.Frame(root, bg=self.bg_color, pady=10)
        file_frame.pack(fill="x")

        self.create_shaded_button(file_frame, "LOAD CSV/EXCEL", self.load_file, "#b38f00").pack(side="left", padx=20)
        self.create_shaded_button(file_frame, "Save JSON", lambda: self.save_file("json")).pack(side="left", padx=5)
        self.create_shaded_button(file_frame, "Save CSV", lambda: self.save_file("csv")).pack(side="left", padx=5)
        self.create_shaded_button(file_frame, "CLEAR GRID", self.clear_grid, "#99261a").pack(side="right", padx=20)

        # --- 3. DIMENSIONS ---
        dim_frame = tk.Frame(root, bg=self.bg_color, pady=5)
        dim_frame.pack(fill="x")

        tk.Label(dim_frame, text="Rows:", bg=self.bg_color, fg=self.fg_color).pack(side="left", padx=5)
        self.rows_ent = tk.Entry(dim_frame, width=4, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color,
                                 borderwidth=0)
        self.rows_ent.insert(0, "10");
        self.rows_ent.pack(side="left")

        tk.Label(dim_frame, text="Cols:", bg=self.bg_color, fg=self.fg_color).pack(side="left", padx=5)
        self.cols_ent = tk.Entry(dim_frame, width=4, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color,
                                 borderwidth=0)
        self.cols_ent.insert(0, "10");
        self.cols_ent.pack(side="left")

        self.create_shaded_button(dim_frame, "Resize Grid", self.create_grid).pack(side="left", padx=10)

        # --- 4. THE GRID ---
        self.canvas = tk.Canvas(root, bg=self.bg_color, highlightthickness=0)
        self.grid_frame = tk.Frame(self.canvas, bg=self.bg_color)
        self.scrollbar = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.cells = {}
        self.create_grid()

        # --- 5. FOOTER ---
        self.create_shaded_button(root, "GENERATE GBVM CODE", self.generate_gbvm, self.fg_color,
                                  font=("Arial", 12, "bold")).pack(fill="x", padx=20, pady=15)

    def create_shaded_entry(self, parent, default, r, c, label_text):
        tk.Label(parent, text=label_text, bg=self.frame_bg, fg=self.fg_color).grid(row=r, column=c - 1)
        ent = tk.Entry(parent, width=12, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color,
                       borderwidth=0)
        ent.insert(0, default)
        ent.grid(row=r, column=c, padx=5, pady=2)
        return ent

    def create_shaded_button(self, parent, text, cmd, color=None, font=("Arial", 9, "bold")):
        btn_fg = color if color else self.fg_color
        return tk.Button(parent, text=text, command=cmd, bg=self.frame_bg, fg=btn_fg,
                         activebackground=self.fg_color, activeforeground=self.bg_color,
                         relief="flat", font=font, padx=10)

    def clean_symbol(self, text):
        text = text.strip()
        if not text: return ""
        if re.match(r'^-?\d+$', text): return text
        clean = re.sub(r'[^a-zA-Z0-9]', '_', text).upper()
        if not clean.startswith("VAR_"): clean = "VAR_" + clean
        return clean

    def create_grid(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.cells = {}
        try:
            r_count = int(self.rows_ent.get())
            c_count = int(self.cols_ent.get())
            for r in range(1, r_count + 1):
                for c in range(1, c_count + 1):
                    lbl = tk.Label(self.grid_frame, text=f"{r},{c}", font=("Arial", 7), bg=self.bg_color,
                                   fg=self.grid_label_fg)
                    lbl.grid(row=(r - 1) * 2, column=c - 1)
                    e = tk.Entry(self.grid_frame, width=12, bg=self.entry_bg, fg=self.fg_color,
                                 insertbackground=self.fg_color, borderwidth=0)
                    e.grid(row=(r - 1) * 2 + 1, column=c - 1, padx=2, pady=2)
                    self.cells[(r, c)] = e
        except ValueError:
            messagebox.showerror("Error", "Invalid dimensions.")

    def clear_grid(self):
        if messagebox.askyesno("Confirm", "Clear all cells?"):
            for e in self.cells.values(): e.delete(0, tk.END)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV/JSON", "*.csv *.json")])
        if not path: return
        if path.endswith('.csv'):
            with open(path, 'r', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                self.rows_ent.delete(0, tk.END);
                self.rows_ent.insert(0, str(len(reader)))
                self.cols_ent.delete(0, tk.END);
                self.cols_ent.insert(0, str(len(reader[0])))
                self.create_grid()
                for r_idx, row_data in enumerate(reader):
                    for c_idx, val in enumerate(row_data):
                        if (r_idx + 1, c_idx + 1) in self.cells:
                            self.cells[(r_idx + 1, c_idx + 1)].insert(0, val.strip())
        elif path.endswith('.json'):
            with open(path, 'r') as f:
                data = json.load(f)
                self.create_grid()
                for k, v in data.items():
                    try:
                        r, c = map(int, k.split(','))
                        if (r, c) in self.cells: self.cells[(r, c)].insert(0, v)
                    except:
                        continue

    def save_file(self, ftype):
        path = filedialog.asksaveasfilename(defaultextension=f".{ftype}")
        if not path: return
        if ftype == "json":
            data = {f"{r},{c}": e.get() for (r, c), e in self.cells.items() if e.get().strip()}
            with open(path, 'w') as f:
                json.dump(data, f)
        else:
            r_c, c_c = int(self.rows_ent.get()), int(self.cols_ent.get())
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for r in range(1, r_c + 1):
                    writer.writerow([self.cells[(r, c)].get() for c in range(1, c_c + 1)])

    def generate_gbvm(self):
        mode = self.mode_var.get()
        mapping_var = self.clean_symbol(self.m_var_ent.get())
        output_var = self.clean_symbol(self.o_var_ent.get())
        prefix = self.prefix_ent.get().strip().upper()
        lines = [f"; --- Pyxel Matrix Output ---", f"; Formula: (Row * 100) + Col"]
        setters = []
        for (r, c), e in self.cells.items():
            val = e.get().strip()
            if val or mode == "DYNAMIC":
                m_id = (r * 100) + c
                lbl = f"L_{r}_{c}"
                lines.append(f"VM_IF_CONST .EQ, {mapping_var}, {m_id}, {lbl}, 0")
                if mode == "DYNAMIC":
                    cmd = f"VM_SET {output_var}, VAR_{prefix}_{r}_{c}"
                else:
                    clean_val = self.clean_symbol(val)
                    cmd = f"VM_SET_CONST {output_var}, {clean_val}" if re.match(r'^-?\d+$',
                                                                                clean_val) else f"VM_SET {output_var}, {clean_val}"
                setters.append((lbl, cmd))
        lines.append("VM_RET_FAR\n")
        for lbl, cmd in setters: lines.extend([f"{lbl}:", f"    {cmd}", "    VM_RET_FAR"])
        self.root.clipboard_clear();
        self.root.clipboard_append("\n".join(lines));
        self.root.update()
        messagebox.showinfo("Success", "GBVM Code Copied!")


if __name__ == "__main__":
    root = tk.Tk();
    app = PyxelMatrixApp(root);
    root.mainloop()