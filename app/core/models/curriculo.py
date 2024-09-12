from sqlalchemy import Column, Integer, Float, String, ForeignKey
from config.db_config import Base

class Curriculo(Base):
    __tablename__ = "curriculos"
    codigo_curriculo = Column(String(4), primary_key=True, index=True)
    codigo_curso = Column(String(8), ForeignKey('cursos.codigo_curso', ondelete="CASCADE"), primary_key=True, index=True)
    min_periodos = Column(Integer, index=True)
    max_periodos = Column(Integer, index=True)
    min_creditos_optativos = Column(Integer, index=True)
    carga_horaria_minima_total = Column(Integer, index=True)
    def __repr__(self):
        return f"Curriculo: {self.codigo_curriculo}, Curso: {self.codigo_curso}"