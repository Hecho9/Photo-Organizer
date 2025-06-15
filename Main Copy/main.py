print("Iniciando main.py...")

try:
    from interface import App
    print("Importação de App da interface.py realizada com sucesso.")
except Exception as e:
    print("Erro ao importar App:", e)
    import traceback
    traceback.print_exc()
    print("O programa será encerrado devido ao erro acima.")
    exit(1)

if __name__ == "__main__":
    print("Instanciando App...")
    app = App()
    print("App instanciado. Iniciando mainloop()...")
    app.mainloop()
    print("mainloop() finalizado. Programa encerrado.")
