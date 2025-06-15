import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

MAX_IMG_SIZE = 600

def load_image(path, box, master):
    try:
        img = Image.open(path)
        img.thumbnail(box, Image.LANCZOS)
        return ImageTk.PhotoImage(img, master=master)
    except Exception:
        return None

class VisualizadorDuplicados(tk.Tk):
    def __init__(self, relatorio_path):
        super().__init__()
        self.title("Verificação Visual de Duplicados")
        self.configure(bg="black")

        with open(relatorio_path, encoding="utf-8") as f:
            self.grupos = json.load(f)
        self.idx_grupo = 0
        self.idx_dup = 0
        self.idx_ver = 0
        self.marcados = set()
        self._imagens = []

        # Header
        self.header = tk.Frame(self, bg="#222")
        self.header.pack(side="top", fill="x")
        self.btn_prev = tk.Button(self.header, text="<< Anterior", command=self.prev_grupo, font=("Arial",16))
        self.btn_prev.pack(side='left', padx=15, pady=10)
        self.lbl_grupo = tk.Label(self.header, text="", bg="#222", fg="white", font=("Arial",18,"bold"))
        self.lbl_grupo.pack(side='left', padx=20)
        self.btn_next = tk.Button(self.header, text="Próximo >>", command=self.next_grupo, font=("Arial",16))
        self.btn_next.pack(side='left', padx=15, pady=10)
        self.btn_sair = tk.Button(self.header, text="Sair", command=self.quit, font=("Arial",16), bg="#911", fg="white")
        self.btn_sair.pack(side='right', padx=15, pady=10)

        # Body
        self.body = tk.Frame(self, bg="black")
        self.body.pack(expand=True, fill="both")

        # Footer
        self.footer = tk.Frame(self, bg="#222")
        self.footer.pack(side="bottom", fill="x")
        self.btn_eliminar = tk.Button(self.footer, text="Eliminar todos os marcados", command=self.eliminar_marcados, font=("Arial",16), bg="#911", fg="white")
        self.btn_eliminar.pack(side="left", padx=15, pady=10)
        self.lbl_status = tk.Label(self.footer, text="", bg="#222", fg="white", font=("Arial",14))
        self.lbl_status.pack(side="left", padx=20)

        self.bind("<Escape>", lambda e: self.quit())
        self.atualizar()

    def atualizar(self):
        try:
            for widget in self.body.winfo_children():
                widget.destroy()
            self._imagens.clear()

            grupo = self.grupos[self.idx_grupo]
            ori_path = grupo.get("original")
            ori_nome = grupo.get("nome", os.path.basename(ori_path)) if ori_path else ""
            dups = grupo.get("duplicados", [])
            vers = grupo.get("a_verificar", [])

            self.lbl_grupo.config(text=f"Grupo {self.idx_grupo+1}/{len(self.grupos)}")
            cols = []
            if dups:
                cols.append(("duplicados", dups, self.idx_dup, self.prev_dup, self.next_dup))
            if ori_path:
                cols.append(("original", [{"caminho": ori_path, "nome": ori_nome}], 0, None, None))
            if vers:
                cols.append(("a_verificar", vers, self.idx_ver, self.prev_ver, self.next_ver))
            col_count = len(cols) if cols else 1

            for idx, (tipo, paths, idx_img, fn_prev, fn_next) in enumerate(cols):
                frame = tk.Frame(self.body, bg="black")
                frame.grid(row=0, column=idx, sticky="nsew", padx=10, pady=10)
                self.body.grid_columnconfigure(idx, weight=1)
                self.body.grid_rowconfigure(0, weight=1)

                if tipo != "original" and len(paths) > 1:
                    nav = tk.Frame(frame, bg="black")
                    nav.pack(side="top", pady=(10,0))
                    btn_prev = tk.Button(nav, text="<", command=fn_prev, font=("Arial",16), width=2)
                    btn_prev.pack(side="left", padx=5)
                    btn_next = tk.Button(nav, text=">", command=fn_next, font=("Arial",16), width=2)
                    btn_next.pack(side="left", padx=5)
                else:
                    tk.Label(frame, text="", bg="black").pack(side="top", pady=20)

                path = paths[idx_img % len(paths)].get("caminho")
                nome = paths[idx_img % len(paths)].get("nome")

                lbl_nome = tk.Label(frame, text=nome, bg="black", fg="white", font=("Arial",12,"bold"))
                lbl_nome.pack(side="top", pady=3)

                box = (self.winfo_screenwidth()//col_count-60, MAX_IMG_SIZE)
                if path and os.path.exists(path):
                    img_tk = load_image(path, box, self)
                    if img_tk:
                        lbl_img = tk.Label(frame, image=img_tk, bg="grey", width=box[0], height=box[1])
                        lbl_img.image = img_tk
                        self._imagens.append(img_tk)
                        lbl_img.pack(side="top", pady=5)
                    else:
                        lbl_img = tk.Label(frame, bg="grey", width=box[0], height=box[1], text="(Ficheiro não suportado)", fg="orange")
                        lbl_img.pack(side="top", pady=5)
                else:
                    lbl_img = tk.Label(frame, bg="grey", width=box[0], height=box[1], text="(Imagem não encontrada)", fg="white")
                    lbl_img.pack(side="top", pady=5)

                if tipo != "original" and path:
                    var = tk.BooleanVar(value=path in self.marcados)
                    chk = tk.Checkbutton(frame, text="Marcar para eliminar", variable=var, bg="black", fg="red",
                        font=("Arial",12,"bold"), selectcolor="black",
                        command=lambda v=var, p=path: self.toggle_marcado(v, p))
                    chk.pack(side="top", pady=5)
                    if path in self.marcados:
                        var.set(True)
                else:
                    tk.Label(frame, text="", bg="black").pack(side="top", pady=15)

            self.lbl_status.config(text=f"Total marcados: {len(self.marcados)}")
        except Exception as ex:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro na atualização", str(ex))

    def toggle_marcado(self, var, path):
        if var.get():
            self.marcados.add(path)
        else:
            self.marcados.discard(path)
        self.lbl_status.config(text=f"Total marcados: {len(self.marcados)}")

    def prev_grupo(self):
        self.idx_grupo = (self.idx_grupo - 1) % len(self.grupos)
        self.idx_dup = 0
        self.idx_ver = 0
        self.atualizar()

    def next_grupo(self):
        self.idx_grupo = (self.idx_grupo + 1) % len(self.grupos)
        self.idx_dup = 0
        self.idx_ver = 0
        self.atualizar()

    def prev_dup(self):
        dups = self.grupos[self.idx_grupo].get("duplicados", [])
        if dups:
            self.idx_dup = (self.idx_dup - 1) % len(dups)
            self.atualizar()

    def next_dup(self):
        dups = self.grupos[self.idx_grupo].get("duplicados", [])
        if dups:
            self.idx_dup = (self.idx_dup + 1) % len(dups)
            self.atualizar()

    def prev_ver(self):
        vers = self.grupos[self.idx_grupo].get("a_verificar", [])
        if vers:
            self.idx_ver = (self.idx_ver - 1) % len(vers)
            self.atualizar()

    def next_ver(self):
        vers = self.grupos[self.idx_grupo].get("a_verificar", [])
        if vers:
            self.idx_ver = (self.idx_ver + 1) % len(vers)
            self.atualizar()

    def eliminar_marcados(self):
        if not self.marcados:
            messagebox.showinfo("Eliminar", "Nenhum ficheiro marcado para eliminar.")
            return
        if not messagebox.askyesno("Eliminar", f"Eliminar {len(self.marcados)} ficheiros marcados?\nEsta ação é irreversível!"):
            return
        erros = []
        eliminados = 0
        for path in list(self.marcados):
            try:
                os.remove(path)
                self.marcados.discard(path)
                eliminados += 1
            except Exception as e:
                erros.append(f"{path}: {e}")
        msg = f"{eliminados} ficheiros eliminados."
        if erros:
            msg += "\n\nErros:\n" + "\n".join(erros)
        messagebox.showinfo("Eliminação concluída", msg)
        self.atualizar()

if __name__ == "__main__":
    import sys
    # O diálogo de ficheiro deve ser feito ANTES de criar o Tk principal!
    root = tk.Tk()
    root.withdraw()
    relatorio_path = filedialog.askopenfilename(
        title="Escolhe o relatorio_duplicados_imagens.json",
        filetypes=[("JSON files", "*.json")]
    )
    root.destroy()
    if not relatorio_path:
        messagebox.showerror("Erro", "Nenhum relatório selecionado.")
        input("Pressione Enter para sair...")
        sys.exit(1)

    app = VisualizadorDuplicados(relatorio_path)
    app.mainloop()
