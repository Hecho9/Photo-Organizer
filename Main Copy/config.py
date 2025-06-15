# ---- CONFIG ----
EXTENSOES = (
    '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.raw', '.heic',
    '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.3gp', '.mpeg', '.mpg',
    '.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.wma', '.amr', '.aiff'
)
EXT_IMAGENS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.raw', '.heic')
EXT_VIDEOS = ('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.3gp', '.mpeg', '.mpg')
EXT_AUDIOS = ('.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.wma', '.amr', '.aiff')
MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

CHECKPOINT_FILE = "analise_checkpoint.json"
CHECKPOINT_INTERVAL = 1000  # ajustar se quiser

PHASH_MAX_DIST = 5
PHASH_BURST_LIMITE = 3

try:
    import imagehash
    from PIL import Image
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False
