import os
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import EXTENSOES, CHECKPOINT_INTERVAL
from analise import analisar_ficheiro, listar_ficheiros
from organizador import obter_pasta_destino
from checkpoint import guardar_checkpoint, carregar_checkpoint, apagar_checkpoint
from duplicados import identificar_duplicados_com_data_mais_antiga, verificar_se_burst_ou_crop
from relatorio import gerar_relatorio_json_multimidia

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Organizador de Ficheiros")
        self.geometry("650x260")
        self.resizable(False, False)
        self.configure(bg="#f8f9fa")

        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
        else:
            style.theme_use(style.theme_names()[0])

        # Estilo flat para botões ttk
        style.configure("TButton",
            relief="flat",
            borderwidth=0,
            padding=10,
            background="#e0e0e0",
            foreground="#222",
            font=("Segoe UI", 11),
        )
        style.map("TButton",
            background=[("active", "#d1eaff"), ("pressed", "#90caf9")],
            foreground=[("disabled", "#aaa"), ("active", "#222")]
        )

        # Barra de progresso moderna
        style.configure("TProgressbar", thickness=8, background="#007bff")

        self.progress = ttk.Progressbar(self, orient='horizontal', length=600, mode='determinate', style="TProgressbar")
        self.progress.pack(pady=20)

        self.label = ttk.Label(self, text="Selecione as pastas e clique em 'Começar'", background="#f8f9fa", font=("Segoe UI", 11))
        self.label.pack(pady=(0, 10))

        self.btn_frame = tk.Frame(self, bg="#f8f9fa")
        self.btn_frame.pack(pady=10)

        self.pause_btn = ttk.Button(self.btn_frame, text="Pausar", command=self.pausar)
        self.resume_btn = ttk.Button(self.btn_frame, text="Retomar", command=self.retomar)
        self.cancel_btn = ttk.Button(self.btn_frame, text="Cancelar", command=self.cancelar)
        self.start_btn = ttk.Button(self, text="Começar", command=self.selecionar_pastas)

        self.paused = threading.Event()
        self.paused.clear()
        self.cancelled = False
        self.origem = None
        self.destino = None

        self.show_state("init")

    def show_state(self, state):
        # Esconde todos os botões primeiro
        for btn in [self.pause_btn, self.resume_btn, self.cancel_btn]:
            btn.pack_forget()
        self.start_btn.pack_forget()
        if state == "init":
            self.start_btn.pack(pady=10)
        elif state == "running":
            self.pause_btn.pack(side='left', padx=8)
            self.cancel_btn.pack(side='left', padx=8)
        elif state == "paused":
            self.resume_btn.pack(side='left', padx=8)
            self.cancel_btn.pack(side='left', padx=8)
        elif state == "done":
            self.start_btn.pack(pady=10)

    def selecionar_pastas(self):
        self.origem = filedialog.askdirectory(title="Selecione a pasta de origem")
        if not self.origem:
            messagebox.showwarning("Atenção", "Nenhuma pasta de origem selecionada.")
            return
        self.destino = filedialog.askdirectory(title="Selecione a pasta de destino")
        if not self.destino:
            messagebox.showwarning("Atenção", "Nenhuma pasta de destino selecionada.")
            return
        self.show_state("running")
        self.progress["value"] = 0
        self.label.config(text="Iniciando análise...")
        threading.Thread(target=self.run_analise, daemon=True).start()

    def run_analise(self):
        try:
            analisados, inicio, ficheiros = [], 0, []
            if os.path.exists("analise_checkpoint.json"):
                if messagebox.askyesno("Retomar?", "Foi detetado um progresso anterior. Quer retomar do último checkpoint?"):
                    analisados, inicio, ficheiros = carregar_checkpoint()
                else:
                    apagar_checkpoint()
            if not ficheiros:
                ficheiros = listar_ficheiros(self.origem, EXTENSOES)
            total = len(ficheiros)
            if total == 0:
                self.label.config(text="Nenhum ficheiro encontrado.")
                self.show_state("init")
                return

            self.progress["maximum"] = total
            for i, path in enumerate(ficheiros[inicio:], inicio+1):
                if self.cancelled:
                    self.label.config(text="Processo cancelado pelo utilizador.")
                    self.show_state("done")
                    return
                while self.paused.is_set():
                    self.label.config(text="Pausado... Aguarde.")
                    time.sleep(0.1)
                analisados.append(analisar_ficheiro(path))
                self.progress["value"] = i
                self.label.config(text=f"Progresso: {i}/{total} ficheiros analisados...")
                self.update_idletasks()
                if i % CHECKPOINT_INTERVAL == 0:
                    guardar_checkpoint(analisados, i, ficheiros)
            guardar_checkpoint(analisados, total, ficheiros)  # Salva no fim

            count_original = sum(1 for f in analisados if f["categoria_data"] == "original")
            count_filesystem = sum(1 for f in analisados if f["categoria_data"] == "filesystem")
            count_semdata = sum(1 for f in analisados if f["categoria_data"] == "semdata")

            originais, duplicados = identificar_duplicados_com_data_mais_antiga(analisados)
            dados_map = {f['path']: f for f in analisados}
            duplicados_filtrados, a_verificar = verificar_se_burst_ou_crop(originais, duplicados, dados_map)

            # --- GERA RELATÓRIO JSON ---
            gerar_relatorio_json_multimidia(originais, duplicados_filtrados, a_verificar, self.destino)

            msg = (
                f"Total de ficheiros: {total}\n"
                f"EXIF originais: {count_original}, Apenas disco: {count_filesystem}, Sem data: {count_semdata}\n"
                f"Originais finais: {len(originais)}\n"
                f"Duplicados finais: {len(duplicados_filtrados)}\n"
                f"A verificar: {len(a_verificar)}\n"
                f"Relatório: relatorio_duplicados.json gerado no destino."
            )
            self.label.config(text="A copiar e organizar ficheiros...")
            self.progress["value"] = 0
            self.progress["maximum"] = len(originais) + len(duplicados_filtrados) + len(a_verificar)
            self.update_idletasks()
            self.organizar_e_copiar(originais, duplicados_filtrados, analisados, self.destino, a_verificar)
            self.label.config(text="Concluído!\n" + msg)
            self.show_state("done")
            apagar_checkpoint()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.label.config(text="Erro detectado. Veja o terminal.")
            self.show_state("done")

    def organizar_e_copiar(self, originais, duplicados, analisados, destino_base, a_verificar=None):
        if not destino_base:
            self.label.config(text="Operação de cópia cancelada.")
            return

        dados_map = {f['path']: f for f in analisados}
        total = len(originais) + len(duplicados) + (len(a_verificar) if a_verificar else 0)
        current = 0

        for path, dados in originais.items():
            if self.cancelled:
                return
            while self.paused.is_set():
                self.label.config(text="Pausado... Aguarde.")
                time.sleep(0.1)
            data = dados['data']
            ext = dados['ext']
            pasta_destino = obter_pasta_destino(destino_base, "unicos", data, ext)
            nome = os.path.basename(dados['path'])
            destino_final = os.path.join(pasta_destino, nome)
            contador = 1
            while os.path.exists(destino_final):
                nome_base, ext_file = os.path.splitext(nome)
                destino_final = os.path.join(pasta_destino, f"{nome_base}_{contador}{ext_file}")
                contador += 1
            import shutil
            shutil.copy2(dados['path'], destino_final)
            current += 1
            self.progress["value"] = current
            self.label.config(text=f"[Originais] Copiado {current}/{total} ficheiros...")
            self.update_idletasks()

        lista_duplicados = duplicados
        if a_verificar:
            set_a_verificar = set((o, d) for o, d, _ in a_verificar)
            lista_duplicados = [item for item in duplicados if (item[0], item[1]) not in set_a_verificar]

        for org_path, dup_path, _ in lista_duplicados:
            if self.cancelled:
                return
            while self.paused.is_set():
                self.label.config(text="Pausado... Aguarde.")
                time.sleep(0.1)
            data = dados_map.get(org_path, {}).get('data')
            ext = dados_map.get(dup_path, {}).get('ext') or dados_map.get(org_path, {}).get('ext', "")
            pasta_destino = obter_pasta_destino(destino_base, "duplicados", data, ext)
            nome = os.path.basename(dup_path)
            destino_final = os.path.join(pasta_destino, nome)
            contador = 1
            while os.path.exists(destino_final):
                nome_base, ext_file = os.path.splitext(nome)
                destino_final = os.path.join(pasta_destino, f"{nome_base}_dup{contador}{ext_file}")
                contador += 1
            import shutil
            shutil.copy2(dup_path, destino_final)
            current += 1
            self.progress["value"] = current
            self.label.config(text=f"[Duplicados] Copiado {current}/{total} ficheiros...")
            self.update_idletasks()

        if a_verificar:
            for org_path, dup_path, _ in a_verificar:
                if self.cancelled:
                    return
                while self.paused.is_set():
                    self.label.config(text="Pausado... Aguarde.")
                    time.sleep(0.1)
                data = dados_map.get(org_path, {}).get('data')
                ext = dados_map.get(dup_path, {}).get('ext') or dados_map.get(org_path, {}).get('ext', "")
                pasta_destino = obter_pasta_destino(destino_base, "a_verificar", data, ext)
                nome = os.path.basename(dup_path)
                destino_final = os.path.join(pasta_destino, nome)
                contador = 1
                while os.path.exists(destino_final):
                    nome_base, ext_file = os.path.splitext(nome)
                    destino_final = os.path.join(pasta_destino, f"{nome_base}_dup{contador}{ext_file}")
                    contador += 1
                import shutil
                shutil.copy2(dup_path, destino_final)
                current += 1
                self.progress["value"] = current
                self.label.config(text=f"[A verificar] Copiado {current}/{total} ficheiros...")
                self.update_idletasks()

    def pausar(self):
        self.paused.set()
        self.show_state("paused")
        self.label.config(text="Pausado...")

    def retomar(self):
        self.paused.clear()
        self.show_state("running")
        self.label.config(text="Retomando...")

    def cancelar(self):
        if messagebox.askyesno("Cancelar", "Tem a certeza que deseja cancelar?"):
            self.cancelled = True
            self.show_state("done")
            self.label.config(text="Cancelado pelo utilizador.")
        else:
            self.label.config(text="Processo em execução.")
