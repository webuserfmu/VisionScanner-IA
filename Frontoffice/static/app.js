// CONFIGURAÇÕES
const API = ""; // URL DO BACKEND SERVIDO NO MESMO DOMINIO
let modalRecuperacaoObj;
let usuarioRecuperacao = null;
let toastObj;

// Ao Carrregar Documento
document.addEventListener("DOMContentLoaded", function(){
    toastObj = new bootstrap.Toast(document.getElementById('liveToast'));
    
    // Dispara a varredura do dicionário para a língua preferida do utilizador
    inicializarIdioma();
    
    verificarEstadoArmadura(navigator.onLine);
    
    checkSessao();
});

// --- SISTEMA INTERNO DE TRADUÇÃO (i18n) ---
let currentLang = localStorage.getItem('ia_lang') || 'pt';

/**
 * Motor de Trânsito Dinâmico: Lê a base JSON de i18n
 * e varre os elementos no HTML (data-i18n) trocando os textos instantaneamente.
 */
function mudarIdioma(lang) {
    currentLang = lang;
    localStorage.setItem('ia_lang', lang);
    
    Object.keys(window.i18n[lang]).forEach(key => {
        const uiElems = document.querySelectorAll(`[data-i18n="${key}"]`);
        uiElems.forEach(el => {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = window.i18n[lang][key];
            } else {
                el.innerHTML = window.i18n[lang][key];
            }
        });
    });

    const lbl = lang === 'pt' ? 'PT' : (lang === 'en' ? 'EN' : 'ES');
    if(document.getElementById('btnLangLogin')) document.getElementById('btnLangLogin').innerHTML = `<i class="bi bi-globe me-1"></i> ${lbl}`;
    if(document.getElementById('btnLangApp')) document.getElementById('btnLangApp').innerHTML = `<i class="bi bi-globe me-1"></i> ${lbl}`;
}

function inicializarIdioma() {
    mudarIdioma(currentLang);
}

// Eventos Globais de Rede
window.addEventListener('offline', () => verificarEstadoArmadura(false));
window.addEventListener('online', () => {
    verificarEstadoArmadura(true);
    showToast("Conexão com a Internet Restabelecida.", "success");
});

function verificarEstadoArmadura(isOnline) {
    const containerRecup = document.getElementById("containerRecuperacao");
    if(containerRecup) {
        if(!isOnline) {
            containerRecup.style.display = "none";
            showToast("Bunker Local: Sistema Operando Offline. (Recuperação de Senha Oculta)", "warning");
        } else {
            containerRecup.style.display = "block";
        }
    }
}

function showToast(mensagem, tipo = 'info') {
    // --- MAGIA DO INTERCEPTADOR DE MENSAGENS DO BACKEND ---
    // O backend continua devolvendo PT-BR puro para não perdermos velocidade e não ter de reescrever o Python.
    // O frontend cruza o texto do backend com as chaves PT e, se prever, cospe logo em Inglês ou Espanhol nativo!
    let translatedMsg = mensagem;
    const chaveOriginal = Object.keys(window.i18n['pt']).find(k => window.i18n['pt'][k] === mensagem);
    if(chaveOriginal && window.i18n[currentLang][chaveOriginal]) {
        translatedMsg = window.i18n[currentLang][chaveOriginal];
    }
    // -----------------------------------------------------

    document.getElementById('toastText').innerText = translatedMsg;
    const icon = document.getElementById('toastIcon');
    const bg = document.getElementById('liveToast');
    
    icon.className = "me-2 fs-5";
    if(tipo === 'error'){
        icon.classList.add("bi-exclamation-octagon", "text-danger");
        bg.style.borderLeftColor = "var(--danger) !important";
    } else if (tipo === 'success') {
        icon.classList.add("bi-check2-circle", "text-success");
    } else {
        icon.classList.add("bi-info-circle", "text-accent");
    }
    toastObj.show();
}

// --- SISTEMA JWT E SESSÃO ---
function getAuthHeader() {
    const s = JSON.parse(localStorage.getItem("ia_sessao"));
    if(!s || !s.access_token) { logout(); return {}; }
    return { 'Authorization': `Bearer ${s.access_token}` };
}

