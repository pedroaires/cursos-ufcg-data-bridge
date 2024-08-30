from sqlalchemy import Column, Integer, Float, String, ForeignKey
from config.db_config import Base

class Aluno(Base):
    __tablename__ = "alunos"

    id_aluno = Column(Integer, primary_key=True, index=True, autoincrement=True)
    periodo_ingressao = Column(Float, index=True)
    motivo_inatividade = Column(String(50), index=True)
    codigo_curso = Column(String(8), ForeignKey('cursos.codigo_curso', ondelete="CASCADE"), index=True)
    

    def __repr__(self):
        return f"Aluno: {self.id_aluno}, Periodo de Ingressao: {self.periodo_ingressao}, Curso: {self.codigo_curso}, Evasao: {self.codigo_evasao}"