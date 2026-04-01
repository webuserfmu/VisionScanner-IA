import os
import numpy as np
from PIL import Image
import io
import faiss
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing import image
from config import Config

tamanho_do_vetor = Config.TAMANHO_VETOR
ARQUIVO_INDICE = Config.ARQUIVO_INDICE

# Constroi o caminho absoluto para o modelo Keras (localizado em ../, ou seja, Backoffice)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'modelo_mobilenetv2_local.keras')

print(f"Carregando Modelo de IA de {MODEL_PATH} ...")
try:
    model = load_model(MODEL_PATH)
except Exception as e:
    print(f"Erro ao carregar modelo: {e}")
    model = None

if os.path.exists(ARQUIVO_INDICE):
    index = faiss.read_index(ARQUIVO_INDICE)
    contador_faiss = index.ntotal
else:
    index = faiss.IndexFlatL2(tamanho_do_vetor)
    contador_faiss = 0

def extrair_vetor(caminho_ou_bytes):
    if not model:
        raise Exception("Modelo de IA não carregado.")
        
    if isinstance(caminho_ou_bytes, bytes):
        img = Image.open(io.BytesIO(caminho_ou_bytes)).convert('RGB')
    else:
        img = Image.open(caminho_ou_bytes).convert('RGB')
        
    img = img.resize((224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    return np.array(model.predict(x), dtype=np.float32)

def zerar_indice():
    global index, contador_faiss
    index = faiss.IndexFlatL2(tamanho_do_vetor)
    contador_faiss = 0
    faiss.write_index(index, ARQUIVO_INDICE)

def adicionar_ao_indice(vetor):
    global index, contador_faiss
    index.add(vetor)
    contador_faiss += 1
    faiss.write_index(index, ARQUIVO_INDICE)
    return contador_faiss - 1

def buscar_no_indice(vetor, k=6):
    global index
    if index.ntotal == 0:
        return [], []
    distancias, indices = index.search(vetor, k)
    return distancias, indices

def get_total_imagens():
    global index
    return index.ntotal
