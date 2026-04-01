from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2
import os

print("Baixando o modelo da internet...")

model = MobileNetV2(weights='imagenet', include_top=False, pooling='avg')

# CORREÇÃO: Adicionada a extensão .keras
caminho_salvamento = 'modelo_mobilenetv2_local.keras'
model.save(caminho_salvamento)

print(f"Modelo salvo com sucesso no arquivo: {os.path.abspath(caminho_salvamento)}")