/**
 * Escudo Embutido do Sistema: Ao invés de usar fetch() normal, todo trafego do painel restrito usa este wrapper.
 * Ele anexa o JWT do SuperAdmin ou Usuário e, se o Servidor recusar por Token envelhecido, ejeta silenciosamente!
 */
async function fetchAutenticado(url, options = {}) {
    const headers = { ...options.headers, ...getAuthHeader() };
    if (options.body instanceof FormData) delete headers['Content-Type']; 
    else if(!headers['Content-Type']) headers['Content-Type'] = 'application/json';
    
    options.headers = headers;
    try {
        const res = await fetch(url, options);
        if (res.status === 401 || res.status === 422) { 
            showToast("Sessão expirada. Faça login novamente.", "error");
            setTimeout(() => logout(), 2000);
            throw new Error("Sessão Invalida.");
        }
        return res;
    } catch (err) {
        console.error(err);
        if (err.message !== "Sessão Invalida.") showToast("Erro de rede com o servidor backend.", "error");
        throw err;
    }
}

// --- LOGIN & INICIALIZAÇÃO ---
function checkSessao() {
    const s = JSON.parse(localStorage.getItem("ia_sessao"));
    if(s && s.access_token && s.perms) setupUI(s);
    else { 
        document.getElementById('telaLogin').classList.remove('d-none'); 
        document.getElementById('telaApp').style.display='none'; 
    }
}

