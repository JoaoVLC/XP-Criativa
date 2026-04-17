from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import bcrypt
from app.database import get_db
from app import models, schemas

router = APIRouter()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


@router.post("/login", response_model=schemas.UsuarioOut)
def login(credenciais: schemas.LoginRequest, db: Session = Depends(get_db)):
    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.email == credenciais.email)
        .first()
    )
    if not usuario or not verify_password(credenciais.senha, usuario.senha):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos.")
    return usuario
