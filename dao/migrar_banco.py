import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from dao.database import engine, SessionLocal

def migrar_banco():
    """Migra o banco de dados para incluir as novas colunas e tabelas"""
    db = SessionLocal()
    try:
        print(" Iniciando migrao do banco de dados...")
        
        # Verificar se a coluna professor_id j existe na tabela provas
        result = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'provas' AND COLUMN_NAME = 'professor_id'
        """))
        
        if not result.fetchone():
            print(" Adicionando coluna professor_id na tabela provas...")
            db.execute(text("ALTER TABLE provas ADD COLUMN professor_id INT"))
            db.execute(text("ALTER TABLE provas ADD COLUMN titulo VARCHAR(255)"))
            db.execute(text("ALTER TABLE provas ADD COLUMN status VARCHAR(50) DEFAULT 'rascunho'"))
            db.execute(text("ALTER TABLE provas ADD COLUMN data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
            
            # Adicionar foreign key constraint
            db.execute(text("ALTER TABLE provas ADD CONSTRAINT fk_provas_professor FOREIGN KEY (professor_id) REFERENCES professores(id)"))
            print(" Colunas adicionadas na tabela provas")
        else:
            print(" Coluna professor_id j existe na tabela provas")
        
        # Verificar se a tabela campus existe
        result = db.execute(text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'campus'
        """))
        
        if not result.fetchone():
            print(" Criando tabela campus...")
            db.execute(text("""
                CREATE TABLE campus (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    endereco VARCHAR(500),
                    ativo BOOLEAN DEFAULT TRUE
                )
            """))
            print(" Tabela campus criada")
        else:
            print(" Tabela campus j existe")
        
        # Verificar se a tabela professores existe
        result = db.execute(text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'professores'
        """))
        
        if not result.fetchone():
            print(" Criando tabela professores...")
            db.execute(text("""
                CREATE TABLE professores (
                    id INT PRIMARY KEY,
                    nome VARCHAR(100) NOT NULL,
                    imagem VARCHAR(255),
                    especialidade VARCHAR(100),
                    campus_id INT NOT NULL,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id) REFERENCES usuarios(id),
                    FOREIGN KEY (campus_id) REFERENCES campus(id)
                )
            """))
            print(" Tabela professores criada")
        else:
            print(" Tabela professores j existe")
        
        # Verificar se a tabela turmas existe
        result = db.execute(text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'turmas'
        """))
        
        if not result.fetchone():
            print(" Criando tabela turmas...")
            db.execute(text("""
                CREATE TABLE turmas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    codigo VARCHAR(6) UNIQUE NOT NULL,
                    professor_id INT NOT NULL,
                    campus_id INT NOT NULL,
                    status ENUM('ativa', 'arquivada', 'excluida') DEFAULT 'ativa',
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_arquivacao TIMESTAMP NULL,
                    FOREIGN KEY (professor_id) REFERENCES professores(id),
                    FOREIGN KEY (campus_id) REFERENCES campus(id)
                )
            """))
            print(" Tabela turmas criada")
        else:
            print(" Tabela turmas j existe")
        
        # Verificar se a tabela aluno_turmas existe
        result = db.execute(text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'aluno_turmas'
        """))
        
        if not result.fetchone():
            print(" Criando tabela aluno_turmas...")
            db.execute(text("""
                CREATE TABLE aluno_turmas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    aluno_id INT NOT NULL,
                    turma_id INT NOT NULL,
                    data_entrada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('ativo', 'removido') DEFAULT 'ativo',
                    FOREIGN KEY (aluno_id) REFERENCES alunos(idAluno),
                    FOREIGN KEY (turma_id) REFERENCES turmas(id)
                )
            """))
            print(" Tabela aluno_turmas criada")
        else:
            print(" Tabela aluno_turmas j existe")
        
        # Verificar se a tabela banco_questoes existe
        result = db.execute(text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'banco_questoes'
        """))
        
        if not result.fetchone():
            print(" Criando tabela banco_questoes...")
            db.execute(text("""
                CREATE TABLE banco_questoes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    professor_id INT NOT NULL,
                    enunciado TEXT NOT NULL,
                    imagem VARCHAR(255),
                    opcao_a VARCHAR(500) NOT NULL,
                    opcao_b VARCHAR(500) NOT NULL,
                    opcao_c VARCHAR(500) NOT NULL,
                    opcao_d VARCHAR(500) NOT NULL,
                    opcao_e VARCHAR(500) NOT NULL,
                    resposta_correta VARCHAR(1) NOT NULL,
                    materia VARCHAR(100) NOT NULL,
                    status ENUM('ativa', 'arquivada') DEFAULT 'ativa',
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (professor_id) REFERENCES professores(id)
                )
            """))
            print(" Tabela banco_questoes criada")
        else:
            print(" Tabela banco_questoes j existe")
        
        # Verificar se a tabela prova_questoes existe
        result = db.execute(text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'prova_questoes'
        """))
        
        if not result.fetchone():
            print(" Criando tabela prova_questoes...")
            db.execute(text("""
                CREATE TABLE prova_questoes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    prova_id INT NOT NULL,
                    questao_id INT NOT NULL,
                    ordem INT NOT NULL,
                    FOREIGN KEY (prova_id) REFERENCES provas(id),
                    FOREIGN KEY (questao_id) REFERENCES banco_questoes(id)
                )
            """))
            print(" Tabela prova_questoes criada")
        else:
            print(" Tabela prova_questoes j existe")
        
        # Verificar se a tabela prova_turmas existe
        result = db.execute(text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'prova_turmas'
        """))
        
        if not result.fetchone():
            print(" Criando tabela prova_turmas...")
            db.execute(text("""
                CREATE TABLE prova_turmas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    prova_id INT NOT NULL,
                    turma_id INT NOT NULL,
                    professor_id INT NOT NULL,
                    data_inicio TIMESTAMP NOT NULL,
                    data_expiracao TIMESTAMP NOT NULL,
                    status ENUM('ativa', 'expirada', 'arquivada') DEFAULT 'ativa',
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prova_id) REFERENCES provas(id),
                    FOREIGN KEY (turma_id) REFERENCES turmas(id),
                    FOREIGN KEY (professor_id) REFERENCES professores(id)
                )
            """))
            print(" Tabela prova_turmas criada")
        else:
            print(" Tabela prova_turmas j existe")
        
        # Verificar se a tabela notificacoes_professor existe
        result = db.execute(text("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'notificacoes_professor'
        """))
        
        if not result.fetchone():
            print(" Criando tabela notificacoes_professor...")
            db.execute(text("""
                CREATE TABLE notificacoes_professor (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    professor_id INT NOT NULL,
                    tipo ENUM('prova_expirada', 'aluno_respondeu', 'turma_criada', 'prova_criada') NOT NULL,
                    titulo VARCHAR(255) NOT NULL,
                    mensagem VARCHAR(500) NOT NULL,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    lida BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (professor_id) REFERENCES professores(id)
                )
            """))
            print(" Tabela notificacoes_professor criada")
        else:
            print(" Tabela notificacoes_professor j existe")
        
        db.commit()
        print(" Migrao do banco de dados concluda com sucesso!")
        
    except Exception as e:
        print(f" Erro durante a migrao: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrar_banco()
