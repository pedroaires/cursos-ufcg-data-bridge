from sqlalchemy import Column, String, Integer, ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint, Table
from sqlalchemy.orm import relationship
from config.db_config import Base

# Junction table for self-referencing many-to-many relationship
prerequisitos = Table(
    'prerequisitos', Base.metadata,
    Column('disciplina_id', String(100), ForeignKey('disciplinas.id', ondelete="CASCADE")),
    Column('prerequisito_id', String(100), ForeignKey('disciplinas.id', ondelete="CASCADE"))
)

class Disciplina(Base):
    __tablename__ = "disciplinas"
    id = Column(String(100), primary_key=True, index=True)
    codigo_disciplina = Column(String(7), index=True)
    disciplina = Column(String(100), index=True)
    creditos = Column(Integer, index=True)
    horas = Column(Integer, index=True)
    tipo = Column(String(50), index=True)
    semestre = Column(Integer, index=True)
    codigo_curriculo = Column(String(4), index=True)
    codigo_curso = Column(String(8), index=True)

    prerequisitos = relationship(
        "Disciplina",
        secondary=prerequisitos,
        primaryjoin=id==prerequisitos.c.disciplina_id,
        secondaryjoin=id==prerequisitos.c.prerequisito_id,
        backref="dependentes"
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ['codigo_curriculo', 'codigo_curso'],
            ['curriculos.codigo_curriculo', 'curriculos.codigo_curso'],
            ondelete="CASCADE"
        ),
        UniqueConstraint('codigo_curriculo', 'codigo_curso', 'codigo_disciplina', name='uix_disciplina_composto')
    )

    def __repr__(self):
        return f"Disciplina: {self.disciplina}, Codigo: {self.codigo_disciplina}"