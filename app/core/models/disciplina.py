from sqlalchemy import Column, String, Integer, ForeignKey
from config.db_config import Base

class Disciplina(Base):
    __tablename__ = "disciplinas"
    codigo_disciplina = Column(String(7), primary_key=True, index=True)
    disciplina = Column(String(100), index=True)
    creditos = Column(Integer, index=True)
    horas = Column(Integer, index=True)
    tipo = Column(String(50), index=True)
    semestre = Column(Integer, index=True)
    codigo_curriculo = Column(String(4), index=True, primary_key=True)
    codigo_curso = Column(String(8), ForeignKey('cursos.codigo_curso'), primary_key=True, index=True)

    def __repr__(self):
        return f"Disciplina: {self.disciplina}, Codigo: {self.codigo_disciplina}"