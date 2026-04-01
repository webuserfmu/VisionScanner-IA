# IA Search By Image

Sistema completo de busca e cadastro de produtos por similaridade de imagem utilizando Inteligência Artificial.
O projeto é dividido em um **Backoffice** (Backend em Flask/Python) que fornece a robusta API Rest e processamento do modelo Keras de Visão Computacional, e um **Frontoffice** (Frontend) responsável pela interação com o usuário final e visualização fluida e moderna.

---

## 🚀 Tecnologias Integradas

- **Backend (API + IA)**
  - **Python** (versão recomendada >= 3.10)
  - **Flask** (Framework Web MVC)
  - **Flask-SQLAlchemy + SQLite** (Banco de dados relacional e ORM para usuários e histórico).
  - **Flask-JWT-Extended** (Autenticação e segurança de rotas com Tokens Bearer).
  - **Werkzeug** (Hashes de senhas em padrão de segurança PBKDF2).
  - **TensorFlow & Keras** (Processamento dos tensores e embeddings de visão usando MobileNetV2).
  - **FAISS (Meta)** (Motor de busca vetorial super rápido para comparar grandes volumes de similaridades em C++ e Python).
  - **Cryptography** (Criptografia para informações de conexão SMTP).

*Nota: Todas as variáveis sensíveis que precisarem passar por e-mail, como códigos de recuperação, usam disparo direto via SMTP para segurança.*

---

## 📂 Estrutura de Diretórios
```text
iaserchbyimage/
│
├── Backoffice/                  # Lógica do Servidor e Inteligência Artificial
│   ├── app.py                   # Ponto de entrada (Entrypoint), rotas, Banco e JWT.
│   ├── imagens_salvas/          # Armazenamento físico das imagens upadas
│   ├── instance/                # Gerado, contém o `database.db` (Banco de Dados Oculto)
│   ├── modelo_mobilenetv2_local.keras # Pesos do modelo Neural já treinado.
│   ├── meu_cerebro_visual.index # Matriz Vetorial serializada das imagens (FAISS)
│   ├── cert.pem, key.pem        # Chaves de desenvolvimento SSL Local (https).
│   └── secret.key, config.enc   # Credenciais SMTP encriptadas.
│
├── Frontoffice/                 # Camada de apresentação e interface visual (Frontend)
│   # Aqui ficam seus arquivos .html, .css, .js...
│
└── .venv/                       # O ambiente virtual do Python (Onde ficam os pacotes)
```

---

## 🔒 Endpoints (Rotas da API) Protegidas

Desde o update de segurança, a maioria das rotas do backend precisam do token JWT. A API funciona trafegando e retornando JSON na porta padrão `5000`.

### Autenticação (Abertas)
- `POST /login`: Recebe `{"usuario": "admin", "senha": "123"}` -> Retorna os dados do perfil e o `access_token` JWT em caso de sucesso.
- `POST /recuperar/solicitar`: Solicita um código via email para reset.
- `POST /recuperar/confirmar`: Confirma a troca de senha.

### Rotas com JWT Requerido
*(Todas exigem o header `Authorization: Bearer <seu_token>` e são baseadas nas permissões do perfil)*

**Usuário:**
- `POST /perfil/atualizar`: Atualiza dados do seu próprio perfil e senha.

**Inteligência Artificial (IA):**
- `POST /buscar`: Recebe um arquivo pelo form-data (`imagem`). Retorna as melhores semelhanças e agrupamentos pelo modelo *MobileNetV2* com base na Similaridade Euclidiana (FAISS).
- `POST /cadastrar`: Recebe form-data (`imagem`, `codigo`, `nome`). Vetoriza, dimensiona para 224x224 pixels e armazena na Matrix de índice e disco físico.
- `GET /produto/<codigo>`: Valida se o produto em questão já existe no banco.

**Administração:**
- `GET/POST /usuarios`: Lista ou cria usuários com permissões granulares (`perm_search`, `perm_add`, `perm_del`, `perm_admin`).
- `DELETE /usuarios/<login_alvo>`: Remove um usuário por login.
- `POST /zerar`: **Cuidado!** Um super admin pode formatar e esvaziar todo o índice FAISS e banco de dados de produtos.

---

---

## ⚙️ Guia Rápido: Instalação e Primeira Utilização (Passo-a-Passo)

Siga estas instruções rigorosamente ao baixar (ou clonar) este projeto para a sua máquina pela primeira vez:

### Passo 1: Preparar o Ambiente Python
Abra o seu terminal na pasta raiz do projeto (`iaserchbyimage/`) e crie o seu ambiente virtual:
```bash
python -m venv .venv
# Ativar no Windows:
.venv\Scripts\activate
# Ativar no Linux/Mac:
source .venv/bin/activate
```

### Passo 2: Instalar Dependências
Com o ambiente ativado, entre na pasta do servidor e instale as bibliotecas:
```bash
cd Backoffice
pip install -r requirements.txt
```

### Passo 3: Baixar o "Cérebro" da Inteligência Artificial
O modelo de rede neural MobileNetV2 do TensorFlow não é salvo no Github devido ao seu tamanho. Você precisa instruir o projeto a baixá-lo localmente executando o script dedicado:
```bash
python baixar_modelo.py
```
*(Ele criará um arquivo `modelo_mobilenetv2_local.keras` gigantesco na pasta).*

### Passo 4: Configurar o Robô de E-mails Seguros
Para que os usuários consigam recuperar senhas caso as esqueçam, configure seu SMTP e credenciais. Para evitar senhas expostas, criamos um assistente de criptografia!
Execute:
```bash
python configurar.py
```
*(Siga as instruções na tela. Você informará seu e-mail do Gmail/Outlook e a sua Senha de Aplicativo. As senhas serão seladas nos novos arquivos ocultos `secret.key` e `config.enc`).*

### Passo 5: Iniciar o Servidor
Mande o servidor Flask subir pela primeira vez:
```bash
python app.py
```
A API iniciará de forma autônoma e mágica. Neste momento:
- O banco de dados oculto (`instance/database.db`) será auto-construído.
- A pasta `imagens_salvas/` será automaticamente desenhada.
- O Primeiro Usuário (Gestor Global) será criado automaticamente.

### Passo 6: Acessar a Interface (Frontoffice)
Abra seu navegador favorito e acesse a URL que o Python entregar no painel (Geralmente `http://127.0.0.1:5000/`).

> **Credenciais de Acesso Original (Por Defeito):**
> **Utilizador:** `admin`
> **Senha:** `123`

Parabéns! Você já está pronto para subir suas imagens no menu *"Alimentar/Ensinar Ítem"*.
