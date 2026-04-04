<#
.SYNOPSIS
Script de Automação de Instalação do VisionScanner no Microsoft IIS.
Este script ativa recursos do Windows, baixa pendências, injeta permissões, e cria o Site e o web.config dinamicamente no IIS.

.DESCRIPTION
Pode ser executado diretamente do Windows PowerShell (Executar como Administrador).
É provável que ocorra falhas se a política de execução não permitir scripts locais:
Para liberar temporariamente: Set-ExecutionPolicy Bypass -Scope Process -Force
#>

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   INSTALADOR E AUTOMATIZADOR DO IIS - VISIONSCANNER IA" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verifica Privilégios Administrativos
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Este script precisa ser executado como Administrador!" -ForegroundColor Red
    Write-Host "Clique com o botão direito no ícone do PowerShell e escolha 'Executar como Administrador'." -ForegroundColor Red
    Pause
    Exit
}

# Caminhos base
$basePath = "C:\python\iaserchbyimage"
$backofficePath = "$basePath\Backoffice"
$siteName = "VisionScanner"

Write-Host "`n[0/6] Configuração de Rota e Porta" -ForegroundColor Yellow
$inputPort = Read-Host "Digite a porta para hospedar o VisionScanner (Aperte Enter para usar nativa 80)"
if ([string]::IsNullOrWhiteSpace($inputPort)) {
    $port = 80
} else {
    $port = [int]$inputPort
}

# 2. Habilitando Recursos do Windows e IIS
Write-Host "`n[1/6] Habilitando Internet Information Services (IIS) e CGI..." -ForegroundColor Yellow
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole -All -NoRestart > $null
Enable-WindowsOptionalFeature -Online -FeatureName IIS-CGI -All -NoRestart > $null
Write-Host "Recursos do IIS instalados com sucesso!" -ForegroundColor Green

# Importa Módulo de Administração WEB
Import-Module WebAdministration

# 3. Preparando o Ambiente Python
Write-Host "`n[2/6] Verificando e instalando wfastcgi no Python..." -ForegroundColor Yellow
try {
    # Garante que o pacote básico está no python global/ambiente rodando
    $null = python -m pip install wfastcgi
} catch {
    Write-Host "Erro: Python ou Pip não foi encontrado no PATH do sistema. Instale o Python primeiro." -ForegroundColor Red
    Exit
}

$wfastcgiExe = (Get-Command wfastcgi-enable -ErrorAction SilentlyContinue)
if (-not $wfastcgiExe) {
    Write-Host "Erro: wfastcgi-enable não encontrado. Tente reinstalar o Python." -ForegroundColor Red
    Exit
}

# Desativa caso já exista para pegar a string de saída limpa
wfastcgi-disable 2>&1 | Out-Null
$wfastcgiOutput = wfastcgi-enable
# wfastcgi-enable solta um padrão ex: "c:\python312\python.exe|c:\python312\lib\site-packages\wfastcgi.py" confugurado no <fastCGI>.
# Vamos pescar a string gerada que fica envolta em aspas na saída.
$regex = '"([^"]*python\.exe\|[^"]*wfastcgi\.py)"'
if ($wfastcgiOutput -match $regex) {
    $fastCgiConfig = $matches[1]
    Write-Host "Roteador Encontrado e Registrado internamente: " -NoNewline; Write-Host $fastCgiConfig -ForegroundColor Cyan
} else {
    Write-Host "Não foi possível extrair automaticamente o caminho do handler wfastcgi-enable." -ForegroundColor Red
    Write-Host "Saída do comando: $wfastcgiOutput" -ForegroundColor Red
    Exit
}

