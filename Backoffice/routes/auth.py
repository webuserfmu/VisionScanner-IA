import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from extensions import db
from services.email_service import enviar_email_real

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    dados = request.json
    usuario_login = dados.get('usuario')
    senha = dados.get('senha')
    
    user = User.query.filter_by(login=usuario_login).first()
    
    if user and check_password_hash(user.senha_hash, senha):
        access_token = create_access_token(identity=user.login)
        return jsonify({
            'sucesso': True, 
            'usuario': user.nome, 
            'perms': {
                'search': user.perm_search,
                'add': user.perm_add,
                'del': user.perm_del,
                'admin': user.perm_admin
            },
            'login': user.login,
            'email': user.email,
            'access_token': access_token
        })
    return jsonify({'sucesso': False, 'mensagem': 'Login inválido'}), 401


@auth_bp.route('/perfil/atualizar', methods=['POST'])
@jwt_required()
def atualizar_perfil():
    dados = request.json
    login = get_jwt_identity()
    
    senha_atual = dados.get('senha_atual')
    novo_email = dados.get('novo_email')
    nova_senha = dados.get('nova_senha')

    user = User.query.filter_by(login=login).first()
    if not user: return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    msg = []
    
    if nova_senha and len(nova_senha.strip()) > 0:
        if not senha_atual or not check_password_hash(user.senha_hash, senha_atual):
            return jsonify({'erro': 'Senha atual incorreta ou ausente. Necessária para mudar a senha.'}), 400
        user.senha_hash = generate_password_hash(nova_senha)
        msg.append("Senha atualizada")

    if novo_email and novo_email != user.email:
        user.email = novo_email
        msg.append("Email atualizado")

    if not msg: return jsonify({'mensagem': 'Nada foi alterado.'})

    db.session.commit()
    return jsonify({'mensagem': " e ".join(msg) + " com sucesso!"})


@auth_bp.route('/recuperar/solicitar', methods=['POST'])
def solicitar_recuperacao():
    email = request.json.get('email')
    user = User.query.filter_by(email=email).first()
            
    if not user: return jsonify({'erro': 'Email não encontrado.'}), 404
    
    codigo = str(random.randint(1000, 9999))
    user.recovery_code = codigo
    db.session.commit()
    
    enviou = enviar_email_real(email, codigo)
    
    if enviou:
        return jsonify({'mensagem': 'Código enviado para seu email.', 'login': user.login})
    else:
        print(f"FALHA NO EMAIL. CÓDIGO LOCAL PARA TESTE: {codigo} (Login: {user.login})")
        return jsonify({'mensagem': 'Erro no envio de email. Verifique o terminal do servidor.', 'login': user.login})


@auth_bp.route('/recuperar/confirmar', methods=['POST'])
def confirmar_recuperacao():
    dados = request.json
    login = dados.get('login')
    codigo_digitado = dados.get('codigo')
    nova_senha = dados.get('nova_senha')
    
    user = User.query.filter_by(login=login).first()
    if not user: return jsonify({'erro': 'Erro de usuário'}), 400
    
    codigo_real = user.recovery_code
    if not codigo_real or codigo_real != codigo_digitado:
        return jsonify({'erro': 'Código inválido!'}), 400
        
    user.senha_hash = generate_password_hash(nova_senha)
    user.recovery_code = None
    db.session.commit()
    
    return jsonify({'mensagem': 'Senha redefinida com sucesso!'})
