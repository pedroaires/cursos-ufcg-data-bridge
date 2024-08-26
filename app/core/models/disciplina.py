from sqlalchemy import Column, String, Integer, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint
from config.db_config import Base

class Disciplina(Base):
    __tablename__ = "disciplinas"
    codigo_disciplina = Column(String(7), primary_key=True, index=True)
    disciplina = Column(String(100), index=True)
    creditos = Column(Integer, index=True)
    horas = Column(Integer, index=True)
    tipo = Column(String(50), index=True)
    semestre = Column(Integer, index=True)
    codigo_curriculo = Column(String(4), index=True)
    codigo_curso = Column(String(8), index=True)

    __table_args__ = (
        PrimaryKeyConstraint('codigo_disciplina', 'codigo_curriculo', 'codigo_curso'),
        ForeignKeyConstraint(
            ['codigo_curriculo', 'codigo_curso'],
            ['curriculos.codigo_curriculo', 'curriculos.codigo_curso']
        ),
        UniqueConstraint('codigo_curriculo', 'codigo_curso', 'codigo_disciplina', name='uix_disciplina_composto')
    )

    def __repr__(self):
        return f"Disciplina: {self.disciplina}, Codigo: {self.codigo_disciplina}"