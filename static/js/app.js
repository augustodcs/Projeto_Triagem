// ====================================================
// SEGURANÇA & SANITIZAÇÃO (Anti-XSS / OWASP)
// ====================================================
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ====================================================
// ESTADO GLOBAL DA APLICAÇÃO
// ====================================================
let currentStep = 1;
let currentMobileFilter = 'TODOS';
let activeGestorCandidateId = null;
let activeCandidateInStatusView = null;
let candidatesCache = [];
let pendingDecisionStatus = null;

// ====================================================
// INICIALIZAÇÃO
// ====================================================
document.addEventListener('DOMContentLoaded', () => {
  setupMasks();
  fetchStats();
  fetchCandidates();
});

// ====================================================
// NAVEGAÇÃO DE MODOS (APP JARDINEIRO vs APP GESTÃO vs SOBRE)
// ====================================================
function switchMode(mode) {
  document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));

  if (mode === 'mobile') {
    document.getElementById('tabBtnMobile').classList.add('active');
    document.getElementById('viewMobile').classList.add('active');
  } else if (mode === 'admin') {
    document.getElementById('tabBtnAdmin').classList.add('active');
    document.getElementById('viewAdmin').classList.add('active');
    fetchStats();
    fetchCandidates();
  } else if (mode === 'about') {
    document.getElementById('tabBtnAbout').classList.add('active');
    document.getElementById('viewAbout').classList.add('active');
  }
}

// ====================================================
// APP DO JARDINEIRO: WIZARD DE CADASTRO
// ====================================================
function goToStep(step) {
  if (step === 2 && currentStep === 1) {
    const nome = document.getElementById('cad_nome').value.trim();
    const cpf = document.getElementById('cad_cpf').value.trim();
    const tel = document.getElementById('cad_telefone').value.trim();
    if (!nome || !cpf || !tel) {
      showToast('Por favor, preencha Nome, CPF e WhatsApp antes de avançar.');
      return;
    }
  }

  currentStep = step;
  
  document.querySelectorAll('#candidateRegisterView .wizard-step').forEach(el => el.classList.remove('active'));
  
  const targetStep = document.getElementById(`step${step}`);
  if (targetStep) {
    targetStep.classList.add('active');
  }

  const progressPercent = (step / 4) * 100;
  document.getElementById('mobileProgressBar').style.width = `${progressPercent}%`;
  document.getElementById('mobileStepPill').innerText = `Etapa ${step} de 4`;

  const titles = {
    1: 'Dados Pessoais e Região',
    2: 'Ferramental e Logística',
    3: 'Experiência & Teste Técnico',
    4: 'Documentação & Antecedentes'
  };
  document.getElementById('mobileStepTitle').innerText = titles[step] || 'Cadastro de Parceiro';
}

function toggleMeiField(checked) {
  const group = document.getElementById('groupMeiCnpj');
  group.style.display = checked ? 'block' : 'none';
}

function simularTrocaArquivo(elementId, novoNome) {
  const el = document.getElementById(elementId);
  if (el) {
    el.innerText = novoNome;
    showToast(`Arquivo selecionado: ${novoNome}`);
  }
}

