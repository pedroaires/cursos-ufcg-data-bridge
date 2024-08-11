import sys
import os

# Import the task you want to run
from core.tasks.cursos_tasks import fetch_cursos

# Trigger the task
result = fetch_cursos.delay()
print(f"Task result ID: {result.id}")

# Optionally, you can wait for the result
print(f"Task result: {result.get(timeout=10)}")