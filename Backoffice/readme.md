# VisionScanner IA 👁️🧠

VisionScanner é uma aplicação web autônoma (bunker offline) hiper-moderna capaz de analisar, vetorizar e encontrar similaridades em imagens utilizando o cérebro de inteligência artificial convolucional **MobileNetV2** nativamente. Ele funciona localmente, protegendo a privacidade dos dados ao mesmo tempo que oferece uma interface futurista baseada em *Glassmorphism*.

## 🔥 Interface Multi-Faces
O sistema foi concebido para entregar elegância premium e conta com um **Motor de Temas** embutido que salva o gosto de cada operador diretamente no banco de dados SQLite.

### 🌌 Tema: Cosmic Dark (Principal)
![Visão Geral do Painel](../docs/mockup_dark.png)
> O tema padrão acopla painéis translúcidos, profundidade cósmica azul-marinho e leitura noturna ideal para grandes fluxos de trabalho.

### ☀️ Tema: Light Acetinado
![Resultados e Navegação](../docs/mockup_light.png)
> Alternativa limpa para ambientes bem iluminados, mantendo todo o polimento e sombras de vidro. *(Também suporta temas extras como Dracula e Matrix)*.

---

## 🛠️ Stack Tecnológico

- **IA / Backoffice:** Python, TensorFlow (Keras), FAISS (Facebook AI Similarity Search), Flask, SQLAlchemy.
- **Servidor:** Cheroot WSGI (com suporte nativo inteligente a `HTTPS`/SSL).
- **Frontoffice:** Vanilla Javascript, Bootstrap 5 + CSS Puro (Sem dependências obscuras, velocidade de carregamento absurda).

## 🚀 Como Executar Localmente
O sistema busca o banco de vetores sem necessidade de nuvem. Inicie sua Máquina Virtual Python a partir da pasta central:
```cmd
c:/python/iaserchbyimage/.venv/Scripts/python.exe app.py
```
> O Cheroot levantará a porta `5000` em modo `HTTP` se não houver certificados, ou subirá o escudo fechado `HTTPS` automaticamente se detectar a existência da dupla `cert.pem` e `key.pem`.

## 🔒 Segurança (Admin & Email)
O Painel de Administrador oferece o controle granular:
- Adição dinâmica de utilizadores sem limite numérico (`Cota Diária`).
- Definição de permissões térmicas com `Busca`, `Gravação` e `Deleção`.
- **Prevenção contra Exclusão:** O próprio sistema impede que o último administrador seja apagado acidentalmente.
- Cofre Encriptado Fernet (AES) para proteger os dados SMTP de recuperação de senhas dos seus robôs e-mail.