async function submitCandidate() {
  const btn = document.getElementById('btnSubmitCandidate');
  btn.disabled = true;
  btn.innerHTML = 'Enviando candidatura...';

  const nome = document.getElementById('cad_nome').value.trim();
  const cpf = document.getElementById('cad_cpf').value.trim();
  const data_nascimento = document.getElementById('cad_nasc').value;
  const telefone = document.getElementById('cad_telefone').value.trim();
  const email = document.getElementById('cad_email').value.trim();
  const cidade = document.getElementById('cad_cidade').value.trim();
  const bairro = document.getElementById('cad_bairro').value.trim();
  const raio_atendimento = document.getElementById('cad_raio').value;

  const meio_transporte = document.getElementById('cad_transporte').value;
  const recolhe_residuos = document.getElementById('cad_residuos').checked;

  const ferramentas = [];
  document.querySelectorAll('input[name="ferramenta"]:checked').forEach(cb => {
    ferramentas.push(cb.value);
  });

  const tempo_experiencia = document.getElementById('cad_experiencia').value;

  // Quiz
  const q1 = document.querySelector('input[name="quiz_q1"]:checked')?.value || '';
  const q2 = document.querySelector('input[name="quiz_q2"]:checked')?.value || '';
  const q3 = document.querySelector('input[name="quiz_q3"]:checked')?.value || '';

  // Documentos
  const doc_frente = document.getElementById('fileNameDoc').innerText;
  const doc_selfie = document.getElementById('fileNameSelfie').innerText;
  const certidao_antecedentes = document.getElementById('fileNameAntecedentes').innerText;

  const possui_mei = document.getElementById('cad_possui_mei').checked;
  const cnpj_mei = document.getElementById('cad_cnpj').value.trim();
  const termos_aceitos = document.getElementById('cad_termos').checked;

  const payload = {
    nome,
    cpf,
    data_nascimento,
    telefone,
    email,
    cidade,
    bairro,
    raio_atendimento,
    meio_transporte,
    recolhe_residuos,
    ferramentas,
    tempo_experiencia,
    especialidades: ["Corte de grama", "Poda", "Manutenção"],
    quiz_respostas: { q1, q2, q3 },
    doc_frente,
    doc_selfie,
    certidao_antecedentes,
    possui_mei,
    cnpj_mei,
    termos_aceitos
  };

  try {
    const res = await fetch('/api/candidatos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || 'Erro ao enviar cadastro.');
      btn.disabled = false;
      btn.innerHTML = 'Concluir e Enviar para Triagem';
      return;
    }

    showToast(`Candidatura ${data.protocolo} registrada com sucesso!`);
    fetchStats();
    fetchCandidates();

    // Redireciona diretamente para a tela de acompanhamento do status no celular
    showCandidateStatusByCpf(cpf);

  } catch (err) {
    console.error(err);
    showToast('Falha na comunicação com o servidor.');
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Concluir e Enviar para Triagem';
  }
}

// ====================================================
// APP DO JARDINEIRO: TELA DE STATUS & REENVIO DE DOCS
// ====================================================
async function showCandidateStatusByCpf(termo) {
  try {
    const res = await fetch('/api/consultar-status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ termo })
    });

    const data = await res.json();
    if (!res.ok || !data.found) {
      showToast(data.message || 'Candidato não localizado.');
      return;
    }

    const c = data.candidato;
    activeCandidateInStatusView = c;

    // Alterna subview no celular do jardineiro
    document.getElementById('candidateRegisterView').classList.remove('active');
    document.getElementById('candidateStatusView').classList.add('active');

    // Preenche dados do cabeçalho
    document.getElementById('statusCandidateName').innerText = c.nome;
    document.getElementById('statusCandidateProtocol').innerText = c.protocolo;
    document.getElementById('statusCandidateDate').innerText = c.data_cadastro.split(' ')[0];

    // Card de Status
    const statusCard = document.getElementById('statusMainCard');
    const badgeLg = document.getElementById('statusBadgeLg');
    const title = document.getElementById('statusMainTitle');
    const expl = document.getElementById('statusExplanationText');

    const boxReenvio = document.getElementById('boxReenvioDocumento');
    const boxAprovado = document.getElementById('boxAprovadoCelebracao');
    const boxReprovado = document.getElementById('boxReprovadoFeedback');

    // Reseta visibilidade dos boxes condicionais
    boxReenvio.style.display = 'none';
    boxAprovado.style.display = 'none';
    boxReprovado.style.display = 'none';
    statusCard.className = 'candidate-status-card';

    if (c.status === 'PENDENCIA_DOC') {
      statusCard.classList.add('status-pendente');
      badgeLg.innerText = '⚠️ PENDÊNCIA DE DOCUMENTAÇÃO';
      title.innerText = 'Ação necessária no seu cadastro';
      expl.innerHTML = `<strong>Mensagem da Terra Fértil:</strong><br>${escapeHtml(c.motivo_status || 'Um documento necessita de correção.')}`;
      boxReenvio.style.display = 'block';

      // Reseta formulário de reenvio
      document.getElementById('resubFileNameDisplay').innerText = 'Toque aqui para selecionar foto nítida';
      document.getElementById('resubComment').value = '';

    } else if (c.status === 'APROVADO') {
      statusCard.classList.add('status-aprovado');
      badgeLg.innerText = '✓ PARCEIRO HOMOLOGADO';
      title.innerText = 'Credenciamento Aprovado!';
      expl.innerText = c.motivo_status || 'Seu perfil foi validado e você já pode receber serviços.';
      boxAprovado.style.display = 'block';

    } else if (c.status === 'REPROVADO') {
      statusCard.classList.add('status-reprovado');
      badgeLg.innerText = '✕ INSCRIÇÃO NÃO APROVADA';
      title.innerText = 'Critérios não atendidos';
      expl.innerText = c.motivo_status || 'Inscrição reprovada na triagem inicial.';
      boxReprovado.style.display = 'block';
      document.getElementById('rejectionDetailText').innerText = c.motivo_status || 'Critérios mínimos não preenchidos.';

    } else { // EM_ANALISE
      statusCard.classList.add('status-analise');
      badgeLg.innerText = '⏳ EM ANÁLISE DOCUMENTAL';
      title.innerText = 'Candidatura em Avaliação';
      expl.innerText = c.motivo_status || 'Nossa central está analisando seus documentos e ferramentas. Prazo médio: 24h úteis.';
    }

    // Resumo
    document.getElementById('sumPhone').innerText = c.telefone;
    document.getElementById('sumCity').innerText = `${c.cidade} - ${c.bairro}`;
    document.getElementById('sumTransport').innerText = c.meio_transporte;
    document.getElementById('sumTools').innerText = c.ferramentas ? c.ferramentas.join(', ') : 'Nenhuma';
    document.getElementById('sumQuiz').innerText = `${c.quiz_nota}%`;

  } catch (err) {
    console.error(err);
    showToast('Erro ao carregar status do candidato.');
  }
}

