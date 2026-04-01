import os
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from cryptography.fernet import Fernet

from models import User, Product
from extensions import db
from services.ai_service import zerar_indice

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/usuarios', methods=['GET', 'POST'])
@jwt_required()
def gerir_usuarios():
    admin = get_jwt_identity()
    admin_user = User.query.filter_by(login=admin).first()
    
    if not admin_user or not admin_user.perm_admin:
        return jsonify({'erro': 'Acesso negado'}), 403

    if request.method == 'GET':
        usuarios = User.query.all()
        return jsonify([{
            'login': u.login, 
            'nome': u.nome, 
            'email': u.email or '',
            'limite_diario': u.limite_diario,
            'uso_hoje': u.uso_hoje_count,
            'perms': {
                'search': u.perm_search,
                'add': u.perm_add,
                'del': u.perm_del,
                'admin': u.perm_admin
            }
        } for u in usuarios])

    if request.method == 'POST':
        dados = request.json
        novo_login = dados.get('login')
        senha = dados.get('senha')
        
        user_alvo = User.query.filter_by(login=novo_login).first()
        
        if not user_alvo:
            if not senha:
                return jsonify({'erro': 'Senha obrigatoria para novo usuario'}), 400
            user_alvo = User(login=novo_login)
            db.session.add(user_alvo)
        
        if senha and len(senha) > 0:
            user_alvo.senha_hash = generate_password_hash(senha)
            
        user_alvo.nome = dados.get('nome')
        user_alvo.email = dados.get('email')
        user_alvo.limite_diario = int(dados.get('limite_diario', 0))
        user_alvo.perm_search = dados.get('perm_search', False)
        user_alvo.perm_add = dados.get('perm_add', False)
        user_alvo.perm_del = dados.get('perm_del', False)
        user_alvo.perm_admin = dados.get('perm_admin', False)
        
        db.session.commit()
        return jsonify({'ok': True})

@admin_bp.route('/usuarios/<login_alvo>', methods=['DELETE'])
@jwt_required()
def apagar_usuario(login_alvo):
    admin = get_jwt_identity()
    admin_user = User.query.filter_by(login=admin).first()
    
    if not admin_user or not admin_user.perm_admin: return jsonify({'erro': 'Acesso negado'}), 403
    if login_alvo == admin: return jsonify({'erro': 'Não pode se apagar'}), 400
    
    user_alvo = User.query.filter_by(login=login_alvo).first()
    if user_alvo:
        # Salvaguarda: Não permitir a exclusão térmica se for o último Admin
        if user_alvo.perm_admin:
            admins_restantes = User.query.filter(User.perm_admin == True, User.login != login_alvo).count()
            if admins_restantes < 1:
                return jsonify({'erro': 'Não é possível eliminar o último Administrador do sistema.'}), 400

        db.session.delete(user_alvo)
        db.session.commit()
        return jsonify({'ok': True})
    return jsonify({'erro': 'Não encontrado'}), 404

@admin_bp.route('/zerar', methods=['POST'])
@jwt_required()
def zerar():
    login = get_jwt_identity()
    user = User.query.filter_by(login=login).first()
    
    if not user or not user.perm_del: return jsonify({'erro': 'Sem permissão'}), 403

    zerar_indice()
    
    Product.query.delete()
    db.session.commit()
    
    return jsonify({'ok': True})


@admin_bp.route('/email/config', methods=['POST'])
@jwt_required()
def configurar_smtp():
    login = get_jwt_identity()
    user = User.query.filter_by(login=login).first()
    if not user or not user.perm_admin:
        return jsonify({'erro': 'Acesso negado'}), 403

    dados = request.json
    email = dados.get('email', '').strip()
    senha = dados.get('senha', '').strip()
    smtp = dados.get('smtp', 'smtp.gmail.com').strip()
    porta = str(dados.get('porta', '587')).strip()

    if not email or not senha:
        return jsonify({'erro': 'E-mail e Senha de APP são obrigatórios'}), 400

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ARQUIVO_CHAVE = os.path.join(BASE_DIR, 'secret.key')
    ARQUIVO_CONFIG = os.path.join(BASE_DIR, 'config.enc')

    try:
        if not os.path.exists(ARQUIVO_CHAVE):
            chave = Fernet.generate_key()
            with open(ARQUIVO_CHAVE, 'wb') as f:
                f.write(chave)

        with open(ARQUIVO_CHAVE, 'rb') as f:
            chave = f.read()

        cipher = Fernet(chave)
        dados_smtp = {"EMAIL": email, "SENHA": senha, "SMTP_SERVER": smtp, "SMTP_PORT": int(porta)}
        dados_json = json.dumps(dados_smtp).encode('utf-8')
        encriptados = cipher.encrypt(dados_json)

        with open(ARQUIVO_CONFIG, 'wb') as f:
            f.write(encriptados)

        # Atualiza a memoria local do módulo email_service em runtime (Opcional, mas seguro)
        return jsonify({'mensagem': 'Configuração gravada no cofre com sucesso!'})

    except Exception as e:
        return jsonify({'erro': f'Falha interna ao criptografar: {str(e)}'}), 500
