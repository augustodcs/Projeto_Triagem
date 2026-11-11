import os
import sys
import json
import random
import webbrowser
import threading
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from database import get_connection, init_db, seed_demo_data

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

# ====================================================
# LÓGICA DE NEGÓCIO COMPARTILHADA (CORE DA APLICAÇÃO)
# ====================================================
def query_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'EM_ANALISE' THEN 1 ELSE 0 END) as em_analise,
            SUM(CASE WHEN status = 'APROVADO' THEN 1 ELSE 0 END) as aprovado,
            SUM(CASE WHEN status = 'PENDENCIA_DOC' THEN 1 ELSE 0 END) as pendencia_doc,
            SUM(CASE WHEN status = 'REPROVADO' THEN 1 ELSE 0 END) as reprovado,
            AVG(quiz_nota) as media_quiz
        FROM candidatos
    ''')
    row = cursor.fetchone()
    conn.close()
    return {
        "total": row['total'] or 0,
        "em_analise": row['em_analise'] or 0,
        "aprovado": row['aprovado'] or 0,
        "pendencia_doc": row['pendencia_doc'] or 0,
        "reprovado": row['reprovado'] or 0,
        "media_quiz": round(row['media_quiz'] or 0, 1)
    }

def query_candidatos(status=None, search=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM candidatos WHERE 1=1"
    params = []
    
    if status and status != 'TODOS':
        query += " AND status = ?"
        params.append(status)
        
    if search:
        query += " AND (nome LIKE ? OR cpf LIKE ? OR cidade LIKE ? OR protocolo LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])
        
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    candidatos = []
    for r in rows:
        item = dict(r)
        item['ferramentas'] = json.loads(item['ferramentas']) if item['ferramentas'] else []
        item['especialidades'] = json.loads(item['especialidades']) if item['especialidades'] else []
        item['portfolio_fotos'] = json.loads(item['portfolio_fotos']) if item['portfolio_fotos'] else []
        item['quiz_respostas'] = json.loads(item['quiz_respostas']) if item['quiz_respostas'] else {}
        candidatos.append(item)
        
    conn.close()
    return candidatos

def query_candidato_by_id(id_cand):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidatos WHERE id = ?", (id_cand,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    item = dict(row)
    item['ferramentas'] = json.loads(item['ferramentas']) if item['ferramentas'] else []
    item['especialidades'] = json.loads(item['especialidades']) if item['especialidades'] else []
    item['portfolio_fotos'] = json.loads(item['portfolio_fotos']) if item['portfolio_fotos'] else []
    item['quiz_respostas'] = json.loads(item['quiz_respostas']) if item['quiz_respostas'] else {}
    return item

def process_create_candidato(data):
    nome = data.get('nome', '').strip()[:100]
    cpf = data.get('cpf', '').strip()[:14]
    telefone = data.get('telefone', '').strip()[:20]
    email = data.get('email', '').strip()[:100]
    cidade = data.get('cidade', 'São Paulo').strip()[:60]
    bairro = data.get('bairro', '').strip()[:60]
    
    try:
        raio_atendimento = max(5, min(int(data.get('raio_atendimento', 20)), 100))
    except (ValueError, TypeError):
        raio_atendimento = 20
    
    if not nome or not cpf or not telefone:
        return {"error": "Campos obrigatórios (Nome, CPF, Telefone) não preenchidos."}, 400
        
    ano = datetime.now().year
    sufixo = random.randint(2000, 9999)
    protocolo = f"TF-{ano}-{sufixo}"
    
    quiz_respostas = data.get('quiz_respostas', {})
    acertos = 0
    if quiz_respostas.get('q1') == 'b': acertos += 1
    if quiz_respostas.get('q2') == 'c': acertos += 1
    if quiz_respostas.get('q3') == 'a': acertos += 1
    quiz_nota = int((acertos / 3.0) * 100)
    
    ferramentas = data.get('ferramentas', [])
    if not isinstance(ferramentas, list): ferramentas = []
    ferramentas = [str(f)[:60] for f in ferramentas[:15]]
    
    meio_transporte = str(data.get('meio_transporte', ''))[:50]
    
    status = 'EM_ANALISE'
    motivo = "Cadastro recebido com sucesso. Aguardando conferência do gestor."
    
    if len(ferramentas) == 0:
        status = 'REPROVADO'
        motivo = "Reprovado automaticamente no filtro: o candidato não declarou possuir nenhum equipamento de trabalho básico."
    elif meio_transporte == 'A pé / Transporte público' and 'Roçadeira a gasolina' in ferramentas:
        motivo = "Alerta: candidato usa transporte público mas declarou ter roçadeira a gasolina. Requer averiguação de logística."

    data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    doc_frente = str(data.get('doc_frente', 'documento_enviado.jpg'))[:100]
    doc_selfie = str(data.get('doc_selfie', 'selfie_enviada.jpg'))[:100]
    comprovante_residencia = str(data.get('comprovante_residencia', 'residencia_enviada.pdf'))[:100]
    certidao_antecedentes = str(data.get('certidao_antecedentes', 'antecedentes_declarados.pdf'))[:100]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO candidatos (
        protocolo, data_cadastro, status, motivo_status,
        nome, cpf, rg, data_nascimento, telefone, email, cidade, bairro, raio_atendimento,
        meio_transporte, ferramentas, recolhe_residuos,
        tempo_experiencia, especialidades, quiz_nota, quiz_respostas, portfolio_fotos,
        doc_frente, doc_selfie, comprovante_residencia, certidao_antecedentes,
        possui_mei, cnpj_mei, termos_aceitos, observacoes_internas
    ) VALUES (
        ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?
    )
    ''', (
        protocolo, data_cadastro, status, motivo,
        nome, cpf, str(data.get('rg', ''))[:20], str(data.get('data_nascimento', ''))[:10],
        telefone, email, cidade, bairro, raio_atendimento,
        meio_transporte, json.dumps(ferramentas, ensure_ascii=False),
        1 if data.get('recolhe_residuos') else 0,
        str(data.get('tempo_experiencia', '1 a 3 anos'))[:30],
        json.dumps(data.get('especialidades', []), ensure_ascii=False),
        quiz_nota, json.dumps(quiz_respostas, ensure_ascii=False),
        json.dumps(data.get('portfolio_fotos', []), ensure_ascii=False),
        doc_frente, doc_selfie, comprovante_residencia, certidao_antecedentes,
        1 if data.get('possui_mei') else 0, str(data.get('cnpj_mei', ''))[:20],
        1 if data.get('termos_aceitos') else 0,
        "Cadastro realizado via Simulador do App do Jardineiro (LGPD Conforme)."
    ))
    
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "id": novo_id,
        "protocolo": protocolo,
        "status": status,
        "motivo": motivo,
        "quiz_nota": quiz_nota
    }, 201

