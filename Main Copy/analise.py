import os
import hashlib
from datetime import datetime
from config import EXT_IMAGENS, EXT_VIDEOS, EXT_AUDIOS, HAS_IMAGEHASH

def obter_tipo(ext):
    ext = ext.lower()
    if ext in EXT_IMAGENS:
        return "imagens"
    elif ext in EXT_VIDEOS:
        return "videos"
    elif ext in EXT_AUDIOS:
        return "audios"
    else:
        return "outros"

def obter_datas(path):
    datas = []
    try:
        import pyexiv2
        metadata = pyexiv2.ImageMetadata(path)
        metadata.read()
        if 'Exif.Image.DateTime' in metadata:
            dt = metadata['Exif.Image.DateTime'].value
            if isinstance(dt, str):
                dt = datetime.strptime(dt, '%Y:%m:%d %H:%M:%S')
            datas.append(('exif_pyexiv2', dt))
    except Exception:
        pass
    try:
        import rawpy
        raw = rawpy.imread(path)
        if hasattr(raw, 'shooting_timestamp') and raw.shooting_timestamp:
            dt = raw.shooting_timestamp
            if isinstance(dt, float):
                dt = datetime.fromtimestamp(dt)
            datas.append(('rawpy', dt))
    except Exception:
        pass
    try:
        import exifread
        with open(path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal")
            dt = tags.get("EXIF DateTimeOriginal")
            if dt:
                dtv = str(dt)
                datas.append(('exif_exifread', datetime.strptime(dtv, '%Y:%m:%d %H:%M:%S')))
    except Exception:
        pass
    try:
        from PIL import Image
        img = Image.open(path)
        if hasattr(img, '_getexif'):
            exif = img._getexif()
            if exif:
                for tag in [36867, 36868, 306]:
                    if tag in exif:
                        dtv = exif[tag]
                        if isinstance(dtv, bytes):
                            dtv = dtv.decode(errors='ignore')
                        datas.append(('exif_pillow', datetime.strptime(dtv[:19], '%Y:%m:%d %H:%M:%S')))
    except Exception:
        pass
    try:
        from pymediainfo import MediaInfo
        media = MediaInfo.parse(path)
        for track in media.tracks:
            for field in ['tagged_date', 'encoded_date', 'recorded_date']:
                val = getattr(track, field, None)
                if val:
                    try:
                        dtv = val.replace('T', ' ').replace('Z', '').replace('+00:00','')
                        datas.append(('mediainfo', datetime.strptime(dtv[:19], '%Y-%m-%d %H:%M:%S')))
                    except Exception:
                        pass
    except Exception:
        pass
    try:
        from hachoir.parser import createParser
        from hachoir.metadata import extractMetadata
        parser = createParser(path)
        if parser:
            with parser:
                metadata = extractMetadata(parser)
                if metadata:
                    for key in ["creation_date", "date", "encoded_date", "file_create_date"]:
                        if metadata.has(key):
                            val = metadata.get(key)
                            try:
                                datas.append(('hachoir', datetime.strptime(str(val)[:19], '%Y-%m-%d %H:%M:%S')))
                            except Exception:
                                pass
    except Exception:
        pass
    try:
        ts = os.path.getmtime(path)
        datas.append(('filesystem_mtime', datetime.fromtimestamp(ts)))
    except Exception:
        pass
    try:
        ts = os.path.getctime(path)
        datas.append(('filesystem_ctime', datetime.fromtimestamp(ts)))
    except Exception:
        pass
    import re
    nome = os.path.basename(path)
    match_hora = re.search(r'(20\d{2})[-_]?(\d{2})[-_]?(\d{2})[^\d]?(\d{2})[-_]?(\d{2})[-_]?(\d{2})', nome)
    if match_hora:
        try:
            dt = f"{match_hora[1]}-{match_hora[2]}-{match_hora[3]} {match_hora[4]}:{match_hora[5]}:{match_hora[6]}"
            datas.append(('filename', datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')))
        except Exception:
            pass
    match = re.search(r'(20\d{2})[-_]?(\d{2})[-_]?(\d{2})', nome)
    if match:
        try:
            dt = f"{match[1]}-{match[2]}-{match[3]} 00:00:00"
            datas.append(('filename', datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')))
        except Exception:
            pass
    datas = [(origem, dt) for origem, dt in datas if dt and dt.year > 1970]
    return datas

def classificar_data(datas):
    if not datas:
        return 'semdata', None
    datas.sort(key=lambda x: x[1])
    origem, dt = datas[0]
    if origem.startswith('exif'):
        return 'original', dt
    elif origem in ('rawpy', 'mediainfo', 'hachoir'):
        return origem, dt
    elif origem.startswith('filesystem'):
        return 'filesystem', dt
    elif origem == 'filename':
        return 'filename', dt
    return origem, dt

def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def get_phash(path):
    if not HAS_IMAGEHASH:
        return None
    try:
        from PIL import Image
        import imagehash
        with Image.open(path) as img:
            return str(imagehash.phash(img))
    except Exception:
        return None

def analisar_ficheiro(path):
    datas = obter_datas(path)
    categoria, dt = classificar_data(datas)
    tamanho = os.path.getsize(path)
    ext = os.path.splitext(path)[1].lower()
    hashmd5 = md5(path)
    hashsha = sha256(path)
    phash = get_phash(path) if HAS_IMAGEHASH and ext in EXT_IMAGENS else None
    return {
        "path": path,
        "categoria_data": categoria,
        "data": dt,
        "tamanho": tamanho,
        "md5": hashmd5,
        "sha256": hashsha,
        "phash": phash,
        "ext": ext
    }

def listar_ficheiros(pasta, extensoes):
    ficheiros = []
    for dirpath, _, files in os.walk(pasta):
        for f in files:
            if f.lower().endswith(extensoes):
                ficheiros.append(os.path.join(dirpath, f))
    return ficheiros

def criar_pasta(caminho):
    if not os.path.exists(caminho):
        os.makedirs(caminho)
