import os
import shutil
from analise import obter_tipo, criar_pasta
from config import MESES_PT

def obter_pasta_destino(base, categoria, data, ext):
    tipo = obter_tipo(ext)
    if data:
        ano = str(data.year)
        mes = MESES_PT[data.month - 1]
        pasta = os.path.join(base, tipo, categoria, ano, mes)
    else:
        pasta = os.path.join(base, tipo, categoria, "sem_data")
    criar_pasta(pasta)
    return pasta