def process_update_status(id_cand, data):
    novo_status = data.get('status')
    motivo = str(data.get('motivo', ''))[:300].strip()
    observacoes = str(data.get('observacoes', ''))[:500].strip()
    
    if novo_status not in ['EM_ANALISE', 'APROVADO', 'REPROVADO', 'PENDENCIA_DOC']:
        return {"error": "Status inválido"}, 400
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE candidatos 
        SET status = ?, motivo_status = ?, observacoes_internas = ?
        WHERE id = ?
    ''', (novo_status, motivo, observacoes, id_cand))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Status atualizado para {novo_status}"}, 200

def process_reenviar_docs(id_cand, data):
    doc_tipo = data.get('doc_tipo', 'doc_frente')
    novo_arquivo = str(data.get('arquivo_nome', 'novo_documento.jpg'))[:100].strip()
    comentario = str(data.get('comentario', ''))[:250].strip()
    
    mapeamento_docs = {
        'doc_frente': 'doc_frente',
        'doc_selfie': 'doc_selfie',
        'certidao_antecedentes': 'certidao_antecedentes'
    }
    if doc_tipo not in mapeamento_docs:
        return {"error": "Tipo de documento inválido para reenvio."}, 400
        
    coluna_doc = mapeamento_docs[doc_tipo]
    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
    novo_motivo = f"Documento corrigido e reenviado pelo candidato em {agora}."
    if comentario:
        novo_motivo += f" Observação do candidato: \"{comentario}\""
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT observacoes_internas FROM candidatos WHERE id = ?", (id_cand,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": "Candidato não encontrado"}, 404
        
    obs_antiga = row['observacoes_internas'] or ''
    obs_nova = f"{obs_antiga}\n[{agora}] O candidato reenviou o documento '{novo_arquivo}' ({doc_tipo})."
    
    cursor.execute(f'''
        UPDATE candidatos 
        SET {coluna_doc} = ?, status = 'EM_ANALISE', motivo_status = ?, observacoes_internas = ?
        WHERE id = ?
    ''', (novo_arquivo, novo_motivo, obs_nova, id_cand))
    conn.commit()
    
    cursor.execute("SELECT * FROM candidatos WHERE id = ?", (id_cand,))
    cand_atualizado = dict(cursor.fetchone())
    conn.close()
    
    return {
        "success": True,
        "message": "Documento reenviado com sucesso! Sua candidatura retornou para análise prioritária.",
        "candidato": cand_atualizado
    }, 200

def process_consultar_status(termo):
    if not termo:
        return {"error": "Informe o CPF ou número de protocolo."}, 400
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, protocolo, nome, cpf, rg, data_nascimento, telefone, email, cidade, bairro,
               raio_atendimento, meio_transporte, ferramentas, tempo_experiencia,
               data_cadastro, status, motivo_status, quiz_nota,
               doc_frente, doc_selfie, certidao_antecedentes, possui_mei, cnpj_mei
        FROM candidatos
        WHERE cpf = ? OR protocolo = ?
        ORDER BY id DESC LIMIT 1
    ''', (termo, termo))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"found": False, "message": "Nenhum cadastro encontrado com esses dados."}, 404
        
    cand = dict(row)
    cand['ferramentas'] = json.loads(cand['ferramentas']) if cand['ferramentas'] else []
    return {"found": True, "candidato": cand}, 200

