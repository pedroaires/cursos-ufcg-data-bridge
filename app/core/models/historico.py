from sqlalchemy import Column, String, Float, ForeignKey, PrimaryKeyConstraint, ForeignKeyConstraint
from config.db_config import Base

class Historico(Base):
    __tablename__ = "historico"
    matricula_fake = Column(String(9), primary_key=True, index=True)
    codigo_curso = Column(String(8), index=True)
    codigo_curriculo = Column(String(4), index=True)
    codigo_disciplina = Column(String(7), index=True)
    periodo = Column(Float, primary_key=True)
    media = Column(Float, index=True)
    situacao = Column(String(50), index=True)

    __table_args__ = (
        PrimaryKeyConstraint('codigo_disciplina', 'codigo_curriculo', 'codigo_curso', 'periodo', 'matricula_fake'),
        ForeignKeyConstraint(
            ['codigo_curriculo', 'codigo_curso', 'codigo_disciplina'],
            ['disciplinas.codigo_curriculo', 'disciplinas.codigo_curso', 'disciplinas.codigo_disciplina']
        ),
    )
    def __repr__(self):
        return f"Matricula: {self.matricula_fake}, Disciplina: {self.codigo_disciplina}, Periodo: {self.periodo}, Media: {self.media}, Situacao: {self.situacao}"