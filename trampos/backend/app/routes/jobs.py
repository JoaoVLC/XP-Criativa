from fastapi import APIRouter, Depends, HTTPException
from ..database import get_db
from .. import schemas

router = APIRouter()


def _map_vaga_row(row: dict) -> dict:
    vaga = {
        'id_vaga': row['id_vaga'],
        'titulo': row['titulo'],
        'descricao': row['descricao'],
        'data': row['data'],
        'local': row['local'],
        'pagamento': row['pagamento'],
        'id_empresa': row['id_empresa'],
        'id_categoria': row['id_categoria'],
        'empresa': None,
        'categoria': None,
    }
    if row.get('empresa_id') is not None:
        vaga['empresa'] = {
            'id_usuario': row['empresa_id'],
            'nome': row['empresa_nome'],
            'email': row['empresa_email'],
            'tipo': row['empresa_tipo'],
            'avatar_url': row['empresa_avatar_url'],
        }
    if row.get('categoria_id') is not None:
        vaga['categoria'] = {
            'id_categoria': row['categoria_id'],
            'nome': row['categoria_nome'],
        }
    return vaga


def _map_candidatura_row(row: dict) -> dict:
    cand = {
        'id_candidatura': row['id_candidatura'],
        'id_usuario': row['id_usuario'],
        'id_vaga': row['id_vaga'],
        'status': row['status'],
        'usuario': None,
        'vaga': None,
    }
    if row.get('usuario_id') is not None:
        cand['usuario'] = {
            'id_usuario': row['usuario_id'],
            'nome': row['usuario_nome'],
            'email': row['usuario_email'],
            'tipo': row['usuario_tipo'],
            'avatar_url': row['usuario_avatar_url'],
        }
    if row.get('vaga_id') is not None:
        vaga = {
            'id_vaga': row['vaga_id'],
            'titulo': row['vaga_titulo'],
            'descricao': row['vaga_descricao'],
            'data': row['vaga_data'],
            'local': row['vaga_local'],
            'pagamento': row['vaga_pagamento'],
            'id_empresa': row['vaga_id_empresa'],
            'id_categoria': row['vaga_id_categoria'],
            'empresa': None,
            'categoria': None,
        }
        if row.get('empresa_id') is not None:
            vaga['empresa'] = {
                'id_usuario': row['empresa_id'],
                'nome': row['empresa_nome'],
                'email': row['empresa_email'],
                'tipo': row['empresa_tipo'],
                'avatar_url': row['empresa_avatar_url'],
            }
        if row.get('categoria_id') is not None:
            vaga['categoria'] = {
                'id_categoria': row['categoria_id'],
                'nome': row['categoria_nome'],
            }
        cand['vaga'] = vaga
    return cand


def _base_vaga_query() -> str:
    return '''
        SELECT
            v.id_vaga,
            v.titulo,
            v.descricao,
            v.data,
            v.local,
            v.pagamento,
            v.id_empresa,
            v.id_categoria,
            u.id_usuario AS empresa_id,
            u.nome AS empresa_nome,
            u.email AS empresa_email,
            u.tipo AS empresa_tipo,
            u.avatar_url AS empresa_avatar_url,
            c.id_categoria AS categoria_id,
            c.nome AS categoria_nome
        FROM Vaga v
        LEFT JOIN Usuario u ON u.id_usuario = v.id_empresa
        LEFT JOIN Categoria c ON c.id_categoria = v.id_categoria
    '''