def process_reset_demo():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidatos")
    conn.commit()
    conn.close()
    seed_demo_data()
    return {"success": True, "message": "Dados de demonstração restaurados com sucesso!"}, 200

def open_browser_delayed(port):
    import time
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    print(f"\n[Terra Fertil] Abrindo interface no navegador: {url}")
    webbrowser.open_new(url)

# ====================================================
# DETECÇÃO DE ENGINE: FLASK vs SERVIDOR PYTHON NATIVO
# ====================================================
try:
    from flask import Flask, render_template, request, jsonify, send_from_directory
    USE_FLASK = True
except ImportError:
    USE_FLASK = False

if USE_FLASK:
    # MODO 1: EXECUÇÃO VIA FLASK
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, 'templates'),
        static_folder=os.path.join(BASE_DIR, 'static')
    )
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self';"
        )
        return response

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/stats', methods=['GET'])
    def api_stats():
        return jsonify(query_stats())

    @app.route('/api/candidatos', methods=['GET'])
    def api_list_candidatos():
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        return jsonify(query_candidatos(status, search))

    @app.route('/api/candidatos/<int:id>', methods=['GET'])
    def api_get_candidato(id):
        cand = query_candidato_by_id(id)
        if not cand:
            return jsonify({"error": "Candidato não encontrado"}), 404
        return jsonify(cand)

    @app.route('/api/candidatos', methods=['POST'])
    def api_create_candidato():
        res, code = process_create_candidato(request.json or {})
        return jsonify(res), code

    @app.route('/api/candidatos/<int:id>/status', methods=['PATCH'])
    def api_update_status(id):
        res, code = process_update_status(id, request.json or {})
        return jsonify(res), code

    @app.route('/api/candidatos/<int:id>/reenviar-docs', methods=['POST'])
    def api_reenviar_docs(id):
        res, code = process_reenviar_docs(id, request.json or {})
        return jsonify(res), code

    @app.route('/api/consultar-status', methods=['POST'])
    def api_consultar_status():
        data = request.json or {}
        res, code = process_consultar_status(data.get('termo', '').strip())
        return jsonify(res), code

    @app.route('/api/reset-demo', methods=['POST'])
    def api_reset_demo():
        res, code = process_reset_demo()
        return jsonify(res), code

    def run_server(port):
        app.run(host='127.0.0.1', port=port, debug=False)

