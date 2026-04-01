import os
import json
import smtplib
from email.mime.text import MIMEText
from cryptography.fernet import Fernet

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO_CHAVE = os.path.join(BASE_DIR, 'secret.key')
ARQUIVO_CONFIG_ENC = os.path.join(BASE_DIR, 'config.enc')

def obter_credenciais():
    try:
        if not os.path.exists(ARQUIVO_CHAVE) or not os.path.exists(ARQUIVO_CONFIG_ENC):
            print("AVISO: Arquivos de configuracao encriptados nao encontrados.")
            return {}

        with open(ARQUIVO_CHAVE, 'rb') as k:
            chave = k.read()
        
        cipher = Fernet(chave)
        
        with open(ARQUIVO_CONFIG_ENC, 'rb') as c:
            dados_encriptados = c.read()
            
        dados_json = cipher.decrypt(dados_encriptados).decode('utf-8')
        creds = json.loads(dados_json)
        
        return {
            'MEU_EMAIL': creds.get('EMAIL', ''),
            'MINHA_SENHA': creds.get('SENHA', ''),
            'SERVIDOR_SMTP': creds.get('SMTP_SERVER', 'smtp.gmail.com'),
            'PORTA_SMTP': int(creds.get('SMTP_PORT', 587))
        }
    except Exception as e:
        print(f"Erro ao descriptografar configuracoes: {e}")
        return {}

def enviar_email_real(destinatario, codigo):
    creds = obter_credenciais()
    
    if not creds or not creds.get('MEU_EMAIL') or not creds.get('MINHA_SENHA'):
        print("Email nao configurado no config.enc. Impossivel enviar.")
        return False
        
    try:
        msg = MIMEText(f"""
        Olá!
        
        Recebemos um pedido de recuperação de senha.
        
        SEU CÓDIGO DE VALIDAÇÃO: {codigo}
        
        Se não foi você, ignore este email.
        """)
        
        msg['Subject'] = "Recuperacao de Senha - IA Scanner"
        msg['From'] = creds['MEU_EMAIL']
        msg['To'] = destinatario

        with smtplib.SMTP(creds['SERVIDOR_SMTP'], creds['PORTA_SMTP']) as server:
            server.starttls()
            server.login(creds['MEU_EMAIL'], creds['MINHA_SENHA'])
            server.send_message(msg)
            
        print(f"Email enviado para {destinatario}")
        return True
    except Exception as e:
        print(f"ERRO AO ENVIAR EMAIL: {e}")
        return False
