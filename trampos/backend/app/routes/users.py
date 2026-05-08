from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import bcrypt
import os
from pathlib import Path
import shutil
from ..database import get_db
from .. import schemas

router = APIRouter()
AVATARS_DIR = Path(__file__).resolve().parents[2] / 'uploads' / 'avatars'


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


@router.post('/usuarios', response_model=schemas.UsuarioOut, status_code=201)
def criar_usuario(usuario: schemas.UsuarioCreate, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('SELECT 1 FROM Usuario WHERE email = %s', (usuario.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail='Email já cadastrado.')
        senha_hash = hash_password(usuario.senha)
        cur.execute(
            'INSERT INTO Usuario (nome, email, senha, tipo) VALUES (%s, %s, %s, %s)',
            (usuario.nome, usuario.email, senha_hash, usuario.tipo),
        )
        db.commit()
        usuario_id = cur.lastrowid
        cur.execute('SELECT id_usuario, nome, email, tipo, avatar_url FROM Usuario WHERE id_usuario = %s', (usuario_id,))
        usuario_data = cur.fetchone()
    return usuario_data


@router.get('/usuarios', response_model=list[schemas.UsuarioOut])
def listar_usuarios(db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('SELECT id_usuario, nome, email, tipo, avatar_url FROM Usuario')
        return cur.fetchall()


@router.get('/usuarios/{id_usuario}', response_model=schemas.UsuarioOut)
def buscar_usuario(id_usuario: int, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute('SELECT id_usuario, nome, email, tipo, avatar_url FROM Usuario WHERE id_usuario = %s', (id_usuario,))
        usuario = cur.fetchone()
    if not usuario:
        raise HTTPException(status_code=404, detail='Usuário não encontrado.')
    return usuario


@router.put('/usuarios/{id_usuario}', response_model=schemas.UsuarioOut)
def atualizar_usuario(
    id_usuario: int,
    dados: schemas.UsuarioUpdate,
    id_usuario_atual: int,
    db=Depends(get_db),
):
    if id_usuario != id_usuario_atual:
        raise HTTPException(status_code=403, detail='Acesso negado.')

    update_data = dados.model_dump(exclude_unset=True)
    if not update_data:
        with db.cursor() as cur:
            cur.execute('SELECT id_usuario, nome, email, tipo, avatar_url FROM Usuario WHERE id_usuario = %s', (id_usuario,))
            usuario = cur.fetchone()
            if not usuario:
                raise HTTPException(status_code=404, detail='Usuário não encontrado.')
            return usuario

    with db.cursor() as cur:
        cur.execute('SELECT id_usuario FROM Usuario WHERE id_usuario = %s', (id_usuario,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='Usuário não encontrado.')

        if 'email' in update_data:
            cur.execute('SELECT id_usuario FROM Usuario WHERE email = %s AND id_usuario != %s', (update_data['email'], id_usuario))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail='Email já em uso por outro usuário.')

        if 'senha' in update_data:
            update_data['senha'] = hash_password(update_data['senha'])

        fields = []
        values = []
        for campo, valor in update_data.items():
            fields.append(f"{campo} = %s")
            values.append(valor)
        values.append(id_usuario)
        cur.execute(f"UPDATE Usuario SET {', '.join(fields)} WHERE id_usuario = %s", tuple(values))
        db.commit()
        cur.execute('SELECT id_usuario, nome, email, tipo, avatar_url FROM Usuario WHERE id_usuario = %s', (id_usuario,))
        usuario = cur.fetchone()
    return usuario


@router.post('/usuarios/{id_usuario}/avatar', response_model=schemas.UsuarioOut)
def upload_avatar(
    id_usuario: int,
    id_usuario_atual: int,
    avatar: UploadFile = File(...),
    db=Depends(get_db),
):
    if id_usuario != id_usuario_atual:
        raise HTTPException(status_code=403, detail='Acesso negado.')

    with db.cursor() as cur:
        cur.execute('SELECT id_usuario FROM Usuario WHERE id_usuario = %s', (id_usuario,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='Usuário não encontrado.')

    if not avatar.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='Envie apenas arquivos de imagem.')

    AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    extensao = os.path.splitext(avatar.filename)[1]
    nome_arquivo = f'user_{id_usuario}{extensao}'
    caminho = AVATARS_DIR / nome_arquivo
    with open(caminho, 'wb') as buffer:
        shutil.copyfileobj(avatar.file, buffer)

    avatar_url = f'http://localhost:8000/uploads/avatars/{nome_arquivo}'
    with db.cursor() as cur:
        cur.execute('UPDATE Usuario SET avatar_url = %s WHERE id_usuario = %s', (avatar_url, id_usuario))
        db.commit()
        cur.execute('SELECT id_usuario, nome, email, tipo, avatar_url FROM Usuario WHERE id_usuario = %s', (id_usuario,))
        usuario = cur.fetchone()
    return usuario


@router.delete('/usuarios/{id_usuario}', status_code=204)
def deletar_usuario(id_usuario: int, id_usuario_atual: int, db=Depends(get_db)):
    if id_usuario != id_usuario_atual:
        raise HTTPException(status_code=403, detail='Acesso negado.')
    with db.cursor() as cur:
        cur.execute('SELECT id_usuario FROM Usuario WHERE id_usuario = %s', (id_usuario,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail='Usuário não encontrado.')
        cur.execute('DELETE FROM Usuario WHERE id_usuario = %s', (id_usuario,))
        db.commit()
