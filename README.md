# 🌿 Terra Fértil Jardins — Sistema de Triagem de Prestadores (MVP)

> **Projeto de Extensão Acadêmica**  
> **Curso:** Engenharia da Computação  
> **Disciplina:** Tecnologia e Sociedade  
> **Parceiro:** Terra Fértil Jardins  

---

## 🎯 Objetivo do Projeto
Desenvolver um protótipo funcional e desacoplado que simula o **processo seletivo e o funil de triagem de jardineiros** para credenciamento na plataforma **Terra Fértil Jardins**. 

O objetivo é garantir que apenas prestadores idôneos, com maquinário próprio adequado e qualificação comprovada recebam o selo de parceiro credenciado antes de receberem chamados de clientes em condomínios e residências.

---

## 📥 Manual Rápido para o Parceiro / Empreendedor

Siga os 4 passos abaixo para baixar e testar a aplicação no seu computador:

### 1️⃣ Baixar o projeto do GitHub
1. No topo desta página do GitHub, clique no botão verde **`<> Code`**.
2. Clique na opção **`Download ZIP`**.
3. Aguarde o download do arquivo `projeto-triagem-main.zip` (ou similar) ser concluído.

### 2️⃣ Descompactar o arquivo baixado
1. Abra a sua pasta **Downloads** no computador.
2. Clique com o botão direito no arquivo ZIP baixado e selecione **"Extrair Tudo..."** (ou use WinRAR / 7-Zip).
3. Escolha uma pasta de destino fácil (ex: na sua Área de Trabalho ou Documentos) e conclua a extração.

### 3️⃣ Iniciar o Protótipo
1. Abra a pasta extraída.
2. Dê **dois cliques** no arquivo:
   👉 **`Iniciar_Triagem.bat`**
3. *Caso o Windows exiba o aviso de segurança azul ("O Windows protegeu o seu computador"):*
   - Clique em **"Mais informações"**
   - Em seguida, clique em **"Executar assim mesmo"**
4. *Caso seu computador ainda não tenha o Python instalado:*
   - O próprio inicializador vai perguntar se você deseja instalar automaticamente ou abrir o site oficial. Siga a instrução na tela (marcando a caixinha `"Add python.exe to PATH"` durante a instalação do instalador).
5. Uma janela preta do terminal abrirá (mantenha-a aberta enquanto usa) e seu **navegador padrão (Chrome, Edge ou Firefox) abrirá automaticamente** exibindo o sistema.

### 4️⃣ Como Encerrar o Teste
1. Feche a aba ou janela do navegador.
2. Volte na janela preta do terminal e pressione **`Ctrl + C`** ou simplesmente feche a janela preta.

---

## 📱 O Que Você Encontrará no Teste

A aplicação simula **dois celulares lado a lado** para você avaliar a experiência completa:

1. **📱 Celular da Esquerda (App do Jardineiro):**
   - Cadastro em 4 etapas (Dados Pessoais, Equipamentos/Maquinário, Experiência/Quiz Situacional, Documentos com certidão de antecedentes).
   - Consulta de candidatura por CPF.
   - Fluxo de reenvio com reabertura de etapa se um documento estiver ilegível.

2. **📱 Celular da Direita (App da Gestão Terra Fértil):**
   - Lista e busca de candidatos em análise.
   - Indicadores em tempo real.
   - Dossiê detalhado com ferramentas checadas e respostas do quiz.
   - Ações de aprovação, reprovação fundamentada ou solicitação de reenvio de documento.

---

## 📋 Questionário de Alinhamento Técnico (Para o Time Técnico do Parceiro)
Após a validação do fluxo com o empreendedor, estas perguntas ajudarão a alinhar a integração com a base existente:

1. **Stack Mobile:** Qual tecnologia foi usada no app atual? (Flutter, React Native, Kotlin/Swift nativo, PWA)?
2. **Backend & Nuvem:** Qual backend está em produção? (Node.js, Python, PHP, C# .NET, Firebase/Supabase)?
3. **Armazenamento de Documentos:** Onde ficam as fotos e documentos? (AWS S3, Google Cloud Storage, Firebase Storage)?
4. **Notificações:** Como os parceiros recebem avisos? (Push via Firebase/OneSignal, SMS ou WhatsApp API)?
5. **Autenticação:** O login do prestador é por SMS/OTP ou E-mail e Senha?
6. **Background Check:** A validação de certidão criminal será manual pela equipe ou pretendem integrar via API (ex: Idwall, Serpro, Caf)?

---

## 💻 Arquitetura Técnica
- **Backend:** Python com engine híbrida inteligente (tenta Flask; se ausente, faz fallback transparente para o servidor HTTP nativo do Python — zero dependência obrigatória).
- **Banco de Dados:** SQLite local (`triagem.db`) com migração e seed automático de dados para demonstração.
- **Frontend:** SPA responsiva (HTML5, CSS3 Mobile-First, Vanilla JavaScript, Lucide SVG Icons offline).
- **Segurança & LGPD:** Proteção contra injeção SQL com consultas parametrizadas, sanitização XSS, escuta estrita em `127.0.0.1` e consentimento explícito LGPD (Lei 13.709/2018).
