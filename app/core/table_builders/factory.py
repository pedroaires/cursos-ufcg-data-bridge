from .cursos_builder import CursosTableBuilder
from .alunos_builder import AlunosTableBuilder

class TableBuilderFactory:
    _builders = {
        'Cursos': CursosTableBuilder,
        'Alunos': AlunosTableBuilder,
    }

    @classmethod
    def create_builder(cls, builder_name):
        builder_class = cls._builders.get(builder_name)
        if builder_class is None:
            raise ValueError(f"Unknown builder: {builder_name}")
        return builder_class()