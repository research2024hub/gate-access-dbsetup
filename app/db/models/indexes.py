"""Query indexes retained from the PostgreSQL migration history."""
from sqlalchemy import Index
from app.db.database import Base

for table, columns in [
    ('logs', ['estate_id', 'date_created']), ('logs', ['type']),
    ('logs', ['date_created']), ('messagedb', ['topic']),
    ('messagedb', ['date_created']), ('accesslog', ['timestamp']),
    ('accesslog', ['license_plate_number', 'timestamp']),
    ('system_metrics', ['device_timestamp']), ('system_metrics', ['received_at']),
]:
    Index('ix_' + table + '_' + '_'.join(columns),
          *(Base.metadata.tables[table].c[c] for c in columns))

for table in Base.metadata.tables.values():
    table.dialect_options['mysql']['engine'] = 'InnoDB'
    table.dialect_options['mysql']['charset'] = 'utf8mb4'
    table.dialect_options['mysql']['collate'] = 'utf8mb4_0900_bin'