# 4. Configuração de Permissões de Pastas (IIS_IUSRS)
Write-Host "`n[3/6] Concedendo Controle (Gravação/Leitura) da pasta matriz para o usuário IIS_IUSRS..." -ForegroundColor Yellow
# /OI /CI /F (herança para arquivos e pastas) /M (modificar)
icacls "$basePath" /grant "IIS_IUSRS:(OI)(CI)M" /T /Q | Out-Null
icacls "$basePath" /grant "IUSR:(OI)(CI)M" /T /Q | Out-Null
Write-Host "Permissões de rede injetadas nativamente com (icacls)." -ForegroundColor Green

# 5. Cravação do Site no IIS
Write-Host "`n[4/6] Registrando o WebSite ($siteName)..." -ForegroundColor Yellow

# Remove site antigo se existir
if (Test-Path "IIS:\Sites\$siteName") {
    Remove-WebSite -Name $siteName
    Write-Host "Sítio antigo apagado sobrepondo por um limpo."
}

# Impede colisão de Portas varrendo TODOS os sites do IIS em execução
$conflictingSites = Get-Website | Where-Object { $_.Bindings.Collection.bindingInformation -match ":$port:" -and $_.Name -ne $siteName -and $_.State -eq 'Started' }

if ($conflictingSites) {
    foreach ($site in $conflictingSites) {
        Write-Host "ATENÇÃO: O site '$($site.Name)' já está usando a porta $port!" -ForegroundColor Red
        $stopConflicting = Read-Host "Deseja forçar o desligamento de '$($site.Name)' para liberar esta porta? (S/N)"
        if ($stopConflicting -match "^[sS]") {
            Stop-Website -Name $site.Name
            Write-Host "Site '$($site.Name)' foi interrompido (Stop)." -ForegroundColor Yellow
        } else {
            Write-Host "Risco de Falha: O IIS irá registrar o site, mas bloqueará a inicialização devido ao conflito de portas!" -ForegroundColor Red
        }
    }
}

# Cria o pool e o site apontando para a pasta onde roda o Flask (Backoffice)
New-WebAppPool -Name $siteName | Out-Null
New-Website -Name $siteName -Port $port -PhysicalPath $backofficePath -ApplicationPool $siteName -Force | Out-Null
Write-Host "Site publicado na Porta $port." -ForegroundColor Green

# Desbloqueia handlers CGI nas entranhas do IIS
Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST'  -filter "system.webServer/security/isapiCgiRestriction" -name "." -value @{description='Flask FastCGI';path=$fastCgiConfig;allowed='True'} -ErrorAction SilentlyContinue

# 6. Gravação do web.config dinâmico
Write-Host "`n[5/6] Gerando arquivo web.config com roteamento do app..." -ForegroundColor Yellow
$webConfigContent = @"
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="Python FastCGI" path="*" verb="*" modules="FastCgiModule" scriptProcessor="$fastCgiConfig" resourceType="Unspecified" requireAccess="Script" />
    </handlers>
  </system.webServer>
  <appSettings>
    <!-- Roteamento do motor Flask -->
    <add key="WSGI_HANDLER" value="app.app" />
    <add key="PYTHONPATH" value="$backofficePath" />
    
    <!-- Filtros anti-spam de log do TensorFlow -->
    <add key="TF_CPP_MIN_LOG_LEVEL" value="2" />
    <add key="TF_ENABLE_ONEDNN_OPTS" value="0" />
  </appSettings>
</configuration>
"@

$webConfigPath = "$backofficePath\web.config"
Set-Content -Path $webConfigPath -Value $webConfigContent -Encoding UTF8
Write-Host "Arquivo web.config injetado na alma." -ForegroundColor Green

Write-Host "`n[6/6] Reiniciando Servidor Web Internamente..." -ForegroundColor Yellow
iisreset /restart | Out-Null

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   INSTALAÇÃO E DEPLOY CONCLUÍDOS COM GLÓRIA!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Acesse o sistema local através de: http://localhost:$port" 
Write-Host "Ou descubra seu IP abrindo o CMD e digitando: ipconfig"

Write-Host "`nPara encerrar, pressione Enter..."
Read-Host
