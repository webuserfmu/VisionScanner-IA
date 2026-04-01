from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime

print("A gerar certificado SSL para o IP 10.87.252.191...")

# Gera a chave privada
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Cria as informações do certificado (Válido para o seu IP da VPN)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, u"10.87.252.191")
])

# Define validade para 10 anos (3650 dias)
cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.utcnow()
).not_valid_after(
    datetime.datetime.utcnow() + datetime.timedelta(days=3650)
).sign(key, hashes.SHA256())

# Salva os ficheiros
with open("key.pem", "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

with open("cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("✅ 'cert.pem' e 'key.pem' gerados com sucesso na pasta!")