else:
    # MODO 2: SERVIDOR NATIVO PYTHON (ZERO DEPENDÊNCIAS / 100% BIBLIOTECA PADRÃO)
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class NativeTerraFertilHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Log limpo
            pass

        def set_security_headers(self, content_type='application/json'):
            self.send_header('Content-Type', content_type)
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'SAMEORIGIN')
            self.send_header('X-XSS-Protection', '1; mode=block')
            self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
            self.send_header('Content-Security-Policy', (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "script-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self';"
            ))

        def send_json(self, data, code=200):
            payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.set_security_headers('application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def read_json_body(self):
            content_len = int(self.headers.get('Content-Length', 0))
            if content_len > 2 * 1024 * 1024:
                return None
            body = self.rfile.read(content_len).decode('utf-8')
            return json.loads(body) if body else {}

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path

            if path == '/' or path == '/index.html':
                html_path = os.path.join(BASE_DIR, 'templates', 'index.html')
                if os.path.exists(html_path):
                    with open(html_path, 'rb') as f:
                        content = f.read()
                    self.send_response(200)
                    self.set_security_headers('text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                else:
                    self.send_error(404, "Arquivo HTML não encontrado")
                    return

            if path.startswith('/static/'):
                rel_path = path.replace('/static/', '', 1)
                file_path = os.path.join(BASE_DIR, 'static', rel_path.replace('/', os.sep))
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    ext = os.path.splitext(file_path)[1].lower()
                    mime_map = {
                        '.css': 'text/css; charset=utf-8',
                        '.js': 'application/javascript; charset=utf-8',
                        '.png': 'image/png',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.svg': 'image/svg+xml'
                    }
                    mime = mime_map.get(ext, 'application/octet-stream')
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    self.send_response(200)
                    self.set_security_headers(mime)
                    self.send_header('Content-Length', str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                else:
                    self.send_error(404, "Arquivo estático não encontrado")
                    return

            if path == '/api/stats':
                self.send_json(query_stats())
                return

            if path == '/api/candidatos':
                qs = parse_qs(parsed.query)
                status = qs.get('status', [None])[0]
                search = qs.get('search', [''])[0]
                self.send_json(query_candidatos(status, search))
                return

            if path.startswith('/api/candidatos/'):
                cand_id = path.replace('/api/candidatos/', '')
                if cand_id.isdigit():
                    cand = query_candidato_by_id(int(cand_id))
                    if cand:
                        self.send_json(cand)
                    else:
                        self.send_json({"error": "Candidato não encontrado"}, 404)
                    return

            self.send_error(404, "Rota não encontrada")

        def do_POST(self):
            parsed = urlparse(self.path)
            path = parsed.path
            data = self.read_json_body()
            if data is None:
                self.send_json({"error": "Payload excede o limite máximo permitido"}, 413)
                return

            if path == '/api/candidatos':
                res, code = process_create_candidato(data)
                self.send_json(res, code)
                return

            if path.startswith('/api/candidatos/') and path.endswith('/reenviar-docs'):
                parts = path.split('/')
                if len(parts) >= 4 and parts[3].isdigit():
                    cand_id = int(parts[3])
                    res, code = process_reenviar_docs(cand_id, data)
                    self.send_json(res, code)
                    return

            if path == '/api/consultar-status':
                termo = data.get('termo', '').strip()
                res, code = process_consultar_status(termo)
                self.send_json(res, code)
                return

            if path == '/api/reset-demo':
                res, code = process_reset_demo()
                self.send_json(res, code)
                return

            self.send_error(404, "Rota POST não encontrada")

        def do_PATCH(self):
            parsed = urlparse(self.path)
            path = parsed.path
            data = self.read_json_body()
            if data is None:
                self.send_json({"error": "Payload excede o limite"}, 413)
                return

            if path.startswith('/api/candidatos/') and path.endswith('/status'):
                parts = path.split('/')
                if len(parts) >= 4 and parts[3].isdigit():
                    cand_id = int(parts[3])
                    res, code = process_update_status(cand_id, data)
                    self.send_json(res, code)
                    return

            self.send_error(404, "Rota PATCH não encontrada")

    def run_server(port):
        server = HTTPServer(('127.0.0.1', port), NativeTerraFertilHandler)
        server.serve_forever()

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    init_db()
    seed_demo_data()
    
    port = 5000
    
    threading.Thread(target=open_browser_delayed, args=(port,), daemon=True).start()
    
    engine_name = "Flask (Servidor WSGI)" if USE_FLASK else "Python Nativo (Sem Dependencias Externas)"
    print("\n" + "="*65)
    print(" TERRA FERTIL JARDINS - SISTEMA DE TRIAGEM DE PRESTADORES")
    print("="*65)
    print(f" Modo de Execucao: {engine_name}")
    print(f" Servidor local ativo em: http://127.0.0.1:{port}")
    print(" A interface esta sendo aberta automaticamente no seu navegador.")
    print(" Para encerrar a aplicacao, feche esta janela ou aperte Ctrl+C.")
    print("="*65 + "\n")
    
    run_server(port)
