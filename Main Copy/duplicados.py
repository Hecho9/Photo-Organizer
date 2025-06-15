from collections import defaultdict, deque
from datetime import datetime
import os
from config import PHASH_MAX_DIST, PHASH_BURST_LIMITE

TAMANHO_MIN_ORIGINAL = 30 * 1024  # 30 KB

def phash_distance(phash1, phash2):
    try:
        return bin(int(phash1, 16) ^ int(phash2, 16)).count('1')
    except Exception:
        return 100

def prioridade_data(categoria):
    ordem = {'original': 0, 'rawpy': 1, 'mediainfo': 2, 'hachoir': 3, 'filesystem': 4, 'filename': 5, 'semdata': 6}
    return ordem.get(categoria, 99)

def identificar_duplicados_com_data_mais_antiga(lista):
    grupos = defaultdict(list)
    path_to_ficheiro = {}
    phashs = [(f["path"], f.get("phash"), f.get("data"), f.get("categoria_data", ""), f.get("tamanho", 0)) for f in lista if f.get("phash")]
    for f in lista:
        path_to_ficheiro[f["path"]] = f
        grupos[("hash", f["md5"], f["sha256"])].append(f["path"])
    for path, phash, *_ in phashs:
        grupos[("phash", phash)].append(path)
    for i in range(len(phashs)):
        p1, h1, *_ = phashs[i]
        for j in range(i+1, len(phashs)):
            p2, h2, *_ = phashs[j]
            if phash_distance(h1, h2) <= PHASH_MAX_DIST:
                grupos[("phash_similar", min(h1, h2), max(h1, h2))].extend([p1, p2])

    vizinhos = defaultdict(set)
    for paths in grupos.values():
        for i in range(len(paths)):
            for j in range(i+1, len(paths)):
                vizinhos[paths[i]].add(paths[j])
                vizinhos[paths[j]].add(paths[i])

    visitados = set()
    originais = {}
    duplicados = []

    for path in path_to_ficheiro:
        if path in visitados:
            continue
        grupo = []
        fila = deque([path])
        while fila:
            atual = fila.popleft()
            if atual in visitados:
                continue
            visitados.add(atual)
            grupo.append(atual)
            for viz in vizinhos[atual]:
                if viz not in visitados:
                    fila.append(viz)
        if not grupo:
            continue
        grupo_ficheiros = [path_to_ficheiro[p] for p in grupo]
        grupo_ficheiros.sort(key=lambda x: (
            prioridade_data(x.get("categoria_data", "")),
            x.get("data") if x.get("data") else datetime.max,
            -x.get("tamanho", 0)
        ))
        # Garante que thumbnails nunca são originais
        for f in grupo_ficheiros:
            if f.get("tamanho", 0) >= TAMANHO_MIN_ORIGINAL:
                original = f
                break
        else:
            original = grupo_ficheiros[0]
        originais[original["path"]] = original
        for dup in grupo_ficheiros:
            if dup["path"] == original["path"]:
                continue
            duplicados.append((original["path"], dup["path"], "Duplicado"))

    return originais, duplicados

def verificar_se_burst_ou_crop(originais, duplicados, dados_map):
    novos_duplicados = []
    a_verificar = []
    for org_path, dup_path, metodo in duplicados:
        org = dados_map.get(org_path)
        dup = dados_map.get(dup_path)
        if not org or not dup or not org.get("phash") or not dup.get("phash"):
            novos_duplicados.append((org_path, dup_path, metodo))
            continue
        # Só permite burst/crop se as extensões forem exatamente iguais
        ext_org = os.path.splitext(org_path)[1].lower()
        ext_dup = os.path.splitext(dup_path)[1].lower()
        if ext_org == ext_dup:
            dist = phash_distance(org["phash"], dup["phash"])
            if dist <= PHASH_BURST_LIMITE:
                data_org = org.get('data') or datetime.max
                data_dup = dup.get('data') or datetime.max
                diff_segundos = abs((data_dup - data_org).total_seconds())
                if diff_segundos < 10:
                    a_verificar.append((org_path, dup_path, "A verificar (possível burst/crop)"))
                    continue
        # Se chegou aqui, não é burst/crop, é duplicado normal
        novos_duplicados.append((org_path, dup_path, metodo))
    return novos_duplicados, a_verificar
