from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import bcrypt
from app.database import get_db
from app import models, schemas

router = APIRouter()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


@router.post("/usuarios", response_model=schemas.UsuarioOut, status_code=201)
def criar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado.")

    dados = usuario.model_dump()
    dados["senha"] = hash_password(dados["senha"])
    db_usuario = models.Usuario(**dados)
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


@router.get("/usuarios", response_model=list[schemas.UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(models.Usuario).all()


@router.get("/usuarios/{id_usuario}", response_model=schemas.UsuarioOut)
def buscar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return usuario


@router.put("/usuarios/{id_usuario}", response_model=schemas.UsuarioOut)
def atualizar_usuario(
    id_usuario: int,
    dados: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
):
    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    update_data = dados.model_dump(exclude_unset=True)

    if "email" in update_data:
        em_uso = (
            db.query(models.Usuario)
            .filter(
                models.Usuario.email == update_data["email"],
                models.Usuario.id_usuario != id_usuario,
            )
            .first()
        )
        if em_uso:
            raise HTTPException(status_code=400, detail="Email já em uso por outro usuário.")

    if "senha" in update_data:
        update_data["senha"] = hash_password(update_data["senha"])

    for campo, valor in update_data.items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/usuarios/{id_usuario}", status_code=204)
def deletar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    db.delete(usuario)
    db.commit()
