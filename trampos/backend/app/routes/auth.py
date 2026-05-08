from fastapi import APIRouter, Depends, HTTPException
import bcrypt
from ..database import get_db
from .. import schemas

router = APIRouter()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


@router.post('/login', response_model=schemas.UsuarioOut)
def login(credenciais: schemas.LoginRequest, db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute(
            'SELECT id_usuario, nome, email, senha, tipo, avatar_url FROM Usuario WHERE email = %s',
            (credenciais.email,),
        )
        usuario = cur.fetchone()
    if not usuario or not verify_password(credenciais.senha, usuario['senha']):
        raise HTTPException(status_code=401, detail='Email ou senha incorretos.')
    usuario.pop('senha', None)
    return usuario
