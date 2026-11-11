import sqlite3
import os
import sys
import json
from datetime import datetime

def get_db_path():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'triagem.db')

DB_PATH = get_db_path()

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidatos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        protocolo TEXT UNIQUE NOT NULL,
        data_cadastro TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'EM_ANALISE', -- EM_ANALISE, APROVADO, REPROVADO, PENDENCIA_DOC
        motivo_status TEXT,
        
        -- Dados Pessoais
        nome TEXT NOT NULL,
        cpf TEXT NOT NULL,
        rg TEXT,
        data_nascimento TEXT,
        telefone TEXT NOT NULL,
        email TEXT NOT NULL,
        cidade TEXT NOT NULL,
        bairro TEXT NOT NULL,
        raio_atendimento INTEGER NOT NULL DEFAULT 20,
        
        -- Logística e Ferramental
        meio_transporte TEXT NOT NULL,
        ferramentas TEXT NOT NULL, -- JSON list
        recolhe_residuos INTEGER NOT NULL DEFAULT 0,
        
        -- Competência e Experiência
        tempo_experiencia TEXT NOT NULL,
        especialidades TEXT NOT NULL, -- JSON list
        quiz_nota INTEGER NOT NULL DEFAULT 0,
        quiz_respostas TEXT, -- JSON
        portfolio_fotos TEXT, -- JSON list
        
        -- Documentação e Conformidade
        doc_frente TEXT,
        doc_selfie TEXT,
        comprovante_residencia TEXT,
        certidao_antecedentes TEXT,
        possui_mei INTEGER NOT NULL DEFAULT 0,
        cnpj_mei TEXT,
        termos_aceitos INTEGER NOT NULL DEFAULT 1,
        
        -- Notas internas da equipe Terra Fértil
        observacoes_internas TEXT
    );
    ''')
    
    conn.commit()
    conn.close()

def seed_demo_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM candidatos")
    count = cursor.fetchone()[0]
    
    if count == 0:
        candidatos_exemplo = [
            {
                "protocolo": "TF-2026-1001",
                "data_cadastro": "2026-10-21 14:30:00",
                "status": "APROVADO",
                "motivo_status": "Documentação regular, ferramentas completas e ótimo desempenho no quiz.",
                "nome": "Sebastião Carlos de Oliveira",
                "cpf": "234.567.890-12",
                "rg": "18.452.901-X",
                "data_nascimento": "1982-05-14",
                "telefone": "(11) 98765-4321",
                "email": "sebastiao.jardins@email.com",
                "cidade": "São Paulo",
                "bairro": "Santo Amaro",
                "raio_atendimento": 30,
                "meio_transporte": "Utilitário próprio (Picape Fiorino)",
                "ferramentas": json.dumps(["Roçadeira a gasolina", "Podador de cerca viva", "Soprador de folhas", "Tesourão de poda", "Escada articulada", "Kit completo de EPIs"]),
                "recolhe_residuos": 1,
                "tempo_experiencia": "Mais de 5 anos",
                "especialidades": json.dumps(["Poda de árvores e arbustos", "Corte de grama ornamental", "Adubação e correção de solo", "Paisagismo e plantio"]),
                "quiz_nota": 100,
                "quiz_respostas": json.dumps({"q1": "correta", "q2": "correta", "q3": "correta"}),
                "portfolio_fotos": json.dumps(["jardim_residencial_antes_depois.jpg", "poda_cerca_viva.jpg"]),
                "doc_frente": "cnh_sebastiao.jpg",
                "doc_selfie": "selfie_sebastiao.jpg",
                "comprovante_residencia": "comprovante_luz.pdf",
                "certidao_antecedentes": "nada_consta_federal.pdf",
                "possui_mei": 1,
                "cnpj_mei": "45.123.789/0001-90",
                "termos_aceitos": 1,
                "observacoes_internas": "Profissional sênior, com 8 anos de praça e MEI ativo. Perfil de alta confiança para condomínios fechados."
            },
            {
                "protocolo": "TF-2026-1002",
                "data_cadastro": "2026-10-22 09:15:00",
                "status": "EM_ANALISE",
                "motivo_status": "Aguardando conferência de documento e validação de selfie.",
                "nome": "Marcos Vinícius Santos",
                "cpf": "345.678.901-23",
                "rg": "22.341.567-8",
                "data_nascimento": "1994-08-20",
                "telefone": "(11) 97654-3210",
                "email": "marcos.paisagismo@gmail.com",
                "cidade": "São Paulo",
                "bairro": "Pinheiros",
                "raio_atendimento": 20,
                "meio_transporte": "Carro de passeio com reboque",
                "ferramentas": json.dumps(["Roçadeira a gasolina", "Tesourão de poda", "Kit completo de EPIs"]),
                "recolhe_residuos": 1,
                "tempo_experiencia": "1 a 3 anos",
                "especialidades": json.dumps(["Corte de grama ornamental", "Manutenção periódica"]),
                "quiz_nota": 67,
                "quiz_respostas": json.dumps({"q1": "correta", "q2": "correta", "q3": "incorreta"}),
                "portfolio_fotos": json.dumps(["gramado_casa_pinheiros.jpg"]),
                "doc_frente": "rg_marcos_frente.jpg",
                "doc_selfie": "selfie_marcos.jpg",
                "comprovante_residencia": "conta_telefone.pdf",
                "certidao_antecedentes": "certidao_estadual.pdf",
                "possui_mei": 0,
                "cnpj_mei": "",
                "termos_aceitos": 1,
                "observacoes_internas": "Candidato demonstrou boa vontade. Errou a pergunta de adubação no quiz, mas possui ferramentas próprias funcionais."
            },
            {
                "protocolo": "TF-2026-1003",
                "data_cadastro": "2026-10-23 11:00:00",
                "status": "PENDENCIA_DOC",
                "motivo_status": "A foto do documento enviada está com reflexo e corte no número do RG.",
                "nome": "Jorge Luiz Medeiros",
                "cpf": "456.789.012-34",
                "rg": "31.982.114-2",
                "data_nascimento": "1988-12-05",
                "telefone": "(11) 96543-2109",
                "email": "jorge.medeiros@hotmail.com",
                "cidade": "São Paulo",
                "bairro": "Santana",
                "raio_atendimento": 15,
                "meio_transporte": "Moto com baú lateral",
                "ferramentas": json.dumps(["Podador de cerca viva", "Tesourão de poda", "EPIs básicos"]),
                "recolhe_residuos": 0,
                "tempo_experiencia": "3 a 5 anos",
                "especialidades": json.dumps(["Poda de árvores e arbustos", "Controle de pragas e adubação"]),
                "quiz_nota": 100,
                "quiz_respostas": json.dumps({"q1": "correta", "q2": "correta", "q3": "correta"}),
                "portfolio_fotos": json.dumps(["cerca_viva_antes_depois.jpg"]),
                "doc_frente": "doc_borrado.jpg",
                "doc_selfie": "selfie_jorge.jpg",
                "comprovante_residencia": "comprovante_agua.pdf",
                "certidao_antecedentes": "certidao_civil.pdf",
                "possui_mei": 1,
                "cnpj_mei": "38.991.002/0001-44",
                "termos_aceitos": 1,
                "observacoes_internas": "Excelente profissional e nota máxima no quiz. Solicitar apenas novo upload nítido do documento."
            },
            {
                "protocolo": "TF-2026-1004",
                "data_cadastro": "2026-10-23 16:20:00",
                "status": "REPROVADO",
                "motivo_status": "Não possui nenhuma ferramenta própria de corte e não atende o raio mínimo de cobertura.",
                "nome": "Ronaldo Farias Ribeiro",
                "cpf": "567.890.123-45",
                "rg": "40.551.983-1",
                "data_nascimento": "2003-03-10",
                "telefone": "(11) 95432-1098",
                "email": "ronaldo.farias@gmail.com",
                "cidade": "Campinas",
                "bairro": "Cambuí",
                "raio_atendimento": 5,
                "meio_transporte": "A pé / Transporte público",
                "ferramentas": json.dumps([]),
                "recolhe_residuos": 0,
                "tempo_experiencia": "Menos de 1 ano",
                "especialidades": json.dumps(["Regar plantas"]),
                "quiz_nota": 33,
                "quiz_respostas": json.dumps({"q1": "incorreta", "q2": "incorreta", "q3": "correta"}),
                "portfolio_fotos": json.dumps([]),
                "doc_frente": "cnh_ronaldo.jpg",
                "doc_selfie": "selfie_ronaldo.jpg",
                "comprovante_residencia": "comprovante_res.pdf",
                "certidao_antecedentes": "certidao.pdf",
                "possui_mei": 0,
                "cnpj_mei": "",
                "termos_aceitos": 1,
                "observacoes_internas": "Candidato sem maquinário e fora da praça de atendimento inicial da Grande SP. Não atende aos requisitos operacionais mínimos do modelo Uber."
            }
        ]
        
        for c in candidatos_exemplo:
            cursor.execute('''
            INSERT INTO candidatos (
                protocolo, data_cadastro, status, motivo_status,
                nome, cpf, rg, data_nascimento, telefone, email, cidade, bairro, raio_atendimento,
                meio_transporte, ferramentas, recolhe_residuos,
                tempo_experiencia, especialidades, quiz_nota, quiz_respostas, portfolio_fotos,
                doc_frente, doc_selfie, comprovante_residencia, certidao_antecedentes,
                possui_mei, cnpj_mei, termos_aceitos, observacoes_internas
            ) VALUES (
                :protocolo, :data_cadastro, :status, :motivo_status,
                :nome, :cpf, :rg, :data_nascimento, :telefone, :email, :cidade, :bairro, :raio_atendimento,
                :meio_transporte, :ferramentas, :recolhe_residuos,
                :tempo_experiencia, :especialidades, :quiz_nota, :quiz_respostas, :portfolio_fotos,
                :doc_frente, :doc_selfie, :comprovante_residencia, :certidao_antecedentes,
                :possui_mei, :cnpj_mei, :termos_aceitos, :observacoes_internas
            )
            ''', c)
        
        conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_demo_data()
    print("Banco de dados SQLite inicializado e alimentado com sucesso!")
