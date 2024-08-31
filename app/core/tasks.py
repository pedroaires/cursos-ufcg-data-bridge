from core.celery_app import app
from core.table_builders.factory import TableBuilderFactory

@app.task()
def raise_table_simple(table_name):
    builder = TableBuilderFactory.create_builder(table_name)
    return builder.build()

@app.task()
def raise_table_with_result(task_result, table_name):
    builder = TableBuilderFactory.create_builder(table_name)
    return builder.build(task_result)