async function fazerLogin() {
    const u = document.getElementById('loginUser').value;
    const p = document.getElementById('loginPass').value;
    const btn = document.getElementById('btnLogin');
    
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Autenticando...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API}/login`, { 
            method: 'POST', 
            headers: {'Content-Type': 'application/json'}, 
            body: JSON.stringify({usuario: u, senha: p}) 
        });
        
        const json = await res.json();
        
        if(res.ok && json.sucesso) {
            localStorage.setItem("ia_sessao", JSON.stringify(json));
            document.getElementById('telaLogin').classList.add('animate__animated', 'animate__fadeOutUp');
            setTimeout(()=> location.reload(), 400);
        } else {
            document.getElementById('msgLogin').innerText = json.mensagem || "Erro Genérico.";
        }
    } catch(e) { 
        document.getElementById('msgLogin').innerText = "Servidor Indisponível"; 
    } finally {
        btn.innerHTML = 'Acessar Sistema <i class="bi bi-arrow-right ms-2"></i>';
        btn.disabled = false;
    }
}

function logout() { localStorage.removeItem("ia_sessao"); location.reload(); }

function setupUI(user) {
    document.getElementById('telaLogin').classList.add('d-none');
    document.getElementById('telaApp').style.display = 'block';
    
    document.getElementById('userDisplay').innerText = user.usuario || user.login;
    
    if(user.tema) {
        document.body.className = '';
        if(user.tema !== 'dark') document.body.classList.add(`theme-${user.tema}`);
        if(document.getElementById('perfilTema')) document.getElementById('perfilTema').value = user.tema;
    }
    
    if(user.perms.search) document.getElementById('badgePermSearch').classList.remove('d-none');
    if(user.perms.add) document.getElementById('badgePermAdd').classList.remove('d-none');
    if(user.perms.del) document.getElementById('badgePermDel').classList.remove('d-none');
    if(user.perms.admin) document.getElementById('badgePermAdmin').classList.remove('d-none');
    
    if(document.getElementById('perfilEmail')) document.getElementById('perfilEmail').value = user.email || "";

    const navCad = document.getElementById('nav-cadastrar');
    const navAdm = document.getElementById('nav-admin');
    
    if (user.perms.add) navCad.classList.remove('d-none');
    if (user.perms.admin) navAdm.classList.remove('d-none');
}

function previewText(input, displayId, imgPreviewId) {
    const txt = document.getElementById(displayId);
    if(input.files && input.files[0]) {
        txt.innerText = window.i18n[currentLang]['lbl_attached'] + input.files[0].name;
        if(imgPreviewId) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.getElementById(imgPreviewId);
                img.src = e.target.result;
                img.style.display = 'block';
            }
            reader.readAsDataURL(input.files[0]);
        }
    } else {
        txt.innerText = window.i18n[currentLang]['lbl_select_file'];
        if(imgPreviewId) document.getElementById(imgPreviewId).style.display = 'none';
    }
}

// --- ATUALIZAR PERFIL ---
async function atualizarPerfil() {
    const s = JSON.parse(localStorage.getItem("ia_sessao"));
    const email = document.getElementById('perfilEmail').value;
    const tema = document.getElementById('perfilTema').value;
    const senhaAtual = document.getElementById('perfilSenhaAtual').value;
    const novaSenha = document.getElementById('perfilNovaSenha').value;
    const confirmaSenha = document.getElementById('perfilConfirmaSenha').value;

    if(novaSenha && !senhaAtual) return showToast("Digite a Senha Atual primeiro para poder criar uma Nova Senha.", "error");
    if(novaSenha && novaSenha !== confirmaSenha) return showToast("As senhas da confirmação não bateram.", "error");

    const payload = { novo_email: email, tema: tema };
    if(senhaAtual) payload.senha_atual = senhaAtual;
    if(novaSenha) payload.nova_senha = novaSenha;

    try {
        const res = await fetchAutenticado(`${API}/perfil/atualizar`, {
            method: 'POST', body: JSON.stringify(payload)
        });
        const json = await res.json();
        
        if(res.ok && !json.erro) {
            showToast(json.mensagem, "success");
            s.email = email;
            s.tema = tema;
            localStorage.setItem("ia_sessao", JSON.stringify(s));
            
            document.body.className = '';
            if(tema !== 'dark') document.body.classList.add(`theme-${tema}`);

            document.getElementById('perfilSenhaAtual').value = "";
            document.getElementById('perfilNovaSenha').value = "";
            document.getElementById('perfilConfirmaSenha').value = "";
        } else {
            showToast(json.erro || "Falha ao gravar perfil.", "error");
        }
    } catch (e) {
        // Handled in fetchAutenticado
    }
}

// --- RECUPERAÇÃO DE SENHA ---
function abrirModalRecuperacao() {
    document.getElementById('recStep1').style.display = 'block';
    document.getElementById('recStep2').style.display = 'none';
    document.getElementById('recEmail').value = "";
    modalRecuperacaoObj = new bootstrap.Modal(document.getElementById('modalRecuperacao'));
    modalRecuperacaoObj.show();
}

async function solicitarCodigo() {
    const email = document.getElementById('recEmail').value;
    const btn = document.getElementById('btnRecSolicitar');
    if(!email) return showToast("Insira o email", "error");
    
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Buscando email...'; btn.disabled = true;

    try {
        const res = await fetch(`${API}/recuperar/solicitar`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({email: email}) });
        const json = await res.json();
        
        if(res.ok && json.login) {
            usuarioRecuperacao = json.login;
            document.getElementById('recStep1').style.display = 'none';
            document.getElementById('recStep2').style.display = 'block';
            showToast("Sucesso no disparo em rede local ou Remota.", "success");
        } else {
            showToast(json.erro || "Email desconhecido neste hub neural", "error");
        }
    } catch { showToast("Problemas na conexão", "error"); }
    finally { btn.innerHTML = 'Disparar Token de Resgate <i class="bi bi-send ms-1"></i>'; btn.disabled = false; }
}

async function confirmarRecuperacao() {
    const codigo = document.getElementById('recCodigo').value;
    const novaSenha = document.getElementById('recNovaSenha').value;
    const confirmaSenha = document.getElementById('recConfirmaSenha').value;
    
    if(!codigo || !novaSenha) return showToast("Preencha o PIN e a nova Senha", "error");
    if(novaSenha !== confirmaSenha) return showToast("Senhas divergem!", "error");

    const btn = document.getElementById('btnRecConfirmar');
    btn.disabled = true;

    const res = await fetch(`${API}/recuperar/confirmar`, { 
        method: 'POST', headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify({ login: usuarioRecuperacao, codigo: codigo, nova_senha: novaSenha }) 
    });
    const json = await res.json();
    
    if(res.ok && json.mensagem) { 
        showToast("Senha recriada! Faca o login.", "success");
        modalRecuperacaoObj.hide(); 
    } else {
        showToast(json.erro || "PIN incorreto ou bloqueio local.", "error"); 
    }
    btn.disabled = false;
}

// --- ENGRENAGENS DE IA ---
async function buscar() {
    const file = document.getElementById('fotoBusca').files[0];
    if(!file) return showToast("Necessário capturar a foto primeiro.", "error");
    
    const btn = document.getElementById('btnBuscar');
    const uploadArea = document.getElementById('buscaUploadArea');
    
    btn.innerHTML = '<span class="spinner-grow spinner-grow-sm me-2"></span> Processando tensores...'; btn.disabled = true;
    uploadArea.classList.add("is-scanning"); // INICIA A ANIMAÇÃO DO SCANNER AQUI

    const form = new FormData(); 
    form.append('imagem', file); 
    
    document.getElementById('listaResultados').innerHTML = "";
    document.getElementById('titleResultados').style.display = 'none';
    
    try {
        const res = await fetchAutenticado(`${API}/buscar`, { method: 'POST', body: form });
        const json = await res.json();
        
        if(json.erro) throw new Error(json.erro);
        
        let html = "";
        document.getElementById('titleResultados').style.display = 'block';

        if(!json.resultados || json.resultados.length === 0) {
            html = '<div class="col-12"><div class="alert alert-warning border-0 bg-warning text-dark"><i class="bi bi-exclamation-triangle-fill me-2"></i>Nenhum produto correspondente cadastrado na rede. Tente ensinar essa referência no menu lateral.</div></div>';
        } else {
            json.resultados.forEach(item => {
                let acerto = Math.round(1000 - item.melhor_distancia);
                let isHighConf = acerto > 750;
                let bgConf = isHighConf ? "bg-success" : "bg-warning text-dark border-0";
                let borderConf = isHighConf ? "border-success" : "border-warning";
                
                html += `
                <div class="col-12 col-md-6">
                    <div class="match-card h-100 position-relative shadow-sm" style="border-left: 4px solid var(--${isHighConf ? 'success' : 'warning'});">
                        <span class="badge ${bgConf} badge-confianca shadow">${acerto} pts</span>
                        <div class="row g-0">
                            <div class="col-4">
                                <img src="${item.imagem_url}" class="thumb-img w-100">
                            </div>
                            <div class="col-8 d-flex align-items-center">
                                <div class="p-3">
                                    <h5 class="fw-bold mb-1 text-white">${item.nome}</h5>
                                    <p class="mb-2 text-muted small">
                                        <i class="bi bi-upc-scan me-1"></i>Código: <b>${item.codigo}</b>
                                        ${item.contagem_matches > 1 ? `<br><small class="text-accent"><i class="bi bi-images me-1"></i>+ ${item.contagem_matches - 1} foto(s) similares pareou</small>` : ''}
                                    </p>
                                    <div class="progress" style="height: 5px; width: 100px; background: rgba(255,255,255,0.1);">
                                      <div class="progress-bar ${bgConf}" style="width: ${acerto/10}%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>`;
            });
        }
        document.getElementById('listaResultados').innerHTML = html;
        showToast("Análise das Redes Neurais concluída.", "success");
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        btn.innerHTML = '<i class="bi bi-magic me-2"></i>Iniciar pesquisa'; btn.disabled = false;
        uploadArea.classList.remove("is-scanning"); // FINALIZA A ANIMAÇÃO DO SCANNER AQUI
    }
}

