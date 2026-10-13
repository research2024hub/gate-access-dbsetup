"""Development helper for the initial baseline only; do not use after deployment."""
from pathlib import Path
import ast
import pprint
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects.mysql import dialect
from app.db.database import Base
import app.db.models
from scripts.schema_rules import trigger_statements


def main():
    ddl = []
    for table in Base.metadata.sorted_tables:
        ddl.append(str(CreateTable(table).compile(dialect=dialect())).strip())
        for index in sorted(table.indexes, key=lambda i: i.name):
            ddl.append(str(CreateIndex(index).compile(dialect=dialect())))
    rules = list(trigger_statements(Base.metadata.sorted_tables))
    path = Path('alembic/versions/mysql_0001_initial.py')
    source = path.read_text()
    for name, value in [('DDL', ddl), ('TRIGGERS', rules), ('TABLES', [t.name for t in Base.metadata.sorted_tables])]:
        node = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.Assign) and n.targets[0].id == name)
        lines = source.splitlines(keepends=True)
        lines[node.lineno-1:node.end_lineno] = [name + ' = ' + pprint.pformat(value, width=100, sort_dicts=False) + '\n']
        source = ''.join(lines)
    path.write_text(source)
    Path('erd/gate_access_erd.sql').write_text(
        '-- MySQL schema export, generated from mysql_0001. Use Alembic for installation.\n'
        + ';\n\n'.join(ddl) + ';\n\nDELIMITER $$\n'
        + '\n'.join(s + '$$' for _, s in rules) + '\nDELIMITER ;\n')

if __name__ == '__main__':
    main()
