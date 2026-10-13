import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import make_url, URL
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv(Path(__file__).resolve().parents[2] / '.env')


def database_url():
    if os.getenv('DATABASE_URL'):
        url = make_url(os.environ['DATABASE_URL'])
    else:
        url = URL.create(
            'mysql+pymysql', username=os.getenv('MYSQL_USER', 'gate_access'),
            password=os.environ['MYSQL_PASSWORD'],
            host=os.getenv('MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            database=os.getenv('MYSQL_DATABASE', 'gate_access'),
            query={'charset': 'utf8mb4'},
        )
    if url.drivername != 'mysql+pymysql':
        raise ValueError('This project now requires mysql+pymysql; use SOURCE_DATABASE_URL for PostgreSQL transfer.')
    return url


DATABASE_URL = database_url()
engine = create_engine(
    DATABASE_URL, pool_pre_ping=True, pool_recycle=1800,
    isolation_level='READ COMMITTED',
    connect_args={'init_command': "SET time_zone = '+00:00'"},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base(metadata=MetaData(naming_convention={
    'ix': 'ix_%(table_name)s_%(column_0_name)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}))