function simularArquivoReenvio() {
  const tipo = document.getElementById('resubDocType').value;
  let nomeArquivo = 'novo_rg_frente_verso_sem_reflexo.jpg';
  if (tipo === 'doc_selfie') nomeArquivo = 'nova_selfie_nitida_comprovacao.jpg';
  if (tipo === 'certidao_antecedentes') nomeArquivo = 'nova_certidao_antecedentes_atualizada.pdf';

  document.getElementById('resubFileNameDisplay').innerText = `✓ ${nomeArquivo} (Pronto para envio)`;
  showToast(`Arquivo anexado: ${nomeArquivo}`);
}

async function submitDocumentResubmission() {
  if (!activeCandidateInStatusView) return;

  const btn = document.getElementById('btnSendResubmission');
  btn.disabled = true;
  btn.innerText = 'Enviando documento...';

  const doc_tipo = document.getElementById('resubDocType').value;
  const fileNameText = document.getElementById('resubFileNameDisplay').innerText;
  const comentario = document.getElementById('resubComment').value.trim();

  let arquivo_nome = 'documento_corrigido.jpg';
  if (fileNameText.includes('(')) {
    arquivo_nome = fileNameText.replace('✓ ', '').split(' (')[0];
  } else {
    arquivo_nome = `novo_${doc_tipo}_atualizado.jpg`;
  }

  try {
    const res = await fetch(`/api/candidatos/${activeCandidateInStatusView.id}/reenviar-docs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        doc_tipo,
        arquivo_nome,
        comentario
      })
    });

    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || 'Erro ao reenviar documento.');
      return;
    }

    showToast('Documento reenviado com sucesso!');
    fetchStats();
    fetchCandidates();

    // Atualiza a tela de status do próprio candidato em tempo real
    showCandidateStatusByCpf(activeCandidateInStatusView.cpf);

  } catch (err) {
    console.error(err);
    showToast('Falha na comunicação com o servidor.');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Reenviar Documento para Nova Análise`;
  }
}

function backToRegisterView() {
  document.getElementById('candidateStatusView').classList.remove('active');
  document.getElementById('candidateRegisterView').classList.add('active');
  document.getElementById('cad_nome').value = '';
  document.getElementById('cad_cpf').value = '';
  document.getElementById('cad_telefone').value = '';
  document.getElementById('cad_email').value = '';
  document.getElementById('cad_bairro').value = '';
  goToStep(1);
}

// Modal de Consulta
function toggleMobileConsultModal() {
  document.getElementById('modalConsultarStatus').classList.toggle('active');
}

// Modal de Termos LGPD
function toggleLgpdModal() {
  const modal = document.getElementById('modalLgpdTerms');
  if (modal) modal.classList.toggle('active');
}

function preencherConsulta(cpf) {
  document.getElementById('consultTermoInput').value = cpf;
}

function realizarConsultaStatusModal() {
  const termo = document.getElementById('consultTermoInput').value.trim();
  if (!termo) {
    showToast('Digite o CPF ou número de protocolo.');
    return;
  }
  toggleMobileConsultModal();
  showCandidateStatusByCpf(termo);
}

// ====================================================
// APP DA GESTÃO TERRA FÉRTIL (MOBILE-FIRST)
// ====================================================
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    
    document.getElementById('kpiEmAnalise').innerText = data.em_analise;
    document.getElementById('kpiPendentes').innerText = data.pendencia_doc;
    document.getElementById('kpiAprovados').innerText = data.aprovado;
    document.getElementById('kpiReprovados').innerText = data.reprovado;

    const badge = document.getElementById('badgePendingCount');
    badge.innerText = data.em_analise;
    badge.style.display = data.em_analise > 0 ? 'inline-block' : 'none';
  } catch (err) {
    console.error('Erro ao buscar stats:', err);
  }
}

