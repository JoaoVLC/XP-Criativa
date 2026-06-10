CREATE DATABASE IF NOT EXISTS trampos
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE trampos;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS Notificacao;
DROP TABLE IF EXISTS Candidatura;
DROP TABLE IF EXISTS Vaga;
DROP TABLE IF EXISTS Categoria;
DROP TABLE IF EXISTS Usuario;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE Usuario (
    id_usuario INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    tipo ENUM('empresa', 'freelancer', 'admin') NOT NULL,
    documento_tipo ENUM('cpf', 'cnpj', 'admin') NOT NULL,
    cpf VARCHAR(20) NULL,
    cnpj VARCHAR(20) NULL,
    razao_social VARCHAR(140) NULL,
    avatar LONGBLOB NULL,
    avatar_mime VARCHAR(50) NULL,
    curriculo LONGBLOB NULL,
    curriculo_nome VARCHAR(180) NULL,
    curriculo_mime VARCHAR(80) NULL,
    curriculo_enviado_em DATETIME NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uq_usuario_email (email),
    UNIQUE KEY uq_usuario_cpf (cpf),
    UNIQUE KEY uq_usuario_cnpj (cnpj)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Categoria (
    id_categoria INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    PRIMARY KEY (id_categoria),
    UNIQUE KEY uq_categoria_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Vaga (
    id_vaga INT NOT NULL AUTO_INCREMENT,
    titulo VARCHAR(100) NOT NULL,
    descricao TEXT NOT NULL,
    data DATE NOT NULL,
    local VARCHAR(150) NOT NULL,
    pagamento DECIMAL(10, 2) NOT NULL,
    status ENUM('aberta', 'pausada', 'encerrada') NOT NULL DEFAULT 'aberta',
    id_empresa INT NOT NULL,
    id_categoria INT NULL,
    criada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_vaga),
    KEY idx_vaga_status (status),
    KEY idx_vaga_data (data),
    CONSTRAINT fk_vaga_empresa
        FOREIGN KEY (id_empresa) REFERENCES Usuario(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_vaga_categoria
        FOREIGN KEY (id_categoria) REFERENCES Categoria(id_categoria) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Candidatura (
    id_candidatura INT NOT NULL AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    id_vaga INT NOT NULL,
    status ENUM('pendente', 'aceito', 'recusado') NOT NULL DEFAULT 'pendente',
    criada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id_candidatura),
    UNIQUE KEY uq_candidatura_usuario_vaga (id_usuario, id_vaga),
    KEY idx_candidatura_status (status),
    CONSTRAINT fk_cand_usuario
        FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_cand_vaga
        FOREIGN KEY (id_vaga) REFERENCES Vaga(id_vaga) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Notificacao (
    id_notificacao INT NOT NULL AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    titulo VARCHAR(120) NOT NULL,
    mensagem VARCHAR(255) NOT NULL,
    tipo ENUM('info', 'success', 'error') NOT NULL DEFAULT 'info',
    lida TINYINT(1) NOT NULL DEFAULT 0,
    criada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_notificacao),
    KEY idx_notificacao_usuario (id_usuario, lida),
    CONSTRAINT fk_notificacao_usuario
        FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO Categoria (nome) VALUES
('Limpeza e Conservação'),
('Eventos e Hospitalidade'),
('Construção e Reformas'),
('Tecnologia e TI'),
('Educação e Tutoria'),
('Entregas e Logística'),
('Design e Criação');

-- Senha de todos os usuários de exemplo: senha123
SET @hash_senha := '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm';
SET @pdf_demo := CAST('%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF' AS BINARY);

INSERT INTO Usuario (nome, email, senha, tipo, documento_tipo, cnpj, razao_social) VALUES
('Administrador Trampos', 'admin@trampos.dev', @hash_senha, 'admin', 'admin', NULL, NULL),
('Tech Rapido Ltda.', 'tech@trampos.dev', @hash_senha, 'empresa', 'cnpj', '00000000000001', 'Tech Rapido Ltda.'),
('Eventos Brilho S.A.', 'brilho@trampos.dev', @hash_senha, 'empresa', 'cnpj', '00000000000002', 'Eventos Brilho S.A.'),
('Construtech Reformas', 'construtech@trampos.dev', @hash_senha, 'empresa', 'cnpj', '00000000000003', 'Construtech Reformas'),
('Click Entregas', 'click@trampos.dev', @hash_senha, 'empresa', 'cnpj', '00000000000004', 'Click Entregas'),
('EduFácil Cursos', 'edufacil@trampos.dev', @hash_senha, 'empresa', 'cnpj', '00000000000005', 'EduFácil Cursos');

INSERT INTO Usuario (nome, email, senha, tipo, documento_tipo, cpf, curriculo, curriculo_nome, curriculo_mime, curriculo_enviado_em) VALUES
('Ana Souza', 'ana@trampos.dev', @hash_senha, 'freelancer', 'cpf', '00000000001', @pdf_demo, 'ana-souza.pdf', 'application/pdf', NOW()),
('Bruno Lima', 'bruno@trampos.dev', @hash_senha, 'freelancer', 'cpf', '00000000002', @pdf_demo, 'bruno-lima.pdf', 'application/pdf', NOW()),
('Carla Mendes', 'carla@trampos.dev', @hash_senha, 'freelancer', 'cpf', '00000000003', @pdf_demo, 'carla-mendes.pdf', 'application/pdf', NOW()),
('Diego Faria', 'diego@trampos.dev', @hash_senha, 'freelancer', 'cpf', '00000000004', @pdf_demo, 'diego-faria.pdf', 'application/pdf', NOW()),
('Elisa Rocha', 'elisa@trampos.dev', @hash_senha, 'freelancer', 'cpf', '00000000005', @pdf_demo, 'elisa-rocha.pdf', 'application/pdf', NOW()),
('Felipe Nunes', 'felipe@trampos.dev', @hash_senha, 'freelancer', 'cpf', '00000000006', @pdf_demo, 'felipe-nunes.pdf', 'application/pdf', NOW());

INSERT INTO Vaga (titulo, descricao, data, local, pagamento, status, id_empresa, id_categoria) VALUES
('Desenvolvedor Python Freelancer', 'Criação de scripts de automação e integração de APIs REST. Experiência com FastAPI será considerada diferencial.', DATE_ADD(CURDATE(), INTERVAL 5 DAY), 'Remoto', 850.00, 'aberta', 2, 4),
('Suporte TI para evento corporativo', 'Suporte presencial durante evento de 2 dias. Configuração de redes, projetores e notebooks.', DATE_ADD(CURDATE(), INTERVAL 10 DAY), 'São Paulo - SP', 600.00, 'aberta', 2, 4),
('Garçom para casamento', 'Atendimento em cerimônia de casamento com 150 convidados. Traje social obrigatório e experiência mínima de 1 ano.', DATE_ADD(CURDATE(), INTERVAL 7 DAY), 'Campinas - SP', 350.00, 'aberta', 3, 2),
('Recepcionista para conferência', 'Recepção durante conferência de negócios de 3 dias. Boa comunicação, postura profissional e inglês desejável.', DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'Rio de Janeiro - RJ', 480.00, 'pausada', 3, 2),
('Pintor de apartamento', 'Pintura completa de apartamento de 3 quartos. Material fornecido pelo contratante e prazo de 4 dias.', DATE_ADD(CURDATE(), INTERVAL 3 DAY), 'Belo Horizonte - MG', 1200.00, 'aberta', 4, 3),
('Entregador moto para fim de semana', 'Rota de entregas expressas no fim de semana. Moto própria e CNH obrigatórias.', DATE_ADD(CURDATE(), INTERVAL 4 DAY), 'Porto Alegre - RS', 420.00, 'aberta', 5, 6),
('Tutor de matemática para ensino médio', 'Aulas particulares para alunos com dificuldades em álgebra e geometria, duas vezes por semana.', DATE_ADD(CURDATE(), INTERVAL 6 DAY), 'Florianópolis - SC', 280.00, 'aberta', 6, 5),
('Designer para identidade visual', 'Criação de logo, paleta de cores e manual de marca para startup. Portfólio necessário.', DATE_ADD(CURDATE(), INTERVAL 8 DAY), 'Remoto', 1500.00, 'aberta', 2, 7);

INSERT INTO Candidatura (id_usuario, id_vaga, status) VALUES
(7, 1, 'pendente'),
(10, 1, 'aceito'),
(12, 1, 'pendente'),
(8, 3, 'pendente'),
(9, 3, 'recusado'),
(8, 6, 'aceito'),
(11, 6, 'pendente'),
(9, 7, 'pendente'),
(7, 7, 'aceito'),
(12, 8, 'pendente'),
(11, 8, 'recusado');

INSERT INTO Notificacao (id_usuario, titulo, mensagem, tipo, lida) VALUES
(7, 'Bem-vindo ao Trampos', 'Seu perfil de exemplo já possui currículo em PDF.', 'info', 0),
(2, 'Candidatos disponiveis', 'A vaga Desenvolvedor Python Freelancer possui candidatos para avaliacao.', 'info', 0),
(1, 'Ambiente preparado', 'Use o painel administrador para gerenciar o sistema.', 'success', 0);

SELECT 'Usuario' AS tabela, COUNT(*) AS registros FROM Usuario UNION ALL
SELECT 'Categoria' AS tabela, COUNT(*) AS registros FROM Categoria UNION ALL
SELECT 'Vaga' AS tabela, COUNT(*) AS registros FROM Vaga UNION ALL
SELECT 'Candidatura' AS tabela, COUNT(*) AS registros FROM Candidatura UNION ALL
SELECT 'Notificacao' AS tabela, COUNT(*) AS registros FROM Notificacao;
