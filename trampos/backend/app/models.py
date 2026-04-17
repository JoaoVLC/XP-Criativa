from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Date, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class Usuario(Base):
    __tablename__ = "Usuario"

    id_usuario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha = Column(String(255), nullable=False)
    tipo = Column(Enum("empresa", "freelancer"), nullable=False)

    vagas = relationship("Vaga", back_populates="empresa", foreign_keys="Vaga.id_empresa")
    candidaturas = relationship("Candidatura", back_populates="usuario")


class Categoria(Base):
    __tablename__ = "Categoria"

    id_categoria = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False)

    vagas = relationship("Vaga", back_populates="categoria")


class Vaga(Base):
    __tablename__ = "Vaga"

    id_vaga = Column(Integer, primary_key=True, index=True, autoincrement=True)
    titulo = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=False)
    data = Column(Date, nullable=False)
    local = Column(String(150), nullable=False)
    pagamento = Column(Numeric(10, 2), nullable=False)
    id_empresa = Column(Integer, ForeignKey("Usuario.id_usuario", ondelete="CASCADE"), nullable=False)
    id_categoria = Column(Integer, ForeignKey("Categoria.id_categoria", ondelete="SET NULL"), nullable=True)

    empresa = relationship("Usuario", back_populates="vagas", foreign_keys=[id_empresa])
    categoria = relationship("Categoria", back_populates="vagas")
    candidaturas = relationship("Candidatura", back_populates="vaga")


class Candidatura(Base):
    __tablename__ = "Candidatura"

    id_candidatura = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("Usuario.id_usuario", ondelete="CASCADE"), nullable=False)
    id_vaga = Column(Integer, ForeignKey("Vaga.id_vaga", ondelete="CASCADE"), nullable=False)
    status = Column(Enum("pendente", "aceito", "recusado"), default="pendente")

    usuario = relationship("Usuario", back_populates="candidaturas")
    vaga = relationship("Vaga", back_populates="candidaturas")