async function verificarProdutoExistente() {
    const cod = document.getElementById('cadCodigo').value;
    const inputNome = document.getElementById('cadNome');
    const btn = document.getElementById('btnCadastrar');
    const btnDel = document.getElementById('btnDelProduto');
    
    if(!cod) {
        inputNome.value = "";
        inputNome.disabled = false;
        btn.innerHTML = 'Registrar e Vetorizar <i class="bi bi-cloud-check ms-2"></i>';
        if(btnDel) btnDel.classList.add('d-none');
        return;
    }

    try {
        const res = await fetchAutenticado(`${API}/produto/${cod}`);
        const json = await res.json();
        
        if(res.ok && json.existe) {
            inputNome.value = json.nome;
            inputNome.disabled = true; // Impede alterar o nome do item pai
            btn.innerHTML = 'Adicionar Foto Extra ao Produto <i class="bi bi-images ms-2"></i>';
            if(btnDel) btnDel.classList.remove('d-none');
            showToast("SKU já existe na base. A imagem será atrelada a esse item.", "success");
        } else {
            if(inputNome.disabled) inputNome.value = ""; // limpa se era outro
            inputNome.disabled = false;
            btn.innerHTML = 'Registrar e Vetorizar <i class="bi bi-cloud-check ms-2"></i>';
            if(btnDel) btnDel.classList.add('d-none');
        }
    } catch {
        // Falha de rede silenciosa. Usuário apenas prossegue.
    }
}

