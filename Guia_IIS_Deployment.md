# Guia Definitivo: Implantar VisionScanner IA no Windows Server / IIS 10+ 

Este manual o ajudará a migrar a aplicação Flask (VisionScanner) do servidor Cheroot interno para o **IIS (Internet Information Services)** robusto da Microsoft usando a camada `wfastcgi`. O IIS atuará como "Guardião" e servidor principal (porta 80/443), enquanto o backend em Python o processa via interface de gateway rápida.

> [!NOTE]
> O IIS servirá tanto a API inteira quanto a renderização da pasta `Frontoffice`, garantindo máxima compatibilidade pois já está tudo mapeado dentro do micro-framework Flask (`app.py`).

## 1. Pré-Requisitos (Preparando a Máquina)

1. **Instalar o IIS**:
   - Pressione **Win + R**, digite `appwiz.cpl` e clique em "Ativar ou desativar recursos do Windows".
   - Marque a caixa **Internet Information Services**.
   - Expanda e navegue até *Serviços da World Wide Web* -> *Recursos de Desenvolvimento de Aplicativos* e **MARQUE** obrigatoriamente a opção **CGI**.
   - Confirme e aguarde o Windows aplicar.

2. **Instalar o Python**:
   - Baixe a versão mais atual em [python.org](https://www.python.org/downloads/windows/).
   - Durante a instalação, clique impreterivelmente na caixa **"Add Python to PATH"**.
   - Recomenda-se instalar em um caminho de fácil acesso (ex: `C:\Python312\`).

## 2. Preparando os Pacotes no Python (wfastcgi)

Em um terminal que você abriu **Como Administrador**, navegue até a pasta da aplicação (`Backoffice`):

```cmd
cd C:\python\iaserchbyimage\Backoffice
pip install -r requirements.txt
pip install wfastcgi
```

Ainda como Administrador, ative o FastCGI no servidor rodando o comando nativo:

```cmd
wfastcgi-enable
```

> [!IMPORTANT]
> O comando acima vai "cuspir" no console um diretório composto pela fusão do seu python e do wfastcgi (Algo semelhante a `"C:\Python312\python.exe|C:\Python312\Lib\site-packages\wfastcgi.py"`). **COPIE e GUARDE essa string**, nós vamos precisar dela na configuração do site!

## 3. Configurando a Estrutura de Pastas e Permissões

Você precisa conceder ao "Usuário do Servidor" a permissão para ler sua pasta e para a IA salvar as fotos carregadas e gravar o log de Vetores:

1. Vá até a pasta matriz do seu projeto: `C:\python\iaserchbyimage\`
2. Clique com o Botão Direito na pasta -> Propriedades -> Guia Segurança.
3. Clique em Editar -> Adicionar... e digite: `IIS_IUSRS` (e também tente `IUSR`). Dê OK.
4. Para o `IIS_IUSRS`, marque nas Caixinhas Embaixo o Controle de "Modificar" e "Gravação".
5. Faça o mesmo procedimento para as pastas internas, prestando especial atenção a `Backoffice\imagens_salvas` e `Backoffice\instance`.

> [!WARNING]
> Sem as permissões de Gravação do `IIS_IUSRS`, o IIS não permitirá ao site anexar imagens nem consultar o índice FAISS, resultando em Erros Críticos `Http 500`.

## 4. Configuração do Servidor IIS

1. Abra o **Gerenciador do IIS** (Win + S -> digite IIS).
2. Na Faixa Esquerda, clique com Botão Direito em **Sites** -> **Adicionar Site...**
3. **Nome do site**: `VisionScanner`
4. **Caminho Físico**: Aponte EXATAMENTE para a pasta do Backend: `C:\python\iaserchbyimage\Backoffice`
5. **Porta**: 80 (ou 443 caso suba um certificado). Dê OK.

### Desbloqueio e Tratamento de Variáveis CGI

1. Clique no Servidor (no lado esquerdo total).
2. Dê duplo clique em **Mapeamentos de Manipulador**.
3. No painel direito da aba que se abre, clique em **Adicionar Mapeamento de Módulo...**
    - **Caminho de solicitação**: `*`
    - **Módulo**: `FastCgiModule`
    - **Executável**: Cole aqui aquela STRING INTEIRA que você guardou no passo 2 do `wfastcgi-enable`! (ex: `C:\Python312\python.exe|C:\Python312\Lib\site-packages\wfastcgi.py`)
    - **Nome**: `FlaskHandler`
4. Confirme, e quando ele perguntar se deseja criar uma regra do FastCGI de exclusão, diga **SIM**.

## 5. Arquivo mágico: web.config

O IIS precisa entender como apontar o roteamento pro seu `app.py`. Crie um arquivo nativo com nome `web.config` na pasta mãe do backend (junto ao app.py), contendo exatamente isso (modifique caminhos se usar outros):

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="Python FastCGI" 
           path="*" 
           verb="*" 
           modules="FastCgiModule" 
           scriptProcessor="C:\Python312\python.exe|C:\Python312\Lib\site-packages\wfastcgi.py" 
           resourceType="Unspecified" 
           requireAccess="Script" />
    </handlers>
  </system.webServer>
  
  <appSettings>
    <!-- Configura as engrenagens de arrasto WSGI -->
    <add key="WSGI_HANDLER" value="app.app" />
    <add key="PYTHONPATH" value="C:\python\iaserchbyimage\Backoffice" />
    
    <!-- Configura as variáveis de ambiente necessárias -->
    <add key="TF_CPP_MIN_LOG_LEVEL" value="2" />
    <add key="TF_ENABLE_ONEDNN_OPTS" value="0" />
  </appSettings>
</configuration>
```
*(Nota: Certifique-se de substituir onde diz `C:\Python312\...` caso seu Python esteja em outro local).*

## 6. Ligar Motores (Validação Final)

1. Volte pro servidor IIS. 
2. No menu do canto direito, clique em "Reiniciar" no Site.
3. Abra o navegador e digite o IP ou `http://localhost`. O IIS irá processar o `wfastcgi`, ler o Framework Python, cruzar caminhos com os arquivos Fontoffice da pasta superior, e devolver o UI perfeitamente integrado.

Dica Bônus: Como agora você está no IIS, o certificado SSL (`cert.pem`) não necessita mais ser lido pelo cheroot. Na configuração do painel do servidor (Botão Direito -> Associações) você poderá adicionar o tráfego `https` usando a chave encriptada .PFX gerada do certificado nativo pelo motor do próprio Windows.
