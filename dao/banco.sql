create database dipe;
use dipe;

SHOW TABLES;

select * from usuarios;
select * from alunos;
select * from provas;
select * from questoes;
select * from resultados;
select * from respostas;

drop table resultados;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    tipo ENUM('gestor', 'aluno') NOT NULL
);

-- Criando a tabela de alunos referenciando a tabela usuários
CREATE TABLE alunos (
    idAluno INT AUTO_INCREMENT PRIMARY KEY, -- ID único da tabela alunos
    idUser INT NOT NULL,                     -- Referência ao usuário (deve ser do tipo 'aluno')
    matricula VARCHAR(20),                    -- Número de matrícula (agora opcional)
    nome VARCHAR(100) NOT NULL,               -- Nome do aluno
    ano INT NOT NULL,                         -- Ano do curso
    curso ENUM('Redes de Computadores', 'Agropecuária', 'Partiu IF') NOT NULL, -- Cursos permitidos
    media DECIMAL(4,2),                       -- Média do aluno
    situacao ENUM('Insuficiente', 'Regular', 'Suficiente'), -- Definida pelo servidor
    CONSTRAINT fk_idUser FOREIGN KEY (idUser) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE provas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    materia VARCHAR(100) NOT NULL,  -- Pode ser "Português", "Matemática" ou "Ciências"
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE questoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prova_id INT NOT NULL,  -- Relacionado com a tabela provas
    enunciado TEXT NOT NULL,
    imagem VARCHAR(255),  -- Caminho da imagem (opcional)
    opcao_a VARCHAR(255) NOT NULL,
    opcao_b VARCHAR(255) NOT NULL,
    opcao_c VARCHAR(255) NOT NULL,
    opcao_d VARCHAR(255) NOT NULL,
    opcao_e VARCHAR(255) NOT NULL,
    resposta_correta CHAR(1) NOT NULL,  -- a, b, c, d ou e
    FOREIGN KEY (prova_id) REFERENCES provas(id)
);

CREATE TABLE respostas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,  -- Relacionado com a tabela aluno
    questao_id INT NOT NULL,  -- Relacionado com a tabela questoes
    resposta_aluno CHAR(1) NOT NULL,  -- Resposta escolhida pelo aluno (a, b, c, d ou e)
    FOREIGN KEY (aluno_id) REFERENCES alunos(idAluno),
    FOREIGN KEY (questao_id) REFERENCES questoes(id)
);

CREATE TABLE resultados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,  -- Relacionado com a tabela aluno
    prova_id INT NOT NULL,  -- Relacionado com a tabela provas
    acertos INT NOT NULL,  -- Número de acertos do aluno na prova
    situacao VARCHAR(50) NOT NULL,  -- Insuficiente, Regular, Suficiente
    FOREIGN KEY (aluno_id) REFERENCES alunos(idAluno),
    FOREIGN KEY (prova_id) REFERENCES provas(id)
);

ALTER TABLE provas DROP COLUMN nome;
ALTER TABLE alunos DROP COLUMN situacao;
ALTER TABLE alunos ADD COLUMN imagem VARCHAR(255);
ALTER TABLE alunos 
ADD COLUMN idade INT NOT NULL,
ADD COLUMN município VARCHAR(255) NOT NULL,
ADD COLUMN zona ENUM('urbana', 'rural') NOT NULL,
ADD COLUMN origem_escolar ENUM('particular', 'pública') NOT NULL;

ALTER TABLE alunos CHANGE `município` `municipio` VARCHAR(100);

DELETE FROM respostas
WHERE aluno_id = 1
AND questao_id IN (
    SELECT id FROM questoes WHERE prova_id = 4
);

DELETE FROM resultados
WHERE prova_id = 4
AND aluno_id = 1;