async function cadastrar() {
    const file = document.getElementById('cadFoto').files[0];
    const cod = document.getElementById('cadCodigo').value;
    const nome = document.getElementById('cadNome').value;
    const btn = document.getElementById('btnCadastrar');
    const uploadArea = document.getElementById('cadUploadArea');
    const btnDel = document.getElementById('btnDelProduto');

    if(!file || !cod || !nome) return showToast("Por favor preencha Cadastro, Código, e Anexe a imagem.", "error");
    
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Vetorizando MobileNet...'; btn.disabled = true;
    if (uploadArea) uploadArea.classList.add("is-scanning");

    const form = new FormData(); 
    form.append('imagem', file); form.append('codigo', cod); form.append('nome', nome);
    
    try {
        const res = await fetchAutenticado(`${API}/cadastrar`, { method: 'POST', body: form });
        const json = await res.json();
        
        if(json.erro) throw new Error(json.erro);
        showToast("Imagem convertida e atrelada ao Cérebro IA com Sucesso!", "success");
        // Resetamos o form mas verificamos se ele ficou disabled
        document.getElementById('cadCodigo').value = ""; 
        document.getElementById('cadNome').value = "";
        document.getElementById('cadNome').disabled = false;
        if(btnDel) btnDel.classList.add('d-none');
        document.getElementById('txtCadPreview').innerText = window.i18n[currentLang]['lbl_select_file'];
        if (document.getElementById('imgCadPreview')) document.getElementById('imgCadPreview').style.display='none';
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        btn.innerHTML = 'Registrar e Vetorizar <i class="bi bi-cloud-check ms-2"></i>'; btn.disabled = false;
        if (uploadArea) uploadArea.classList.remove("is-scanning");
    }
}

async function deletarProduto() {
    const cod = document.getElementById('cadCodigo').value;
    if(!cod) return;
    
    if(!confirm(`Tem certeza que deseja apagar DEFINITIVAMENTE o produto '${cod}' e TODAS as suas imagens?`)) return;
    
    const btnDel = document.getElementById('btnDelProduto');
    btnDel.disabled = true;
    
    try {
        const res = await fetchAutenticado(`${API}/produto/${cod}`, { method: 'DELETE' });
        const json = await res.json();
        
        if(json.erro) throw new Error(json.erro);
        
        showToast(`Produto ${cod} e imagens deletadas com sucesso!`, "success");
        
        document.getElementById('cadCodigo').value = "";
        document.getElementById('cadNome').value = "";
        document.getElementById('cadNome').disabled = false;
        btnDel.classList.add('d-none');
        document.getElementById('btnCadastrar').innerHTML = 'Registrar e Vetorizar <i class="bi bi-cloud-check ms-2"></i>';
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        btnDel.disabled = false;
    }
}

// --- ADMIN ---
async function carregarUsuarios() {
    carregarConfigEmail();
    try {
        const res = await fetchAutenticado(`${API}/usuarios`);
        const lista = await res.json();
        
        if(lista.erro) throw new Error(lista.erro);

        let html = "";
        lista.forEach(u => {
            let limitTxt = window.i18n[currentLang]['lbl_unlimited'];
            let limite = u.limite_diario === 0 ? `<span class="badge bg-secondary">${limitTxt}</span>` : `${u.uso_hoje}/${u.limite_diario}`;
            let badges = "";
            if(u.perms.search) badges += '<span class="text-success mx-1 v-tooltip" title="Buscar"><i class="bi bi-search"></i></span>'; 
            if(u.perms.add) badges += '<span class="text-primary mx-1 v-tooltip" title="Salvar Info"><i class="bi bi-plus-circle"></i></span>'; 
            if(u.perms.del) badges += '<span class="text-danger mx-1 v-tooltip" title="Wipe"><i class="bi bi-trash"></i></span>'; 
            if(u.perms.admin) badges += '<span class="text-warning mx-1 v-tooltip" title="Master"><i class="bi bi-star-fill"></i></span>';
            
            const s = JSON.parse(localStorage.getItem("ia_sessao"));
            let btnDel = `<button onclick="delUser('${u.login}')" class="btn btn-sm btn-outline-danger px-2 py-1 lh-1"><i class="bi bi-person-x"></i></button>`;
            if(u.login === s.login) btnDel = `<span class="badge bg-dark">${window.i18n[currentLang]['lbl_logged_in']}</span>`;
            
            html += `<tr>
                <td class="fw-bold text-accent">${u.login}</td>
                <td>${limite}</td>
                <td class="fs-5">${badges}</td>
                <td>${btnDel}</td>
            </tr>`;
        });
        document.getElementById('tabelaUsuarios').innerHTML = html;
    } catch (error) {
        showToast("Não deu para baixar os usuários. Vocé é admin mesmo?", "error");
    }
}

