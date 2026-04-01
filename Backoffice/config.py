import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_DIR = os.path.join(BASE_DIR, 'instance')
    os.makedirs(DB_DIR, exist_ok=True)
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-unsecure-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', f'sqlite:///{os.path.join(DB_DIR, "database.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuracoes da IA com caminhos base no diretorio do backoffice
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PASTA_IMAGENS = os.path.join(BASE_DIR, 'imagens_salvas')
    ARQUIVO_INDICE = os.path.join(BASE_DIR, 'meu_cerebro_visual.index')
    TAMANHO_VETOR = 1280
