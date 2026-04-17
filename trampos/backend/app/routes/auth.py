from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import get_db
from app import models, schemas

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login", response_model=schemas.UsuarioOut)
def login(credenciais: schemas.LoginRequest, db: Session = Depends(get_db)):
    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.email == credenciais.email)
        .first()
    )
    if not usuario or not pwd_context.verify(credenciais.senha, usuario.senha):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos.")
    return usuario
