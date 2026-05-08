# SQLAlchemy models were removed from this project.
# The backend now uses raw MySQL access through PyMySQL.
    vaga = relationship("Vaga", back_populates="candidaturas")
