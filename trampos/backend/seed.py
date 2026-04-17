"""
seed.py — popula o banco trampos com dados fake para testes de frontend.
Execução: python seed.py  (dentro do venv, na pasta backend/)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, timedelta
import bcrypt
from app.database import SessionLocal, engine
from app import models

models.Base.metadata.create_all(bind=engine)

def hash_senha(s: str) -> str:
    return bcrypt.hashpw(s.encode(), bcrypt.gensalt()).decode()

db  = SessionLocal()

# ── 1. Limpar dados antigos (ordem: FK dependentes primeiro) ──────────────────
db.query(models.Candidatura).delete()
db.query(models.Vaga).delete()
db.query(models.Categoria).delete()
db.query(models.Usuario).delete()
db.commit()

# ── 2. Categorias ─────────────────────────────────────────────────────────────
categorias_nomes = [
    "Limpeza e Conservação",
    "Eventos e Hospitalidade",
    "Construção e Reformas",
    "Tecnologia e TI",
    "Educação e Tutoria",
    "Entregas e Logística",
    "Design e Criação",
]
cats = [models.Categoria(nome=n) for n in categorias_nomes]
db.add_all(cats)
db.flush()   # gera IDs sem commit

cat = {c.nome: c for c in cats}

# ── 3. Usuários ───────────────────────────────────────────────────────────────
SENHA = hash_senha("senha123")

empresas_raw = [
    ("TechRápido Ltda.",      "tech@trampos.dev"),
    ("Eventos Brilho S.A.",   "brilho@trampos.dev"),
    ("Construtech Reformas",  "construtech@trampos.dev"),
    ("Click Entregas",        "click@trampos.dev"),
    ("EduFácil Cursos",       "edufacil@trampos.dev"),
]
freelancers_raw = [
    ("Ana Souza",       "ana@trampos.dev"),
    ("Bruno Lima",      "bruno@trampos.dev"),
    ("Carla Mendes",    "carla@trampos.dev"),
    ("Diego Faria",     "diego@trampos.dev"),
    ("Elisa Rocha",     "elisa@trampos.dev"),
    ("Felipe Nunes",    "felipe@trampos.dev"),
]

empresas = [
    models.Usuario(nome=n, email=e, senha=SENHA, tipo="empresa")
    for n, e in empresas_raw
]
freelancers = [
    models.Usuario(nome=n, email=e, senha=SENHA, tipo="freelancer")
    for n, e in freelancers_raw
]
db.add_all(empresas + freelancers)
db.flush()

emp = {u.nome: u for u in empresas}
free = {u.nome: u for u in freelancers}

# ── 4. Vagas ──────────────────────────────────────────────────────────────────
hoje = date.today()

vagas_raw = [
    dict(
        titulo="Desenvolvedor Python Freelancer",
        descricao="Precisamos de um desenvolvedor Python para criar scripts de automação e integração de APIs REST. Experiência com FastAPI é um diferencial.",
        data=hoje + timedelta(days=5),
        local="Remoto",
        pagamento=850.00,
        id_empresa=emp["TechRápido Ltda."].id_usuario,
        id_categoria=cat["Tecnologia e TI"].id_categoria,
    ),
    dict(
        titulo="Suporte TI para evento corporativo",
        descricao="Necessitamos de técnico de TI para suporte presencial durante evento de 2 dias em São Paulo. Configuração de redes, projetores e notebooks.",
        data=hoje + timedelta(days=10),
        local="São Paulo – SP",
        pagamento=600.00,
        id_empresa=emp["TechRápido Ltda."].id_usuario,
        id_categoria=cat["Tecnologia e TI"].id_categoria,
    ),
    dict(
        titulo="Garçom para casamento",
        descricao="Buscamos garçom experiente para atendimento em cerimônia de casamento com 150 convidados. Traje social obrigatório. Experiência mínima de 1 ano.",
        data=hoje + timedelta(days=7),
        local="Campinas – SP",
        pagamento=350.00,
        id_empresa=emp["Eventos Brilho S.A."].id_usuario,
        id_categoria=cat["Eventos e Hospitalidade"].id_categoria,
    ),
    dict(
        titulo="Recepcionista para conferência",
        descricao="Vaga para recepcionista durante conferência de negócios de 3 dias. Fluência em inglês é obrigatória. Boa comunicação e apresentação.",
        data=hoje + timedelta(days=14),
        local="Rio de Janeiro – RJ",
        pagamento=480.00,
        id_empresa=emp["Eventos Brilho S.A."].id_usuario,
        id_categoria=cat["Eventos e Hospitalidade"].id_categoria,
    ),
    dict(
        titulo="Pintor de apartamento",
        descricao="Pintura completa de apartamento 3 quartos, área total de 85m². Material fornecido pelo contratante. Prazo de entrega: 4 dias corridos.",
        data=hoje + timedelta(days=3),
        local="Belo Horizonte – MG",
        pagamento=1200.00,
        id_empresa=emp["Construtech Reformas"].id_usuario,
        id_categoria=cat["Construção e Reformas"].id_categoria,
    ),
    dict(
        titulo="Pedreiro para reforma de banheiro",
        descricao="Reforma completa de banheiro: remoção de azulejos, assentamento de novos revestimentos, troca de louças e metais. Experiência comprovada.",
        data=hoje + timedelta(days=2),
        local="Curitiba – PR",
        pagamento=900.00,
        id_empresa=emp["Construtech Reformas"].id_usuario,
        id_categoria=cat["Construção e Reformas"].id_categoria,
    ),
    dict(
        titulo="Entregador moto para fim de semana",
        descricao="Entregador com moto própria para cobrir rota de entregas expressas durante o final de semana. Região central de Porto Alegre. CNH obrigatória.",
        data=hoje + timedelta(days=4),
        local="Porto Alegre – RS",
        pagamento=420.00,
        id_empresa=emp["Click Entregas"].id_usuario,
        id_categoria=cat["Entregas e Logística"].id_categoria,
    ),
    dict(
        titulo="Auxiliar de logística para Black Friday",
        descricao="Auxiliar para separação, embalagem e organização de pedidos em galpão logístico durante período de Black Friday. Turno integral.",
        data=hoje + timedelta(days=20),
        local="Barueri – SP",
        pagamento=320.00,
        id_empresa=emp["Click Entregas"].id_usuario,
        id_categoria=cat["Entregas e Logística"].id_categoria,
    ),
    dict(
        titulo="Tutor de matemática para ensino médio",
        descricao="Tutor para aulas particulares de matemática para alunos do ensino médio com dificuldades em álgebra e geometria. 2 vezes por semana.",
        data=hoje + timedelta(days=6),
        local="Florianópolis – SC",
        pagamento=280.00,
        id_empresa=emp["EduFácil Cursos"].id_usuario,
        id_categoria=cat["Educação e Tutoria"].id_categoria,
    ),
    dict(
        titulo="Designer para criação de identidade visual",
        descricao="Designer freelancer para criação de logo, paleta de cores e manual de marca para startup. Entrega em até 7 dias. Portfólio necessário.",
        data=hoje + timedelta(days=8),
        local="Remoto",
        pagamento=1500.00,
        id_empresa=emp["TechRápido Ltda."].id_usuario,
        id_categoria=cat["Design e Criação"].id_categoria,
    ),
    dict(
        titulo="Faxineira para escritório",
        descricao="Serviço de limpeza completa em escritório comercial de 200m². Produtos de limpeza fornecidos. Trabalho para dois sábados consecutivos.",
        data=hoje + timedelta(days=9),
        local="São Paulo – SP",
        pagamento=260.00,
        id_empresa=emp["Eventos Brilho S.A."].id_usuario,
        id_categoria=cat["Limpeza e Conservação"].id_categoria,
    ),
    dict(
        titulo="Barman para festa corporativa",
        descricao="Barman com experiência em drinques clássicos e contemporâneos para evento corporativo com 80 pessoas. Uniforme e materiais fornecidos.",
        data=hoje + timedelta(days=12),
        local="Brasília – DF",
        pagamento=500.00,
        id_empresa=emp["Eventos Brilho S.A."].id_usuario,
        id_categoria=cat["Eventos e Hospitalidade"].id_categoria,
    ),
]

vagas = [models.Vaga(**v) for v in vagas_raw]
db.add_all(vagas)
db.flush()

# ── 5. Candidaturas ───────────────────────────────────────────────────────────
candidaturas_raw = [
    # vaga 0 – Dev Python
    (vagas[0], free["Ana Souza"],    "pendente"),
    (vagas[0], free["Diego Faria"],  "aceito"),
    (vagas[0], free["Felipe Nunes"], "pendente"),
    # vaga 2 – Garçom
    (vagas[2], free["Bruno Lima"],   "pendente"),
    (vagas[2], free["Carla Mendes"], "recusado"),
    # vaga 6 – Entregador
    (vagas[6], free["Bruno Lima"],   "aceito"),
    (vagas[6], free["Elisa Rocha"],  "pendente"),
    # vaga 8 – Tutor
    (vagas[8], free["Carla Mendes"], "pendente"),
    (vagas[8], free["Ana Souza"],    "aceito"),
    # vaga 9 – Designer
    (vagas[9], free["Felipe Nunes"], "pendente"),
    (vagas[9], free["Elisa Rocha"],  "recusado"),
]

cands = [
    models.Candidatura(
        id_usuario=u.id_usuario,
        id_vaga=v.id_vaga,
        status=s,
    )
    for v, u, s in candidaturas_raw
]
db.add_all(cands)
db.commit()

print("✅  Seed concluído!")
print(f"   • {len(cats)} categorias")
print(f"   • {len(empresas)} empresas  (senha: senha123)")
print(f"   • {len(freelancers)} freelancers (senha: senha123)")
print(f"   • {len(vagas)} vagas")
print(f"   • {len(cands)} candidaturas")
print()
print("Logins de teste:")
print("  Empresa   → tech@trampos.dev      / senha123")
print("  Freelancer→ ana@trampos.dev       / senha123")
