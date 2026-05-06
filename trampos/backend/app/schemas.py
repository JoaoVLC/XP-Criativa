from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from datetime import date
from decimal import Decimal


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


# ── Usuario ───────────────────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    tipo: Literal["empresa", "freelancer"]


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    senha: Optional[str] = None


class UsuarioOut(BaseModel):
    id_usuario: int
    nome: str
    email: str
    tipo: str
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True


# ── Categoria ─────────────────────────────────────────────────────────────────

class CategoriaCreate(BaseModel):
    nome: str


class CategoriaOut(BaseModel):
    id_categoria: int
    nome: str

    class Config:
        from_attributes = True


# ── Vaga ──────────────────────────────────────────────────────────────────────

class VagaCreate(BaseModel):
    titulo: str
    descricao: str
    data: date
    local: str
    pagamento: Decimal
    id_empresa: int
    id_categoria: Optional[int] = None


class VagaOut(BaseModel):
    id_vaga: int
    titulo: str
    descricao: str
    data: date
    local: str
    pagamento: Decimal
    id_empresa: int
    id_categoria: Optional[int] = None
    empresa: Optional[UsuarioOut] = None
    categoria: Optional[CategoriaOut] = None

    class Config:
        from_attributes = True


# ── Candidatura ───────────────────────────────────────────────────────────────

class CandidaturaCreate(BaseModel):
    id_usuario: int
    id_vaga: int


class CandidaturaStatusUpdate(BaseModel):
    status: Literal["pendente", "aceito", "recusado"]


class CandidaturaOut(BaseModel):
    id_candidatura: int
    id_usuario: int
    id_vaga: int
    status: str
    usuario: Optional[UsuarioOut] = None
    vaga: Optional[VagaOut] = None  # populated when listing a user's applications

    class Config:
        from_attributes = True
