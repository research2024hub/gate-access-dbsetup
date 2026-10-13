import os
import unittest
os.environ.setdefault('DATABASE_URL', 'mysql+pymysql://test:test@127.0.0.1/gate_access_test')
from sqlalchemy import create_engine, MetaData, text
from scripts.transfer_postgres import digest, legacy_message


class MessageTransferTests(unittest.TestCase):
    def test_legacy_message_checksum_matches_null_gate_target(self):
        engine = create_engine('sqlite://')
        with engine.begin() as conn:
            conn.execute(text('CREATE TABLE old_messages (id INTEGER PRIMARY KEY, topic TEXT, message TEXT)'))
            conn.execute(text('CREATE TABLE new_messages (id INTEGER PRIMARY KEY, topic TEXT, message TEXT, gate_id INTEGER)'))
            conn.execute(text("INSERT INTO old_messages VALUES (1,'Update','Original message')"))
            meta = MetaData()
            meta.reflect(conn)
            original = conn.execute(meta.tables['old_messages'].select()).mappings().one()
            conn.execute(meta.tables['new_messages'].insert(), legacy_message(original))
            names = ['id', 'gate_id', 'topic', 'message']
            self.assertEqual(digest(conn, meta.tables['old_messages'], names, legacy_message),
                             digest(conn, meta.tables['new_messages'], names))
            self.assertNotIn('gate_id', original)
