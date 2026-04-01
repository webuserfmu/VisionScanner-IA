import os
import uuid
from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from models import User, Product
from extensions import db
from config import Config
from services.ai_service import extrair_vetor, adicionar_ao_indice, buscar_no_indice, get_total_imagens

ai_bp = Blueprint('ai', __name__)

def verificar_limite_busca(user):
    if user.limite_diario == 0: return True, "Ilimitado"

    hoje = datetime.now().strftime('%Y-%m-%d')

    if user.uso_hoje_data != hoje:
        user.uso_hoje_data = hoje
        user.uso_hoje_count = 0

    if user.uso_hoje_count >= user.limite_diario:
        return False, f"Limite diário atingido ({user.limite_diario} pesquisas)."

    user.uso_hoje_count += 1
    db.session.commit()
    return True, "OK"

@ai_bp.route('/imagens/<path:filename>')
def servir_imagem(filename): 
    return send_from_directory(Config.PASTA_IMAGENS, filename)

@ai_bp.route('/produto/<codigo>', methods=['GET'])
@jwt_required()
def get_produto(codigo):
    prod = Product.query.filter_by(codigo=codigo).first()
    if prod:
        return jsonify({'existe': True, 'nome': prod.nome})
    return jsonify({'existe': False})

@ai_bp.route('/produto/<codigo>', methods=['DELETE'])
@jwt_required()
def deletar_produto(codigo):
    login = get_jwt_identity()
    user = User.query.filter_by(login=login).first()
    
    if not user or not user.perm_del:
        return jsonify({'erro': 'Sem permissão para deletar'}), 403

    produtos = Product.query.filter_by(codigo=codigo).all()
    if not produtos:
        return jsonify({'erro': 'Produto não encontrado'}), 404
        
    for p in produtos:
        # Tenta remover o arquivo físico da imagem
        caminho_imagem = os.path.join(Config.PASTA_IMAGENS, p.arquivo)
        if os.path.exists(caminho_imagem):
            try:
                os.remove(caminho_imagem)
            except Exception as e:
                print(f"Erro ao remover imagem {caminho_imagem}: {e}")
                
        # Repare que os vetores no índice FAISS não são deletáveis em IndexFlatL2 nativamente.
        # Ao deletarmos a tupla da base SQL, a busca ignorará o índice do FAISS orfão 
        # (já que Product.query.get retornará None no loop de busca).
        db.session.delete(p)
        
    db.session.commit()
    return jsonify({'mensagem': f'Produto {codigo} e todas as suas imagens foram deletados.'})

@ai_bp.route('/buscar', methods=['POST'])
@jwt_required()
def buscar():
    login = get_jwt_identity()
    user = User.query.filter_by(login=login).first()
    
    if not user or not user.perm_search:
        return jsonify({'erro': 'Sem permissão de busca'}), 403
    
    permitido, msg = verificar_limite_busca(user)
    if not permitido: return jsonify({'erro': msg}), 429

    if 'imagem' not in request.files: return jsonify({'erro': 'Faltou imagem'}), 400
    if get_total_imagens() == 0: return jsonify({'resultados': []}), 200

    try:
        vetor = extrair_vetor(request.files['imagem'].read())
        distancias, indices = buscar_no_indice(vetor, 6)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
        
    agrupados = {}
    base_url = request.host_url.rstrip('/')
    
    for i, idx_interno in enumerate(indices[0]):
        if idx_interno != -1:
            item = Product.query.get(int(idx_interno))
            if item:
                cod = item.codigo
                dist = float(distancias[0][i])
                if cod not in agrupados:
                    agrupados[cod] = {
                        'codigo': cod, 
                        'nome': item.nome, 
                        'melhor_distancia': dist, 
                        'imagem_url': f"{base_url}/imagens/{item.arquivo}", 
                        'contagem_matches': 1
                    }
                else:
                    agrupados[cod]['contagem_matches'] += 1
                    if dist < agrupados[cod]['melhor_distancia']:
                        agrupados[cod]['melhor_distancia'] = dist
                        agrupados[cod]['imagem_url'] = f"{base_url}/imagens/{item.arquivo}"
    
    res = list(agrupados.values())
    res.sort(key=lambda x: x['melhor_distancia'])
    return jsonify({'resultados': res})

@ai_bp.route('/cadastrar', methods=['POST'])
@jwt_required()
def cadastrar():
    login = get_jwt_identity()
    user = User.query.filter_by(login=login).first()
    
    if not user or not user.perm_add:
        return jsonify({'erro': 'Sem permissão para adicionar'}), 403

    arquivo = request.files.get('imagem')
    codigo = request.form.get('codigo')
    nome = request.form.get('nome')
    
    if not arquivo or not codigo: return jsonify({'erro': 'Dados incompletos'}), 400
    
    extensao = arquivo.filename.split('.')[-1]
    nome_arquivo = f"{uuid.uuid4()}.{extensao}"
    caminho = os.path.join(Config.PASTA_IMAGENS, nome_arquivo)
    arquivo.save(caminho)
    
    try:
        vetor = extrair_vetor(caminho)
        novo_id_faiss = adicionar_ao_indice(vetor)
        
        novo_produto = Product(id_faiss=novo_id_faiss, codigo=codigo, nome=nome, arquivo=nome_arquivo)
        db.session.add(novo_produto)
        db.session.commit()
    except Exception as e:
        return jsonify({'erro': f'Erro ao processar imagem: {str(e)}'}), 500
    
    return jsonify({'mensagem': 'Cadastrado!', 'total_imagens': get_total_imagens()})
