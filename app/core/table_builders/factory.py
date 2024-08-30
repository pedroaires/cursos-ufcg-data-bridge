from .cursos_builder import CursosTableBuilder
from .alunos_builder import AlunosTableBuilder
from .curriculos_builder import CurriculosTableBuilder
from .disciplinas_builder import DisciplinasTableBuilder
from .historico_builder import HistoricoTableBuilder
class TableBuilderFactory:
    _builders = {
        'Cursos': CursosTableBuilder,
        'Alunos': AlunosTableBuilder,
        'Curriculos': CurriculosTableBuilder,
        'Disciplinas': DisciplinasTableBuilder,
        'Historico': HistoricoTableBuilder,
    }

    @classmethod
    def create_builder(cls, builder_name):
        builder_class = cls._builders.get(builder_name)
        if builder_class is None:
            raise ValueError(f"Unknown builder: {builder_name}")
        return builder_class()