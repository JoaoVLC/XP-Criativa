"""
seed.py — popula o banco trampos com dados fake para testes de frontend.
Execução: python seed.py  (dentro do venv, na pasta backend/)
"""

from datetime import date, timedelta
import bcrypt

try:
    from .app.database import get_db
except ImportError:
    from app.database import get_db


def hash_senha(s: str) -> str:
    return bcrypt.hashpw(s.encode(), bcrypt.gensalt()).decode()


def main():
    with next(get_db()) as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM Candidatura')
            cur.execute('DELETE FROM Vaga')
            cur.execute('DELETE FROM Categoria')
            cur.execute('DELETE FROM Usuario')
            conn.commit()

            categorias_nomes = [
                'Limpeza e Conservação',
                'Eventos e Hospitalidade',
                'Construção e Reformas',
                'Tecnologia e TI',
                'Educação e Tutoria',
                'Entregas e Logística',
                'Design e Criação',
            ]
            categoria_ids = {}
            for nome in categorias_nomes:
                cur.execute('INSERT INTO Categoria (nome) VALUES (%s)', (nome,))
                categoria_ids[nome] = cur.lastrowid

            senha_hash = hash_senha('senha123')
            empresas_raw = [
                ('TechRápido Ltda.',      'tech@trampos.dev'),
                ('Eventos Brilho S.A.',   'brilho@trampos.dev'),
                ('Construtech Reformas',  'construtech@trampos.dev'),
                ('Click Entregas',        'click@trampos.dev'),
                ('EduFácil Cursos',       'edufacil@trampos.dev'),
            ]
            freelancers_raw = [
                ('Ana Souza',       'ana@trampos.dev'),
                ('Bruno Lima',      'bruno@trampos.dev'),
                ('Carla Mendes',    'carla@trampos.dev'),
                ('Diego Faria',     'diego@trampos.dev'),
                ('Elisa Rocha',     'elisa@trampos.dev'),
                ('Felipe Nunes',    'felipe@trampos.dev'),
            ]
            user_ids = {}
            for nome, email in empresas_raw:
                cur.execute('INSERT INTO Usuario (nome, email, senha, tipo) VALUES (%s, %s, %s, %s)',
                            (nome, email, senha_hash, 'empresa'))
                user_ids[nome] = cur.lastrowid
            for nome, email in freelancers_raw:
                cur.execute('INSERT INTO Usuario (nome, email, senha, tipo) VALUES (%s, %s, %s, %s)',
                            (nome, email, senha_hash, 'freelancer'))
                user_ids[nome] = cur.lastrowid

            hoje = date.today()
            vagas_raw = [
                dict(titulo='Desenvolvedor Python Freelancer', descricao='Precisamos de um desenvolvedor Python para criar scripts de automação e integração de APIs REST. Experiência com FastAPI é um diferencial.', data=hoje + timedelta(days=5), local='Remoto', pagamento=850.00, id_empresa=user_ids['TechRápido Ltda.'], id_categoria=categoria_ids['Tecnologia e TI']),
                dict(titulo='Suporte TI para evento corporativo', descricao='Necessitamos de técnico de TI para suporte presencial durante evento de 2 dias em São Paulo. Configuração de redes, projetores e notebooks.', data=hoje + timedelta(days=10), local='São Paulo – SP', pagamento=600.00, id_empresa=user_ids['TechRápido Ltda.'], id_categoria=categoria_ids['Tecnologia e TI']),
                dict(titulo='Garçom para casamento', descricao='Buscamos garçom experiente para atendimento em cerimônia de casamento com 150 convidados. Traje social obrigatório. Experiência mínima de 1 ano.', data=hoje + timedelta(days=7), local='Campinas – SP', pagamento=350.00, id_empresa=user_ids['Eventos Brilho S.A.'], id_categoria=categoria_ids['Eventos e Hospitalidade']),
                dict(titulo='Recepcionista para conferência', descricao='Vaga para recepcionista durante conferência de negócios de 3 dias. Fluência em inglês é obrigatória. Boa comunicação e apresentação.', data=hoje + timedelta(days=14), local='Rio de Janeiro – RJ', pagamento=480.00, id_empresa=user_ids['Eventos Brilho S.A.'], id_categoria=categoria_ids['Eventos e Hospitalidade']),
                dict(titulo='Pintor de apartamento', descricao='Pintura completa de apartamento 3 quartos, área total de 85m². Material fornecido pelo contratante. Prazo de entrega: 4 dias corridos.', data=hoje + timedelta(days=3), local='Belo Horizonte – MG', pagamento=1200.00, id_empresa=user_ids['Construtech Reformas'], id_categoria=categoria_ids['Construção e Reformas']),
                dict(titulo='Pedreiro para reforma de banheiro', descricao='Reforma completa de banheiro: remoção de azulejos, assentamento de novos revestimentos, troca de louças e metais. Experiência comprovada.', data=hoje + timedelta(days=2), local='Curitiba – PR', pagamento=900.00, id_empresa=user_ids['Construtech Reformas'], id_categoria=categoria_ids['Construção e Reformas']),
                dict(titulo='Entregador moto para fim de semana', descricao='Entregador com moto própria para cobrir rota de entregas expressas durante o final de semana. Região central de Porto Alegre. CNH obrigatória.', data=hoje + timedelta(days=4), local='Porto Alegre – RS', pagamento=420.00, id_empresa=user_ids['Click Entregas'], id_categoria=categoria_ids['Entregas e Logística']),
                dict(titulo='Auxiliar de logística para Black Friday', descricao='Auxiliar para separação, embalagem e organização de pedidos em galpão logístico durante período de Black Friday. Turno integral.', data=hoje + timedelta(days=20), local='Barueri – SP', pagamento=320.00, id_empresa=user_ids['Click Entregas'], id_categoria=categoria_ids['Entregas e Logística']),
                dict(titulo='Tutor de matemática para ensino médio', descricao='Tutor para aulas particulares de matemática para alunos do ensino médio com dificuldades em álgebra e geometria. 2 vezes por semana.', data=hoje + timedelta(days=6), local='Florianópolis – SC', pagamento=280.00, id_empresa=user_ids['EduFácil Cursos'], id_categoria=categoria_ids['Educação e Tutoria']),
                dict(titulo='Designer para criação de identidade visual', descricao='Designer freelancer para criação de logo, paleta de cores e manual de marca para startup. Entrega em até 7 dias. Portfólio necessário.', data=hoje + timedelta(days=8), local='Remoto', pagamento=1500.00, id_empresa=user_ids['TechRápido Ltda.'], id_categoria=categoria_ids['Design e Criação']),
                dict(titulo='Faxineira para escritório', descricao='Serviço de limpeza completa em escritório comercial de 200m². Produtos de limpeza fornecidos. Trabalho para dois sábados consecutivos.', data=hoje + timedelta(days=9), local='São Paulo – SP', pagamento=260.00, id_empresa=user_ids['Eventos Brilho S.A.'], id_categoria=categoria_ids['Limpeza e Conservação']),
                dict(titulo='Barman para festa corporativa', descricao='Barman com experiência em drinques clássicos e contemporâneos para evento corporativo com 80 pessoas. Uniforme e materiais fornecidos.', data=hoje + timedelta(days=12), local='Brasília – DF', pagamento=500.00, id_empresa=user_ids['Eventos Brilho S.A.'], id_categoria=categoria_ids['Eventos e Hospitalidade']),
            ]
            vaga_ids = {}
            for vaga in vagas_raw:
                cur.execute('INSERT INTO Vaga (titulo, descricao, data, local, pagamento, id_empresa, id_categoria) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                            (vaga['titulo'], vaga['descricao'], vaga['data'], vaga['local'], vaga['pagamento'], vaga['id_empresa'], vaga['id_categoria']))
                vaga_ids[vaga['titulo']] = cur.lastrowid

            candidaturas_raw = [
                (vaga_ids['Desenvolvedor Python Freelancer'], user_ids['Ana Souza'], 'pendente'),
                (vaga_ids['Desenvolvedor Python Freelancer'], user_ids['Diego Faria'], 'aceito'),
                (vaga_ids['Desenvolvedor Python Freelancer'], user_ids['Felipe Nunes'], 'pendente'),
                (vaga_ids['Garçom para casamento'], user_ids['Bruno Lima'], 'pendente'),
                (vaga_ids['Garçom para casamento'], user_ids['Carla Mendes'], 'recusado'),
                (vaga_ids['Entregador moto para fim de semana'], user_ids['Bruno Lima'], 'aceito'),
                (vaga_ids['Entregador moto para fim de semana'], user_ids['Elisa Rocha'], 'pendente'),
                (vaga_ids['Tutor de matemática para ensino médio'], user_ids['Carla Mendes'], 'pendente'),
                (vaga_ids['Tutor de matemática para ensino médio'], user_ids['Ana Souza'], 'aceito'),
                (vaga_ids['Designer para criação de identidade visual'], user_ids['Felipe Nunes'], 'pendente'),
                (vaga_ids['Designer para criação de identidade visual'], user_ids['Elisa Rocha'], 'recusado'),
            ]
            for id_vaga, id_usuario, status in candidaturas_raw:
                cur.execute('INSERT INTO Candidatura (id_usuario, id_vaga, status) VALUES (%s, %s, %s)', (id_usuario, id_vaga, status))
            conn.commit()

    print('✅  Seed concluído!')
    print('   • 7 categorias')
    print('   • 5 empresas  (senha: senha123)')
    print('   • 6 freelancers (senha: senha123)')
    print('   • 13 vagas')
    print('   • 11 candidaturas')


if __name__ == '__main__':
    main()
