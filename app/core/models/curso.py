from sqlalchemy import Column, String, Boolean
from config.db_config import Base

class Curso(Base):
    __tablename__ = "cursos"

    codigo_curso = Column(String(8), primary_key=True, index=True)
    nome_comum = Column(String(100), index=True)
    schema = Column(String(100), index=True)
    disponivel = Column(Boolean, default=True)
    campus = Column(String(2), index=True)

    def __repr__(self):
        return f"Curso: {self.nome_comum}, Codigo: {self.codigo_curso}, Campus: {self.campus}"