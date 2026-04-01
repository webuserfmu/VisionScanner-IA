from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    limite_diario = db.Column(db.Integer, default=0)
    uso_hoje_data = db.Column(db.String(20), default='')
    uso_hoje_count = db.Column(db.Integer, default=0)
    perm_search = db.Column(db.Boolean, default=True)
    perm_add = db.Column(db.Boolean, default=True)
    perm_del = db.Column(db.Boolean, default=True)
    perm_admin = db.Column(db.Boolean, default=False)
    recovery_code = db.Column(db.String(10), nullable=True)

class Product(db.Model):
    id_faiss = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(100), nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    arquivo = db.Column(db.String(255), nullable=False)