async function fetchCandidates() {
  try {
    const res = await fetch(`/api/candidatos?status=${currentMobileFilter}`);
    candidatesCache = await res.json();
    renderCandidateCardsMobile(candidatesCache);
  } catch (err) {
    console.error('Erro ao buscar candidatos:', err);
  }
}

function renderCandidateCardsMobile(list) {
  const container = document.getElementById('gestorCandidateCardsContainer');
  if (list.length === 0) {
    container.innerHTML = `<div class="text-center p-3 text-muted text-xs">Nenhum parceiro encontrado nesta categoria.</div>`;
    return;
  }

  container.innerHTML = list.map(c => {
    const safeNome = escapeHtml(c.nome);
    const safeProtocolo = escapeHtml(c.protocolo);
    const safeCidade = escapeHtml(c.cidade);
    const safeBairro = escapeHtml(c.bairro);
    const safeStatus = escapeHtml(c.status);
    const ferCount = c.ferramentas ? c.ferramentas.length : 0;
    const toolsPreview = c.ferramentas && ferCount > 0 
      ? `<span class="tool-tag">${escapeHtml(c.ferramentas[0])}</span> ${ferCount > 1 ? `<span class="tool-tag">+${ferCount - 1}</span>` : ''}`
      : `<span class="tool-tag" style="background:#fee2e2; color:#991b1b;">Sem ferramentas</span>`;

    let scoreClass = 'low';
    if (c.quiz_nota >= 80) scoreClass = 'high';
    else if (c.quiz_nota >= 50) scoreClass = 'mid';

    return `
      <div class="cand-card-mobile" onclick="openGestorDetailView(${Number(c.id)})">
        <div class="cand-card-top">
          <div>
            <div class="cand-card-title">${safeNome}</div>
            <div class="cand-card-protocol">${safeProtocolo} • ${safeCidade} (${safeBairro})</div>
          </div>
          <span class="badge-status ${safeStatus}">${safeStatus.replace('_', ' ')}</span>
        </div>
        <div class="cand-card-sub">
          ${toolsPreview}
        </div>
        <div class="cand-card-meta">
          <span class="text-xs text-muted">Quiz: <strong class="score-badge ${scoreClass}">${Number(c.quiz_nota)}%</strong></span>
          <span class="text-xs text-primary font-bold">Abrir Dossiê →</span>
        </div>
      </div>
    `;
  }).join('');
}

function setMobileFilter(status) {
  currentMobileFilter = status;
  document.querySelectorAll('#gestorFilterChips .gestor-chip').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-status') === status);
  });
  fetchCandidates();
}

function filterCandidatesMobile() {
  const query = document.getElementById('gestorSearchInput').value.toLowerCase().trim();
  if (!query) {
    renderCandidateCardsMobile(candidatesCache);
    return;
  }

  const filtered = candidatesCache.filter(c => 
    c.nome.toLowerCase().includes(query) ||
    c.cpf.includes(query) ||
    c.protocolo.toLowerCase().includes(query) ||
    c.cidade.toLowerCase().includes(query) ||
    c.bairro.toLowerCase().includes(query)
  );

  renderCandidateCardsMobile(filtered);
}

