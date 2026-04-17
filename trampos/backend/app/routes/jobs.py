from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models, schemas

router = APIRouter()


# ── Categorias ────────────────────────────────────────────────────────────────

@router.post("/categorias", response_model=schemas.CategoriaOut, status_code=201)
def criar_categoria(categoria: schemas.CategoriaCreate, db: Session = Depends(get_db)):
    db_cat = models.Categoria(**categoria.model_dump())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat


@router.get("/categorias", response_model=list[schemas.CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(models.Categoria).all()


# ── Vagas ─────────────────────────────────────────────────────────────────────

@router.post("/vagas", response_model=schemas.VagaOut, status_code=201)
def criar_vaga(vaga: schemas.VagaCreate, db: Session = Depends(get_db)):
    empresa = db.query(models.Usuario).filter(models.Usuario.id_usuario == vaga.id_empresa).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    if empresa.tipo != "empresa":
        raise HTTPException(status_code=400, detail="Somente empresas podem criar vagas.")

    db_vaga = models.Vaga(**vaga.model_dump())
    db.add(db_vaga)
    db.commit()
    db.refresh(db_vaga)
    return db_vaga


# NOTE: static-segment routes MUST come before parameterized ones
@router.get("/vagas/empresa/{id_empresa}", response_model=list[schemas.VagaOut])
def vagas_da_empresa(id_empresa: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Vaga)
        .options(joinedload(models.Vaga.empresa), joinedload(models.Vaga.categoria))
        .filter(models.Vaga.id_empresa == id_empresa)
        .all()
    )


@router.get("/vagas", response_model=list[schemas.VagaOut])
def listar_vagas(db: Session = Depends(get_db)):
    return (
        db.query(models.Vaga)
        .options(joinedload(models.Vaga.empresa), joinedload(models.Vaga.categoria))
        .all()
    )


@router.get("/vagas/{id_vaga}", response_model=schemas.VagaOut)
def buscar_vaga(id_vaga: int, db: Session = Depends(get_db)):
    vaga = (
        db.query(models.Vaga)
        .options(joinedload(models.Vaga.empresa), joinedload(models.Vaga.categoria))
        .filter(models.Vaga.id_vaga == id_vaga)
        .first()
    )
    if not vaga:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    return vaga


@router.delete("/vagas/{id_vaga}", status_code=204)
def deletar_vaga(id_vaga: int, db: Session = Depends(get_db)):
    vaga = db.query(models.Vaga).filter(models.Vaga.id_vaga == id_vaga).first()
    if not vaga:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    db.delete(vaga)
    db.commit()


# ── Candidaturas ──────────────────────────────────────────────────────────────

@router.post("/candidaturas", response_model=schemas.CandidaturaOut, status_code=201)
def candidatar(candidatura: schemas.CandidaturaCreate, db: Session = Depends(get_db)):
    vaga = db.query(models.Vaga).filter(models.Vaga.id_vaga == candidatura.id_vaga).first()
    if not vaga:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")

    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == candidatura.id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if usuario.tipo != "freelancer":
        raise HTTPException(status_code=400, detail="Somente freelancers podem se candidatar.")

    duplicata = (
        db.query(models.Candidatura)
        .filter(
            models.Candidatura.id_vaga == candidatura.id_vaga,
            models.Candidatura.id_usuario == candidatura.id_usuario,
        )
        .first()
    )
    if duplicata:
        raise HTTPException(status_code=400, detail="Você já se candidatou a esta vaga.")

    db_cand = models.Candidatura(**candidatura.model_dump())
    db.add(db_cand)
    db.commit()
    db.refresh(db_cand)
    return db_cand


# NOTE: static-segment route BEFORE parameterized
@router.get("/candidaturas/usuario/{id_usuario}", response_model=list[schemas.CandidaturaOut])
def candidaturas_do_usuario(id_usuario: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Candidatura)
        .options(
            joinedload(models.Candidatura.vaga).joinedload(models.Vaga.empresa),
            joinedload(models.Candidatura.vaga).joinedload(models.Vaga.categoria),
        )
        .filter(models.Candidatura.id_usuario == id_usuario)
        .all()
    )


@router.get("/vagas/{id_vaga}/candidaturas", response_model=list[schemas.CandidaturaOut])
def candidatos_da_vaga(id_vaga: int, db: Session = Depends(get_db)):
    vaga = db.query(models.Vaga).filter(models.Vaga.id_vaga == id_vaga).first()
    if not vaga:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    return (
        db.query(models.Candidatura)
        .options(joinedload(models.Candidatura.usuario))
        .filter(models.Candidatura.id_vaga == id_vaga)
        .all()
    )


@router.patch("/candidaturas/{id_candidatura}", response_model=schemas.CandidaturaOut)
def atualizar_candidatura(
    id_candidatura: int,
    dados: schemas.CandidaturaStatusUpdate,
    db: Session = Depends(get_db),
):
    cand = (
        db.query(models.Candidatura)
        .filter(models.Candidatura.id_candidatura == id_candidatura)
        .first()
    )
    if not cand:
        raise HTTPException(status_code=404, detail="Candidatura não encontrada.")
    cand.status = dados.status
    db.commit()
    db.refresh(cand)
    return cand
