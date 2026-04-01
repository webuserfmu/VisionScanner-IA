import json
from cryptography.fernet import Fernet
import os

# Nomes dos arquivos
ARQUIVO_CHAVE = 'secret.key'
ARQUIVO_CONFIG = 'config.enc'

def gerar_chave():
    """Gera uma chave de criptografia se não existir."""
    if not os.path.exists(ARQUIVO_CHAVE):
        chave = Fernet.generate_key()
        with open(ARQUIVO_CHAVE, 'wb') as chave_file:
            chave_file.write(chave)
        print(f"✅ Chave de segurança criada: {ARQUIVO_CHAVE}")
    else:
        print(f"ℹ️ Usando chave existente em {ARQUIVO_CHAVE}")

def criptografar_dados():
    gerar_chave()
    
    # Carrega a chave
    with open(ARQUIVO_CHAVE, 'rb') as chave_file:
        chave = chave_file.read()
    
    cipher = Fernet(chave)
    
    print("\n--- CONFIGURAÇÃO DE EMAIL SEGURO ---")
    email = input("Digite o seu Email (Gmail/Outlook): ").strip()
    senha = input("Digite a SENHA DE APP (não a senha normal): ").strip()
    smtp = input("Servidor SMTP (ex: smtp.gmail.com): ").strip() or "smtp.gmail.com"
    porta = input("Porta SMTP (ex: 587): ").strip() or "587"
    
    dados = {
        "EMAIL": email,
        "SENHA": senha,
        "SMTP_SERVER": smtp,
        "SMTP_PORT": int(porta)
    }
    
    # Transforma em JSON e depois encripta
    dados_json = json.dumps(dados).encode('utf-8')
    dados_encriptados = cipher.encrypt(dados_json)
    
    with open(ARQUIVO_CONFIG, 'wb') as f:
        f.write(dados_encriptados)
        
    print(f"\n✅ Configuração salva e encriptada em '{ARQUIVO_CONFIG}'!")
    print("Agora você pode apagar as senhas do código principal.")

if __name__ == "__main__":
    criptografar_dados()