// ====================================================
// APP DA GESTÃO: DOSSIÊ COMPLETO & DECISÃO COM TEMPLATES
// ====================================================
async function openGestorDetailView(id) {
  activeGestorCandidateId = id;
  try {
    const res = await fetch(`/api/candidatos/${id}`);
    const c = await res.json();

    // Alterna subview no celular do gestor
    document.getElementById('gestorListView').classList.remove('active');
    document.getElementById('gestorDetailView').classList.add('active');

    // Preenche dados
    document.getElementById('gdProtocol').innerText = c.protocolo;
    document.getElementById('gdNome').innerText = c.nome;
    document.getElementById('gdAvatar').innerText = c.nome.split(' ').map(n => n[0]).slice(0, 2).join('');
    document.getElementById('gdRegiao').innerText = `${c.cidade} • ${c.bairro} (${c.raio_atendimento} km raio)`;

    // Status strip
    const badge = document.getElementById('gdStatusBadge');
    badge.className = `badge-status ${c.status}`;
    badge.innerText = c.status.replace('_', ' ');
    document.getElementById('gdStatusMotivo').innerText = c.motivo_status || 'Sem pendências.';

    // WhatsApp link
    const rawTel = c.telefone.replace(/\D/g, '');
    document.getElementById('gdWhatsappBtn').href = `https://wa.me/55${rawTel}?text=Olá%20${encodeURIComponent(c.nome)},%20somos%20da%20Terra%20Fértil%20Jardins!`;

    // Maquinário
    document.getElementById('gdTransporte').innerText = c.meio_transporte;
    document.getElementById('gdResiduos').innerText = c.recolhe_residuos ? 'Sim (ensaca e recolhe)' : 'Não';
    
    const toolsContainer = document.getElementById('gdFerramentasList');
    if (c.ferramentas && c.ferramentas.length > 0) {
      toolsContainer.innerHTML = c.ferramentas.map(t => `<span class="tool-tag">${escapeHtml(t)}</span>`).join('');
    } else {
      toolsContainer.innerHTML = '<span class="text-xs" style="color:#ef4444;">Nenhuma ferramenta informada</span>';
    }

    // Documentos & Antecedentes
    document.getElementById('gdDocFrente').innerText = c.doc_frente || 'cnh_frente.jpg';
    document.getElementById('gdDocSelfie').innerText = c.doc_selfie || 'selfie.jpg';
    document.getElementById('gdDocAntecedentes').innerText = c.certidao_antecedentes || 'certidao_antecedentes_declarados.pdf';
    document.getElementById('gdDocMei').innerText = c.possui_mei ? `MEI Ativo: ${c.cnpj_mei || 'Sim'}` : 'Não possui MEI';

    // Quiz
    const quizScore = document.getElementById('gdQuizScore');
    quizScore.innerText = `${c.quiz_nota}%`;
    quizScore.className = `score-badge ${c.quiz_nota >= 80 ? 'high' : c.quiz_nota >= 50 ? 'mid' : 'low'}`;

    // Anotações internas
    document.getElementById('gdObsInternas').value = c.observacoes_internas || '';

  } catch (err) {
    console.error('Erro ao abrir dossiê mobile:', err);
    showToast('Erro ao carregar dossiê do parceiro.');
  }
}

function closeGestorDetailView() {
  document.getElementById('gestorDetailView').classList.remove('active');
  document.getElementById('gestorListView').classList.add('active');
  activeGestorCandidateId = null;
  closeDecisionSheet();
}

