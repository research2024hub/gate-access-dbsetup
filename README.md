# Gate Access database — MySQL

SQLAlchemy models and Alembic migrations for 25 gate-access tables. This repository
contains database setup code, not an HTTP API or website. MySQL 8.4 is the deployment
target. MariaDB and older MySQL releases are not supported.

## Start locally

1. Start Docker Desktop.
2. Use Python 3.12 and a fresh virtual environment:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

3. If `.env` does not exist, copy `.env.example` to `.env` and replace both password
   placeholders with different random passwords. The converted working copy already
   has random MySQL passwords and preserves its old URL as `SOURCE_DATABASE_URL`.
   Keep `.env` private (`chmod 600 .env`). Shell environment variables override it.
4. Start MySQL and create the empty schema:

   ```bash
   docker compose up -d --wait
   python -m alembic upgrade head
   ```

5. **For your existing records**, follow [the transfer guide](docs/MYSQL_MIGRATION.md).
   Do not seed first. For a completely new installation only:

   ```bash
   python -m scripts.seed
   ```

`alembic upgrade head` intentionally creates no seed rows, allowing transfer of
existing primary keys. Do not run `Base.metadata.create_all()` to install this
schema: it does not install business-rule triggers.

## Guides

- [Project requirements and acceptance criteria](docs/PROJECT_REQUIREMENTS.md)
- [Student guide: every table, relationship, trigger, and design decision](docs/DATABASE_STUDENT_GUIDE.md)
- [Browser/print edition of the student guide](docs/DATABASE_STUDENT_GUIDE.html)
- [Word edition of the student guide](docs/DATABASE_STUDENT_GUIDE.docx)
- [Gate-specific messages: mysql_0003 deployment and delivery boundaries](docs/MESSAGE_GATE_MIGRATION.md)
- [Move existing PostgreSQL records](docs/MYSQL_MIGRATION.md)
- [Host MySQL on EC2, step by step](docs/EC2_MYSQL_HOSTING.md)
- [Schema export](erd/gate_access_erd.sql)

The original PostgreSQL migrations and reviews are in `archive/postgresql/` for
reference, outside the active Alembic revision path. They are not MySQL instructions.
The old Python virtual environment may still contain the PostgreSQL driver; use a
fresh environment above. `requirements.txt` is the pinned runtime install list;
`requirements-transfer.txt` additionally installs the PostgreSQL reader. Pipfile is
retained as an alternative manifest; its obsolete PostgreSQL lockfile is archived.

## Checks

```bash
python -m unittest discover -s tests -v
python -m alembic upgrade head --sql > /tmp/gate_access_schema.sql
```

Live integration tests additionally require a **new, empty, disposable** database
whose name starts with `gate_access_test`. They create and drop its application
tables. Never point them at your real database:

```bash
DATABASE_URL='mysql+pymysql://test_user:password@127.0.0.1:13306/gate_access_test' \
TEST_DATABASE_URL='mysql+pymysql://test_user:password@127.0.0.1:13306/gate_access_test' \
python -m unittest discover -s tests -v
```

MySQL DDL auto-commits: a failed migration may leave partial tables. Diagnose the
failure, then recreate only the disposable empty target before retrying. Never
reset a target that already contains transferred records. SQL export from Alembic
is for review; use Alembic's online command for installation. The ERD SQL export
includes MySQL client delimiters for triggers.
