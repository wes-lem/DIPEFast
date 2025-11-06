show databases;
CREATE DATABASE dipe;
USE dipe;
show tables;

-- Seleciona o banco de dados que você quer limpar (substitua 'seu_banco_de_dados')
USE dipe;
-- Desabilita a verificação de chaves estrangeiras para permitir apagar as tabelas
SET FOREIGN_KEY_CHECKS = 0;

-- Gera e executa os comandos DROP TABLE para cada tabela no banco de dados
SET GROUP_CONCAT_MAX_LEN=32768;
SET @tables = NULL;
SELECT GROUP_CONCAT('`', table_name, '`') INTO @tables
  FROM information_schema.tables
  WHERE table_schema = (SELECT DATABASE());
SELECT IFNULL(@tables,'dummy') INTO @tables;

SET @tables = CONCAT('DROP TABLE IF EXISTS ', @tables);
PREPARE stmt FROM @tables;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Reativa a verificação de chaves estrangeiras
SET FOREIGN_KEY_CHECKS = 1;

select * from provas;
select * from alunos;
select * from usuarios;
select * from questoes;
select * from respostas;
select * from resultados;
select * from gestores;

SELECT user, host, authentication_string FROM mysql.user WHERE user='root';

-- Tabela de usuários
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    tipo ENUM('gestor', 'aluno') NOT NULL
);

select * from usuarios;

-- Tabela de alunos
CREATE TABLE alunos (
    idAluno INT AUTO_INCREMENT PRIMARY KEY,
    idUser INT NOT NULL,
    matricula VARCHAR(20),
    nome VARCHAR(100) NOT NULL,
    ano INT NOT NULL,
    curso ENUM('Redes de Computadores', 'Agropecuária') NOT NULL,
    media DECIMAL(4,2),
    imagem VARCHAR(255),
    idade INT NOT NULL,
    municipio VARCHAR(100) NOT NULL,
    zona ENUM('urbana', 'rural') NOT NULL,
    origem_escolar ENUM('particular', 'pública') NOT NULL,
    CONSTRAINT fk_idUser FOREIGN KEY (idUser) REFERENCES usuarios(id) ON DELETE CASCADE
);

Select * from alunos;

-- Tabela de provas
CREATE TABLE provas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    materia VARCHAR(100) NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de questões
CREATE TABLE questoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prova_id INT NOT NULL,
    enunciado TEXT NOT NULL,
    imagem VARCHAR(255),
    opcao_a VARCHAR(255) NOT NULL,
    opcao_b VARCHAR(255) NOT NULL,
    opcao_c VARCHAR(255) NOT NULL,
    opcao_d VARCHAR(255) NOT NULL,
    opcao_e VARCHAR(255) NOT NULL,
    resposta_correta CHAR(1) NOT NULL,
    FOREIGN KEY (prova_id) REFERENCES provas(id)
);

-- Tabela de respostas dos alunos
CREATE TABLE respostas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    questao_id INT NOT NULL,
    resposta_aluno CHAR(1) NOT NULL,
    FOREIGN KEY (aluno_id) REFERENCES alunos(idAluno),
    FOREIGN KEY (questao_id) REFERENCES questoes(id)
);

-- Tabela de resultados das provas
CREATE TABLE resultados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    prova_id INT NOT NULL,
    acertos INT NOT NULL,
    situacao ENUM('Insuficiente', 'Regular', 'Suficiente') NOT NULL,
    FOREIGN KEY (aluno_id) REFERENCES alunos(idAluno),
    FOREIGN KEY (prova_id) REFERENCES provas(id)
);

CREATE TABLE gestores (
    id INT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    imagem VARCHAR(255),
    FOREIGN KEY (id) REFERENCES usuarios(id) ON DELETE CASCADE
);


SELECT USER(), CURRENT_USER();

ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';
FLUSH PRIVILEGES;

-- Desabilita verificação de chave estrangeira temporariamente
SET FOREIGN_KEY_CHECKS = 0;

-- Apaga os dados das tabelas que registram respostas e resultados
TRUNCATE TABLE respostas;
TRUNCATE TABLE resultados;

-- Reabilita verificação de chave estrangeira
SET FOREIGN_KEY_CHECKS = 1;


