import os
import json

def gerar_relatorio_json_multimidia(originais, duplicados, a_verificar, destino):
    """
    Gera três relatórios separados:
    - relatorio_duplicados_imagens.json
    - relatorio_duplicados_videos.json
    - relatorio_duplicados_audios.json

    Cada relatório só inclui grupos com duplicados e/ou a_verificar da categoria correspondente.
    """
    EXT_IMAGENS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.raw', '.heic')
    EXT_VIDEOS  = ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.3gp', '.mpeg', '.mpg')
    EXT_AUDIOS  = ('.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.wma', '.amr', '.aiff')

    def categoria(ext):
        if ext in EXT_IMAGENS:
            return "imagens"
        elif ext in EXT_VIDEOS:
            return "videos"
        elif ext in EXT_AUDIOS:
            return "audios"
        else:
            return None

    relatorio_cat = {
        "imagens": [],
        "videos": [],
        "audios": [],
    }

    dup_map = {}
    verif_map = {}

    # Mapear duplicados e a_verificar por original
    for org_path, dup_path, _ in duplicados:
        dup_map.setdefault(org_path, []).append(dup_path)
    for org_path, dup_path, _ in a_verificar:
        verif_map.setdefault(org_path, []).append(dup_path)

    for org_path, org_info in originais.items():
        ext = os.path.splitext(org_path)[1].lower()
        cat = categoria(ext)
        if not cat:
            continue
        dups = [p for p in dup_map.get(org_path, []) if categoria(os.path.splitext(p)[1].lower()) == cat]
        vers = [p for p in verif_map.get(org_path, []) if categoria(os.path.splitext(p)[1].lower()) == cat]
        if dups or vers:
            relatorio_cat[cat].append({
                "original": org_path,
                "nome": os.path.basename(org_path),
                "duplicados": [{"caminho": p, "nome": os.path.basename(p)} for p in dups],
                "a_verificar": [{"caminho": p, "nome": os.path.basename(p)} for p in vers]
            })

    if relatorio_cat["imagens"]:
        with open(os.path.join(destino, "relatorio_duplicados_imagens.json"), "w", encoding="utf-8") as f:
            json.dump(relatorio_cat["imagens"], f, indent=2, ensure_ascii=False)
    if relatorio_cat["videos"]:
        with open(os.path.join(destino, "relatorio_duplicados_videos.json"), "w", encoding="utf-8") as f:
            json.dump(relatorio_cat["videos"], f, indent=2, ensure_ascii=False)
    if relatorio_cat["audios"]:
        with open(os.path.join(destino, "relatorio_duplicados_audios.json"), "w", encoding="utf-8") as f:
            json.dump(relatorio_cat["audios"], f, indent=2, ensure_ascii=False)
