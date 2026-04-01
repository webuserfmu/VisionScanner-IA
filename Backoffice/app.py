import os
# Silenciadores do TensorFlow (Deve vir o mais cedo possível, antes de qualquer "import tensorflow" oculto noutros módulos)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Oculta mensagens Informativas ('I') e Warnings ('W') do console
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' # Oculta os avisos flutuantes da biblioteca oneDNN Intel

from flask import Flask
from flask_cors import CORS
from werkzeug.security import generate_password_hash

from config import Config
from extensions import db, jwt
from models import User

from flask import send_from_directory
import os

# Import Blueprints
from routes.auth import auth_bp
from routes.ai import ai_bp
from routes.admin import admin_bp

def create_app(config_class=Config):
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Frontoffice'))
    app = Flask(__name__, static_folder=os.path.join(frontend_dir, 'static'))
    app.config.from_object(config_class)
    
    CORS(app)

    # Initialize Flask extensions here
    db.init_app(app)
    jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(frontend_dir, path)

    # Configuração da Pasta de Imagens
    os.makedirs(app.config['PASTA_IMAGENS'], exist_ok=True)

    with app.app_context():
        db.create_all()
        
        # Migração Segura de Tabela (Adiciona coluna de tema sem quebrar o BD)
        from sqlalchemy import text
        try:
            db.session.execute(text("ALTER TABLE user ADD COLUMN tema_perfil VARCHAR(20) DEFAULT 'dark'"))
            db.session.commit()
            print("Migração Concluída: Coluna de Temas adicionada aos usuários.")
        except Exception:
            db.session.rollback() # A coluna já existe, segue o jogo.
        # Inicializa Super Admin se não existir
        if not User.query.filter_by(login='admin').first():
            admin_user = User(
                login='admin',
                senha_hash=generate_password_hash('123'),
                nome='Super Admin',
                email='admin@sistema.local',
                limite_diario=0,
                perm_search=True,
                perm_add=True,
                perm_del=True,
                perm_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário 'admin' padrão verificado/criado.")

    return app

if __name__ == '__main__':
    from cheroot.wsgi import Server as WSGIServer
    from cheroot.ssl.builtin import BuiltinSSLAdapter

    app = create_app()
    print("Iniciando Servidor de Produção via Cheroot (Standalone)...")
    
    server = WSGIServer(('0.0.0.0', 5000), app, numthreads=6)
    
    if os.path.exists('cert.pem') and os.path.exists('key.pem'):
        server.ssl_adapter = BuiltinSSLAdapter('cert.pem', 'key.pem')
        print("O VisionScanner IA está rodando em modo SEGURO (HTTPS) na porta 5000!")
    else:
        print("O VisionScanner IA está rodando em modo HTTP na porta 5000!")
        
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()