async function salvarUsuario() {
    const dados = {
        login: document.getElementById('admLogin').value, 
        senha: document.getElementById('admPass').value,
        nome: document.getElementById('admNome').value, 
        email: document.getElementById('admEmail').value,
        limite_diario: document.getElementById('admLimite').value,
        perm_search: document.getElementById('permSearch').checked, 
        perm_add: document.getElementById('permAdd').checked,
        perm_del: document.getElementById('permDel').checked, 
        perm_admin: document.getElementById('permAdmin').checked
    };
    if(!dados.login) return showToast("Falta o login.", "error");

    try {
        const res = await fetchAutenticado(`${API}/usuarios`, { method: 'POST', body: JSON.stringify(dados) });
        const json = await res.json();
        if(json.erro) throw new Error(json.erro);
        
        showToast("Modificações salvas.", "success");
        carregarUsuarios();
        document.getElementById('admLogin').value = ""; document.getElementById('admPass').value = ""; document.getElementById('admEmail').value = "";
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function delUser(loginAlvo) {
    if(!confirm(`Confirmação Crítica: Deletar usuário '${loginAlvo}'?`)) return;
    try {
        const res = await fetchAutenticado(`${API}/usuarios/${loginAlvo}`, { method: 'DELETE' });
        if(res.ok) {
            showToast("Usuário deletado.", "success");
            carregarUsuarios(); 
        } else { throw new Error("Recusado pelo servidor"); }
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function zerar() { 
    if(!confirm("CUIDADO: APAGARÁ TODAS AS FOTOS E O INDICE DO BANCO! Continuar?")) return; 
    
    try {
        const res = await fetchAutenticado(`${API}/zerar`, { method: 'POST' }); 
        const json = await res.json();
        if(json.erro) throw new Error(json.erro);
        showToast("Wipe Concluído.", "success");
        setTimeout(()=> location.reload(), 2000);
    } catch (error) {
         showToast(error.message, "error");
    }
}

// --- CONFIGURAÇÃO DE EMAIL (ADMIN) ---
async function carregarConfigEmail() {
    try {
        const res = await fetchAutenticado(`${API}/email/config`);
        if (!res.ok) return;
        const config = await res.json();
        
        if (config.email) document.getElementById('smtpEmail').value = config.email;
        if (config.smtp) document.getElementById('smtpServer').value = config.smtp;
        if (config.porta) document.getElementById('smtpPort').value = config.porta;
        // Don't set password field for security, but the backend knows if it exists via has_senha (could be used to show a placeholder)
        if (config.has_senha) {
            document.getElementById('smtpPass').placeholder = "******** (Salva)";
        }
    } catch (e) {
        console.error("Falha ao carregar configuração de e-mail:", e);
    }
}

// --- CONFIGURAÇÃO DE EMAIL (ADMIN) ---
async function salvarConfigEmail() {
    const dados = {
        email: document.getElementById('smtpEmail').value,
        senha: document.getElementById('smtpPass').value,
        smtp: document.getElementById('smtpServer').value,
        porta: document.getElementById('smtpPort').value
    };

    if(!dados.email) return showToast("E-mail é obrigatório.", "error");

    try {
        const res = await fetchAutenticado(`${API}/email/config`, { method: 'POST', body: JSON.stringify(dados) });
        const json = await res.json();
        
        if(!res.ok || json.erro) throw new Error(json.erro || "Falha ao encriptar servidor.");
        
        showToast("Cofre bloqueado e credenciais de e-mail ativas!", "success");
        document.getElementById('smtpPass').value = ""; // Limpa a senha visualmente por segurança
    } catch (e) {
        showToast(e.message, "error");
    }
}
