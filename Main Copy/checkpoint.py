import os
import json
from config import CHECKPOINT_FILE

def guardar_checkpoint(analisados, i, ficheiros):
    # Converte datetimes para string (caso existam)
    def safe(obj):
        if isinstance(obj, dict):
            return {k: safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [safe(v) for v in obj]
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return obj
    data = {
        "progresso": i,
        "analisados": safe(analisados),
        "ficheiros": ficheiros
    }
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def carregar_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados["analisados"], dados["progresso"], dados["ficheiros"]
    return [], 0, []

def apagar_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