// ACTION SHEET DE DECISÃO (SEM PROMPT DO NAVEGADOR)
function openDecisionSheet(status) {
  pendingDecisionStatus = status;
  const sheet = document.getElementById('decisionActionSheet');
  const title = document.getElementById('sheetTitle');
  const chipsContainer = document.getElementById('sheetQuickChips');
  const textarea = document.getElementById('sheetMessageInput');

  chipsContainer.innerHTML = '';

  if (status === 'PENDENCIA_DOC') {
    title.innerText = '⚠️ Solicitar Correção de Documentos';
    const presets = [
      "Foto do documento ilegível ou com corte no número",
      "Selfie sem o documento oficial em mãos",
      "Certidão de antecedentes vencida ou não anexada"
    ];
    presets.forEach(p => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'quick-chip';
      chip.innerText = p;
      chip.onclick = () => { textarea.value = p; };
      chipsContainer.appendChild(chip);
    });
    textarea.value = presets[0];

  } else if (status === 'REPROVADO') {
    title.innerText = '✕ Reprovar Candidato';
    const presets = [
      "Não possui as ferramentas de corte mínimas exigidas (roçadeira/podador)",
      "Fora da praça de atendimento e raio de cobertura da Terra Fértil",
      "Insuficiência de requisitos operacionais básicos"
    ];
    presets.forEach(p => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'quick-chip';
      chip.innerText = p;
      chip.onclick = () => { textarea.value = p; };
      chipsContainer.appendChild(chip);
    });
    textarea.value = presets[0];

  } else if (status === 'APROVADO') {
    title.innerText = '✓ Aprovar e Credenciar Parceiro';
    const presets = [
      "Documentação e antecedentes conferidos com sucesso. Apto a receber chamados.",
      "Profissional com maquinário completo e nota máxima no teste de segurança."
    ];
    presets.forEach(p => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'quick-chip';
      chip.innerText = p;
      chip.onclick = () => { textarea.value = p; };
      chipsContainer.appendChild(chip);
    });
    textarea.value = presets[0];
  }

  sheet.classList.add('active');
}

function closeDecisionSheet() {
  document.getElementById('decisionActionSheet').classList.remove('active');
  pendingDecisionStatus = null;
}

async function confirmDecisionFromSheet() {
  if (!activeGestorCandidateId || !pendingDecisionStatus) return;

  const motivo = document.getElementById('sheetMessageInput').value.trim();
  const obs = document.getElementById('gdObsInternas').value.trim();

  try {
    const res = await fetch(`/api/candidatos/${activeGestorCandidateId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: pendingDecisionStatus,
        motivo: motivo || 'Decisão registrada pela gestão.',
        observacoes: obs
      })
    });

    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || 'Erro ao registrar decisão.');
      return;
    }

    showToast(`Decisão salva: Parceiro ${pendingDecisionStatus.replace('_', ' ')}.`);
    closeDecisionSheet();
    
    // Atualiza o dossiê com o novo status
    openGestorDetailView(activeGestorCandidateId);
    fetchStats();
    fetchCandidates();

  } catch (err) {
    console.error(err);
    showToast('Falha ao registrar decisão.');
  }
}

async function resetDemoData() {
  if (!confirm('Deseja restaurar a base de candidatos de exemplo?')) return;

  try {
    const res = await fetch('/api/reset-demo', { method: 'POST' });
    const data = await res.json();
    showToast(data.message || 'Dados restaurados!');
    fetchStats();
    fetchCandidates();
    if (activeGestorCandidateId) closeGestorDetailView();
  } catch (err) {
    showToast('Erro ao restaurar dados.');
  }
}

// ====================================================
// MÁSCARAS & UTILITÁRIOS
// ====================================================
function setupMasks() {
  const cpfInput = document.getElementById('cad_cpf');
  if (cpfInput) {
    cpfInput.addEventListener('input', e => {
      let v = e.target.value.replace(/\D/g, '');
      if (v.length > 11) v = v.slice(0, 11);
      if (v.length > 9) v = v.replace(/^(\d{3})(\d{3})(\d{3})(\d{1,2})$/, '$1.$2.$3-$4');
      else if (v.length > 6) v = v.replace(/^(\d{3})(\d{3})(\d{1,3})$/, '$1.$2.$3');
      else if (v.length > 3) v = v.replace(/^(\d{3})(\d{1,3})$/, '$1.$2');
      e.target.value = v;
    });
  }

  const telInput = document.getElementById('cad_telefone');
  if (telInput) {
    telInput.addEventListener('input', e => {
      let v = e.target.value.replace(/\D/g, '');
      if (v.length > 11) v = v.slice(0, 11);
      if (v.length > 10) v = v.replace(/^(\d{2})(\d{5})(\d{4})$/, '($1) $2-$3');
      else if (v.length > 6) v = v.replace(/^(\d{2})(\d{4})(\d{0,4})$/, '($1) $2-$3');
      else if (v.length > 2) v = v.replace(/^(\d{2})(\d{0,5})$/, '($1) $2');
      e.target.value = v;
    });
  }
}

function showToast(msg) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerText = msg;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3500);
}
