from sqlalchemy import Column, Integer, Float, String, ForeignKey, UniqueConstraint
from config.db_config import Base

class Aluno(Base):
    __tablename__ = "alunos"

    id_aluno = Column(Integer, primary_key=True, index=True, autoincrement=True)
    matricula = Column(Integer, index=True)
    periodo_ingressao = Column(String(10), index=True)
    motivo_inatividade = Column(String(50), index=True)
    codigo_curso = Column(String(8), ForeignKey('cursos.codigo_curso', ondelete="CASCADE"), index=True)
    situacao = Column(String(50), index=True)

    __table_args__ = (
        UniqueConstraint('matricula', 'codigo_curso', name='uix_matricula_curso'),
    )
    

    def __repr__(self):
        return f"Aluno: {self.id_aluno}, Periodo de Ingressao: {self.periodo_ingressao}, Curso: {self.codigo_curso}, Evasao: {self.codigo_evasao}"