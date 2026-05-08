-- ===========================================================
--
--  Todos os usuários fake têm senha: senha123
-- ============================================================

-- ── Banco de dados ───────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS trampos
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE trampos;

-- ── Tabelas (DROP seguro para permitir re-execução) ──────────
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS Candidatura;
DROP TABLE IF EXISTS Vaga;
DROP TABLE IF EXISTS Categoria;
DROP TABLE IF EXISTS Usuario;

SET FOREIGN_KEY_CHECKS = 1;

-- ── Usuario ──────────────────────────────────────────────────
CREATE TABLE Usuario (
    id_usuario  INT          NOT NULL AUTO_INCREMENT,
    nome        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL,
    senha       VARCHAR(255) NOT NULL,
    tipo        ENUM('empresa', 'freelancer') NOT NULL,
    avatar_url  VARCHAR(255) NULL,
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uq_usuario_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Categoria ────────────────────────────────────────────────
CREATE TABLE Categoria (
    id_categoria INT          NOT NULL AUTO_INCREMENT,
    nome         VARCHAR(100) NOT NULL,
    PRIMARY KEY (id_categoria)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Vaga ─────────────────────────────────────────────────────
CREATE TABLE Vaga (
    id_vaga      INT            NOT NULL AUTO_INCREMENT,
    titulo       VARCHAR(100)   NOT NULL,
    descricao    TEXT           NOT NULL,
    data         DATE           NOT NULL,
    local        VARCHAR(150)   NOT NULL,
    pagamento    DECIMAL(10, 2) NOT NULL,
    id_empresa   INT            NOT NULL,
    id_categoria INT            NULL,
    PRIMARY KEY (id_vaga),
    CONSTRAINT fk_vaga_empresa
        FOREIGN KEY (id_empresa)   REFERENCES Usuario(id_usuario)  ON DELETE CASCADE,
    CONSTRAINT fk_vaga_categoria
        FOREIGN KEY (id_categoria) REFERENCES Categoria(id_categoria) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Candidatura ──────────────────────────────────────────────
CREATE TABLE Candidatura (
    id_candidatura INT  NOT NULL AUTO_INCREMENT,
    id_usuario     INT  NOT NULL,
    id_vaga        INT  NOT NULL,
    status         ENUM('pendente', 'aceito', 'recusado') NOT NULL DEFAULT 'pendente',
    PRIMARY KEY (id_candidatura),
    CONSTRAINT fk_cand_usuario
        FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)  ON DELETE CASCADE,
    CONSTRAINT fk_cand_vaga
        FOREIGN KEY (id_vaga)    REFERENCES Vaga(id_vaga)        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
--  DADOS FAKE
--  Senha de todos os usuários: senha123
--  Hash bcrypt gerado com cost factor 12.
-- ============================================================

-- ── Usuarios ─────────────────────────────────────────────────
INSERT INTO Usuario (nome, email, senha, tipo) VALUES
-- empresas
('TechRápido Ltda.',    'tech@trampos.dev',        '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'empresa'),
('Eventos Brilho S.A.','brilho@trampos.dev',       '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'empresa'),
('Construtech Reformas','construtech@trampos.dev', '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'empresa'),
('Click Entregas',      'click@trampos.dev',       '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'empresa'),
('EduFácil Cursos',     'edufacil@trampos.dev',    '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'empresa'),
-- freelancers
('Ana Souza',   'ana@trampos.dev',    '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'freelancer'),
('Bruno Lima',  'bruno@trampos.dev',  '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'freelancer'),
('Carla Mendes','carla@trampos.dev',  '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'freelancer'),
('Diego Faria', 'diego@trampos.dev',  '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'freelancer'),
('Elisa Rocha', 'elisa@trampos.dev',  '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'freelancer'),
('Felipe Nunes','felipe@trampos.dev', '$2b$12$mHKOQ9t5TE80ra7dyK9cKeKQG2kCsyPde6kAmP2G7WUr20XhJwdEm', 'freelancer');

-- ── Categorias ───────────────────────────────────────────────
INSERT INTO Categoria (nome) VALUES
('Limpeza e Conservação'),
('Eventos e Hospitalidade'),
('Construção e Reformas'),
('Tecnologia e TI'),
('Educação e Tutoria'),
('Entregas e Logística'),
('Design e Criação');

-- ── Vagas ────────────────────────────────────────────────────
-- Datas relativas a CURDATE() para ficarem sempre no futuro
INSERT INTO Vaga (titulo, descricao, data, local, pagamento, id_empresa, id_categoria) VALUES
(
  'Desenvolvedor Python Freelancer',
  'Precisamos de um desenvolvedor Python para criar scripts de automação e integração de APIs REST. Experiência com FastAPI é um diferencial.',
  DATE_ADD(CURDATE(), INTERVAL 5  DAY), 'Remoto',               850.00, 1, 4
),
(
  'Suporte TI para evento corporativo',
  'Necessitamos de técnico de TI para suporte presencial durante evento de 2 dias em São Paulo. Configuração de redes, projetores e notebooks.',
  DATE_ADD(CURDATE(), INTERVAL 10 DAY), 'São Paulo – SP',        600.00, 1, 4
),
(
  'Garçom para casamento',
  'Buscamos garçom experiente para atendimento em cerimônia de casamento com 150 convidados. Traje social obrigatório. Experiência mínima de 1 ano.',
  DATE_ADD(CURDATE(), INTERVAL 7  DAY), 'Campinas – SP',         350.00, 2, 2
),
(
  'Recepcionista para conferência',
  'Vaga para recepcionista durante conferência de negócios de 3 dias. Fluência em inglês é obrigatória. Boa comunicação e apresentação.',
  DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'Rio de Janeiro – RJ',   480.00, 2, 2
),
(
  'Pintor de apartamento',
  'Pintura completa de apartamento 3 quartos, área total de 85m². Material fornecido pelo contratante. Prazo de entrega: 4 dias corridos.',
  DATE_ADD(CURDATE(), INTERVAL 3  DAY), 'Belo Horizonte – MG',  1200.00, 3, 3
),
(
  'Pedreiro para reforma de banheiro',
  'Reforma completa de banheiro: remoção de azulejos, assentamento de novos revestimentos, troca de louças e metais. Experiência comprovada.',
  DATE_ADD(CURDATE(), INTERVAL 2  DAY), 'Curitiba – PR',          900.00, 3, 3
),
(
  'Entregador moto para fim de semana',
  'Entregador com moto própria para cobrir rota de entregas expressas durante o final de semana. Região central de Porto Alegre. CNH obrigatória.',
  DATE_ADD(CURDATE(), INTERVAL 4  DAY), 'Porto Alegre – RS',      420.00, 4, 6
),
(
  'Auxiliar de logística para Black Friday',
  'Auxiliar para separação, embalagem e organização de pedidos em galpão logístico durante período de Black Friday. Turno integral.',
  DATE_ADD(CURDATE(), INTERVAL 20 DAY), 'Barueri – SP',           320.00, 4, 6
),
(
  'Tutor de matemática para ensino médio',
  'Tutor para aulas particulares de matemática para alunos do ensino médio com dificuldades em álgebra e geometria. 2 vezes por semana.',
  DATE_ADD(CURDATE(), INTERVAL 6  DAY), 'Florianópolis – SC',     280.00, 5, 5
),
(
  'Designer para criação de identidade visual',
  'Designer freelancer para criação de logo, paleta de cores e manual de marca para startup. Entrega em até 7 dias. Portfólio necessário.',
  DATE_ADD(CURDATE(), INTERVAL 8  DAY), 'Remoto',                1500.00, 1, 7
),
(
  'Faxineira para escritório',
  'Serviço de limpeza completa em escritório comercial de 200m². Produtos de limpeza fornecidos. Trabalho para dois sábados consecutivos.',
  DATE_ADD(CURDATE(), INTERVAL 9  DAY), 'São Paulo – SP',          260.00, 2, 1
),
(
  'Barman para festa corporativa',
  'Barman com experiência em drinques clássicos e contemporâneos para evento corporativo com 80 pessoas. Uniforme e materiais fornecidos.',
  DATE_ADD(CURDATE(), INTERVAL 12 DAY), 'Brasília – DF',           500.00, 2, 2
);

-- ── Candidaturas ─────────────────────────────────────────────
-- id_usuario: 6=Ana, 7=Bruno, 8=Carla, 9=Diego, 10=Elisa, 11=Felipe
-- id_vaga:    1=Dev Python, 3=Garçom, 7=Entregador, 9=Tutor, 10=Designer
INSERT INTO Candidatura (id_usuario, id_vaga, status) VALUES
(6,  1, 'pendente'),   -- Ana      → Dev Python
(9,  1, 'aceito'),     -- Diego    → Dev Python
(11, 1, 'pendente'),   -- Felipe   → Dev Python
(7,  3, 'pendente'),   -- Bruno    → Garçom
(8,  3, 'recusado'),   -- Carla    → Garçom
(7,  7, 'aceito'),     -- Bruno    → Entregador
(10, 7, 'pendente'),   -- Elisa    → Entregador
(8,  9, 'pendente'),   -- Carla    → Tutor
(6,  9, 'aceito'),     -- Ana      → Tutor
(11, 10, 'pendente'),  -- Felipe   → Designer
(10, 10, 'recusado');  -- Elisa    → Designer

-- ── Verificação ──────────────────────────────────────────────
SELECT 'Usuario'    AS tabela, COUNT(*) AS registros FROM Usuario    UNION ALL
SELECT 'Categoria'  AS tabela, COUNT(*) AS registros FROM Categoria  UNION ALL
SELECT 'Vaga'       AS tabela, COUNT(*) AS registros FROM Vaga       UNION ALL
SELECT 'Candidatura'AS tabela, COUNT(*) AS registros FROM Candidatura;