@router.put('/categorias/{id_categoria}', response_model=schemas.CategoriaOut)
def atualizar_categoria(id_categoria: int, categoria: schemas.CategoriaCreate, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('SELECT id_categoria FROM Categoria WHERE id_categoria = %s', (id_categoria,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='Categoria não encontrada.')
        cur.execute('UPDATE Categoria SET nome = %s WHERE id_categoria = %s', (categoria.nome, id_categoria))
        db.commit()
        cur.execute('SELECT id_categoria, nome FROM Categoria WHERE id_categoria = %s', (id_categoria,))
        return cur.fetchone()


@router.delete('/categorias/{id_categoria}', status_code=204)
def deletar_categoria(id_categoria: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('SELECT id_categoria FROM Categoria WHERE id_categoria = %s', (id_categoria,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='Categoria não encontrada.')
        cur.execute('DELETE FROM Categoria WHERE id_categoria = %s', (id_categoria,))
        db.commit()


@router.get('/categorias', response_model=list[schemas.CategoriaOut])
def listar_categorias(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('SELECT id_categoria, nome FROM Categoria')
        return cur.fetchall()


@router.post('/categorias', response_model=schemas.CategoriaOut, status_code=201)
def criar_categoria(categoria: schemas.CategoriaCreate, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('INSERT INTO Categoria (nome) VALUES (%s)', (categoria.nome,))
        db.commit()
        categoria_id = cur.lastrowid
        cur.execute('SELECT id_categoria, nome FROM Categoria WHERE id_categoria = %s', (categoria_id,))
        return cur.fetchone()


@router.post('/vagas', response_model=schemas.VagaOut, status_code=201)
def criar_vaga(vaga: schemas.VagaCreate, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('SELECT tipo FROM Usuario WHERE id_usuario = %s', (vaga.id_empresa,))
        empresa = cur.fetchone()
        if not empresa:
            raise HTTPException(status_code=404, detail='Empresa não encontrada.')
        if empresa['tipo'] != 'empresa':
            raise HTTPException(status_code=400, detail='Somente empresas podem criar vagas.')
        cur.execute(
            'INSERT INTO Vaga (titulo, descricao, data, local, pagamento, id_empresa, id_categoria) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (vaga.titulo, vaga.descricao, vaga.data, vaga.local, vaga.pagamento, vaga.id_empresa, vaga.id_categoria),
        )
        db.commit()
        vaga_id = cur.lastrowid
        cur.execute(_base_vaga_query() + ' WHERE v.id_vaga = %s', (vaga_id,))
        return _map_vaga_row(cur.fetchone())


@router.get('/vagas/empresa/{id_empresa}', response_model=list[schemas.VagaOut])
def vagas_da_empresa(id_empresa: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(_base_vaga_query() + ' WHERE v.id_empresa = %s', (id_empresa,))
        return [_map_vaga_row(row) for row in cur.fetchall()]


@router.get('/vagas', response_model=list[schemas.VagaOut])
def listar_vagas(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(_base_vaga_query())
        return [_map_vaga_row(row) for row in cur.fetchall()]


@router.get('/vagas/{id_vaga}', response_model=schemas.VagaOut)
def buscar_vaga(id_vaga: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(_base_vaga_query() + ' WHERE v.id_vaga = %s', (id_vaga,))
        vaga = cur.fetchone()
    if not vaga:
        raise HTTPException(status_code=404, detail='Vaga não encontrada.')
    return _map_vaga_row(vaga)


@router.delete('/vagas/{id_vaga}', status_code=204)
def deletar_vaga(id_vaga: int, id_usuario: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('SELECT id_empresa FROM Vaga WHERE id_vaga = %s', (id_vaga,))
        vaga = cur.fetchone()
        if not vaga:
            raise HTTPException(status_code=404, detail='Vaga não encontrada.')
        if vaga['id_empresa'] != id_usuario:
            raise HTTPException(status_code=403, detail='Você não tem permissão para excluir esta vaga.')
        cur.execute('DELETE FROM Vaga WHERE id_vaga = %s', (id_vaga,))
        db.commit()


@router.post('/candidaturas', response_model=schemas.CandidaturaOut, status_code=201)
def candidatar(candidatura: schemas.CandidaturaCreate, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('SELECT id_vaga FROM Vaga WHERE id_vaga = %s', (candidatura.id_vaga,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='Vaga não encontrada.')
        cur.execute('SELECT tipo FROM Usuario WHERE id_usuario = %s', (candidatura.id_usuario,))
        usuario = cur.fetchone()
        if not usuario:
            raise HTTPException(status_code=404, detail='Usuário não encontrado.')
        if usuario['tipo'] != 'freelancer':
            raise HTTPException(status_code=400, detail='Somente freelancers podem se candidatar.')
        cur.execute('SELECT 1 FROM Candidatura WHERE id_vaga = %s AND id_usuario = %s', (candidatura.id_vaga, candidatura.id_usuario))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail='Você já se candidatou a esta vaga.')
        cur.execute('INSERT INTO Candidatura (id_usuario, id_vaga) VALUES (%s, %s)', (candidatura.id_usuario, candidatura.id_vaga))
        db.commit()
        cand_id = cur.lastrowid
        cur.execute('SELECT id_candidatura, id_usuario, id_vaga, status FROM Candidatura WHERE id_candidatura = %s', (cand_id,))
        return cur.fetchone()


@router.get('/candidaturas/usuario/{id_usuario}', response_model=list[schemas.CandidaturaOut])
def candidaturas_do_usuario(id_usuario: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('''
            SELECT
                c.id_candidatura,
                c.id_usuario,
                c.id_vaga,
                c.status,
                v.id_vaga AS vaga_id,
                v.titulo AS vaga_titulo,
                v.descricao AS vaga_descricao,
                v.data AS vaga_data,
                v.local AS vaga_local,
                v.pagamento AS vaga_pagamento,
                v.id_empresa AS vaga_id_empresa,
                v.id_categoria AS vaga_id_categoria,
                u.id_usuario AS empresa_id,
                u.nome AS empresa_nome,
                u.email AS empresa_email,
                u.tipo AS empresa_tipo,
                u.avatar_url AS empresa_avatar_url,
                cat.id_categoria AS categoria_id,
                cat.nome AS categoria_nome
            FROM Candidatura c
            JOIN Vaga v ON v.id_vaga = c.id_vaga
            LEFT JOIN Usuario u ON u.id_usuario = v.id_empresa
            LEFT JOIN Categoria cat ON cat.id_categoria = v.id_categoria
            WHERE c.id_usuario = %s
        ''', (id_usuario,))
        return [_map_candidatura_row(row) for row in cur.fetchall()]


@router.get('/vagas/{id_vaga}/candidaturas', response_model=list[schemas.CandidaturaOut])
def candidatos_da_vaga(id_vaga: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('SELECT id_vaga FROM Vaga WHERE id_vaga = %s', (id_vaga,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='Vaga não encontrada.')
        cur.execute('''
            SELECT
                c.id_candidatura,
                c.id_usuario,
                c.id_vaga,
                c.status,
                u.id_usuario AS usuario_id,
                u.nome AS usuario_nome,
                u.email AS usuario_email,
                u.tipo AS usuario_tipo,
                u.avatar_url AS usuario_avatar_url
            FROM Candidatura c
            LEFT JOIN Usuario u ON u.id_usuario = c.id_usuario
            WHERE c.id_vaga = %s
        ''', (id_vaga,))
        return [_map_candidatura_row(row) for row in cur.fetchall()]


@router.patch('/candidaturas/{id_candidatura}', response_model=schemas.CandidaturaOut)
def atualizar_candidatura(
    id_candidatura: int,
    dados: schemas.CandidaturaStatusUpdate,
    id_usuario: int,
    db=Depends(get_db),
):
    with db.cursor() as cur:
        cur.execute('SELECT id_vaga FROM Candidatura WHERE id_candidatura = %s', (id_candidatura,))
        candidatura = cur.fetchone()
        if not candidatura:
            raise HTTPException(status_code=404, detail='Candidatura não encontrada.')
        cur.execute('SELECT id_empresa FROM Vaga WHERE id_vaga = %s', (candidatura['id_vaga'],))
        vaga = cur.fetchone()
        if not vaga or vaga['id_empresa'] != id_usuario:
            raise HTTPException(status_code=403, detail='Você não tem permissão para alterar esta candidatura.')
        cur.execute('UPDATE Candidatura SET status = %s WHERE id_candidatura = %s', (dados.status, id_candidatura))
        db.commit()
        cur.execute('SELECT id_candidatura, id_usuario, id_vaga, status FROM Candidatura WHERE id_candidatura = %s', (id_candidatura,))
        return cur.fetchone()
