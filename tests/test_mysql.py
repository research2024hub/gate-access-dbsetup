"""Integration tests. TEST_DATABASE_URL must name a disposable gate_access_test* DB."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from alembic import command
from alembic.config import Config


@unittest.skipUnless(os.getenv('TEST_DATABASE_URL'), 'Set TEST_DATABASE_URL to run MySQL integration tests')
class MySQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = make_url(os.environ['TEST_DATABASE_URL'])
        if not url.database.startswith('gate_access_test'):
            raise ValueError('Tests may only use a disposable gate_access_test* database')
        # Run in a separate process with DATABASE_URL=TEST_DATABASE_URL.
        from app.db.database import engine
        if engine.url != url:
            raise ValueError('DATABASE_URL and TEST_DATABASE_URL must match for integration tests')
        cls.engine = engine
        cls.config = Config('alembic.ini')
        command.upgrade(cls.config, 'head')
        from scripts.seed import main
        main()

    @classmethod
    def tearDownClass(cls):
        command.downgrade(cls.config, 'base')

    def test_rules_and_concurrent_capacity(self):
        with self.engine.begin() as c:
            c.execute(text("INSERT INTO estates (name,location_coordinates) VALUES ('Test','0,0')"))
            estate = c.scalar(text("SELECT id FROM estates WHERE name='Test'"))
            group = c.scalar(text('SELECT id FROM access_groups WHERE estate_id=:id'), {'id': estate})
            self.assertIsNotNone(group)
            c.execute(text("INSERT INTO users (email,password) VALUES ('same@example.test','hash')"))
            user = c.scalar(text("SELECT id FROM users WHERE email='same@example.test'"))
            with self.assertRaises(DBAPIError):
                c.execute(text("INSERT INTO users (email,password) VALUES ('same@example.test','hash')"))
            c.execute(text('UPDATE users SET deleted_at=UTC_TIMESTAMP(6) WHERE id=:id'), {'id': user})
            c.execute(text("INSERT INTO users (email,password) VALUES ('same@example.test','hash')"))
            with self.assertRaises(DBAPIError):
                c.execute(text('UPDATE users SET deleted_at=NULL WHERE id=:id'), {'id': user})
            c.execute(text("INSERT INTO personal_info (estate_id,name,access_group_id) VALUES (:e,'Owner',:g)"), {'e':estate,'g':group})
            person = c.scalar(text('SELECT MAX(id) FROM personal_info'))
            c.execute(text("INSERT INTO account_holders (user_id,personal_info_id,house_address) VALUES (:u,:p,'A')"), {'u':user,'p':person})
            holder = c.scalar(text('SELECT MAX(id) FROM account_holders'))
            with self.assertRaises(DBAPIError):
                c.execute(text("INSERT INTO account_holders (user_id,personal_info_id,house_address) VALUES (:u,:p,'B')"), {'u':user,'p':person})
            c.execute(text("INSERT INTO events (creator_id,name,max_num_of_attendees,start_time,end_time) VALUES (:h,'Test',1,'2026-01-01','2026-01-02')"), {'h':holder})
            event_id = c.scalar(text('SELECT MAX(id) FROM events'))
            c.execute(text('INSERT INTO guests () VALUES ()'))
            guest1 = c.scalar(text('SELECT MAX(id) FROM guests'))
            c.execute(text('INSERT INTO guests () VALUES ()'))
            guest2 = c.scalar(text('SELECT MAX(id) FROM guests'))
            self.assertEqual('{}', c.scalar(text('SELECT CAST(other_info AS CHAR) FROM guests WHERE id=:g'), {'g':guest1}))
        barrier = Barrier(2)
        def register(guest):
            try:
                with self.engine.begin() as c:
                    barrier.wait(timeout=10)
                    c.execute(text('INSERT INTO event_registers (event_id,guest_id) VALUES (:e,:g)'), {'e':event_id,'g':guest})
                return True
            except DBAPIError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual([False, True], sorted(pool.map(register, [guest1,guest2])))
        with self.engine.begin() as c:
            self.assertEqual(1, c.scalar(text('SELECT COUNT(*) FROM event_registers WHERE event_id=:e'), {'e':event_id}))
            c.execute(text("INSERT INTO events (creator_id,name,max_num_of_attendees,start_time,end_time) VALUES (:h,'Move target',1,'2026-01-01','2026-01-02')"), {'h':holder})
            target = c.scalar(text('SELECT LAST_INSERT_ID()'))
            registration = c.scalar(text('SELECT id FROM event_registers WHERE event_id=:e'), {'e':event_id})
            c.execute(text('UPDATE event_registers SET event_id=:e WHERE id=:r'), {'e':target,'r':registration})
            self.assertEqual(target,c.scalar(text('SELECT event_id FROM event_registers WHERE id=:r'), {'r':registration}))
            registered_guest = c.scalar(text('SELECT guest_id FROM event_registers WHERE id=:r'), {'r':registration})
            other_guest = guest2 if registered_guest == guest1 else guest1
            with self.assertRaises(DBAPIError) as full:
                c.execute(text('INSERT INTO event_registers (event_id,guest_id) VALUES (:e,:g)'), {'e':target,'g':other_guest})
            self.assertEqual(1644,full.exception.orig.args[0])
            c.execute(text("INSERT INTO logs (actor_user_id,type,message) VALUES (:u,'TEST','Keep')"), {'u':user})
            c.execute(text('DELETE FROM users WHERE id=:u'), {'u':user})
            self.assertIsNone(c.scalar(text("SELECT actor_user_id FROM logs WHERE message='Keep'")))
            self.assertEqual(1,c.scalar(text("SELECT COUNT(*) FROM logs WHERE message='Keep'")))

    def test_phone_uniqueness_and_nullable_email(self):
        with self.engine.connect() as c:
            tx = c.begin()
            try:
                c.execute(text("INSERT INTO users (phone_number,password) VALUES ('+233555000001','hash')"))
                old_id = c.scalar(text('SELECT LAST_INSERT_ID()'))
                with self.assertRaises(DBAPIError) as duplicate:
                    c.execute(text("INSERT INTO users (phone_number,password) VALUES ('+233555000001','hash')"))
                self.assertEqual(1062, duplicate.exception.orig.args[0])
                c.execute(text('UPDATE users SET deleted_at=UTC_TIMESTAMP(6) WHERE id=:id'), {'id':old_id})
                c.execute(text("INSERT INTO users (phone_number,password) VALUES ('+233555000001','hash')"))
                with self.assertRaises(DBAPIError) as restore:
                    c.execute(text('UPDATE users SET deleted_at=NULL WHERE id=:id'), {'id':old_id})
                self.assertEqual(1062, restore.exception.orig.args[0])
            finally:
                tx.rollback()

    def test_membership_across_personal_records_and_soft_delete(self):
        with self.engine.connect() as c:
            tx = c.begin()
            try:
                c.execute(text("INSERT INTO estates (name,location_coordinates) VALUES ('Membership test','1,1')"))
                estate = c.scalar(text('SELECT LAST_INSERT_ID()'))
                group = c.scalar(text('SELECT id FROM access_groups WHERE estate_id=:e'), {'e':estate})
                c.execute(text("INSERT INTO users (email,password) VALUES ('member@example.test','hash')"))
                user = c.scalar(text('SELECT LAST_INSERT_ID()'))
                people = []
                for name in ['First record', 'Second record']:
                    c.execute(text('INSERT INTO personal_info (estate_id,name,access_group_id) VALUES (:e,:n,:g)'),
                              {'e':estate,'n':name,'g':group})
                    people.append(c.scalar(text('SELECT LAST_INSERT_ID()')))
                insert = text("INSERT INTO account_holders (user_id,personal_info_id,house_address) VALUES (:u,:p,'A')")
                c.execute(insert, {'u':user,'p':people[0]})
                holder = c.scalar(text('SELECT LAST_INSERT_ID()'))
                # An ordinary UNIQUE(user_id, personal_info_id) would incorrectly allow this.
                with self.assertRaises(DBAPIError) as duplicate:
                    c.execute(insert, {'u':user,'p':people[1]})
                self.assertEqual(1062, duplicate.exception.orig.args[0])
                # Updating a membership must not treat that same row as a duplicate.
                c.execute(text("UPDATE account_holders SET house_address='B' WHERE id=:id"), {'id':holder})
                c.execute(text('UPDATE account_holders SET deleted_at=UTC_TIMESTAMP(6) WHERE id=:id'), {'id':holder})
                c.execute(insert, {'u':user,'p':people[1]})
                with self.assertRaises(DBAPIError) as restore:
                    c.execute(text('UPDATE account_holders SET deleted_at=NULL WHERE id=:id'), {'id':holder})
                self.assertEqual(1062, restore.exception.orig.args[0])
            finally:
                tx.rollback()

    def test_guest_owner_fk_and_single_report_status(self):
        with self.engine.connect() as c:
            tx = c.begin()
            try:
                c.execute(text("INSERT INTO users (email,password) VALUES ('ownership@example.test','hash')"))
                user = c.scalar(text('SELECT LAST_INSERT_ID()'))
                # This ID belongs to a user only, not to an account holder.
                orphan = 2000000000
                c.execute(text("INSERT INTO users (id,email,password) VALUES (:id,'useronly@example.test','hash')"), {'id':orphan})
                with self.assertRaises(DBAPIError) as missing_owner:
                    c.execute(text('INSERT INTO guests (creator_id) VALUES (:id)'), {'id':orphan})
                self.assertEqual(1452, missing_owner.exception.orig.args[0])
                c.execute(text("INSERT INTO account_holders (user_id,house_address) VALUES (:u,'Test')"), {'u':user})
                holder = c.scalar(text('SELECT LAST_INSERT_ID()'))
                c.execute(text('INSERT INTO guests (creator_id) VALUES (:h)'), {'h':holder})
                c.execute(text("INSERT INTO user_reports (user_id,subject,description) VALUES (:u,'Test','Test')"), {'u':user})
                report = c.scalar(text('SELECT LAST_INSERT_ID()'))
                c.execute(text("INSERT INTO report_status (report_id,status) VALUES (:r,'OPEN')"), {'r':report})
                with self.assertRaises(DBAPIError) as duplicate_status:
                    c.execute(text("INSERT INTO report_status (report_id,status) VALUES (:r,'CLOSED')"), {'r':report})
                self.assertEqual(1062, duplicate_status.exception.orig.args[0])
            finally:
                tx.rollback()

    def test_concurrent_memberships(self):
        with self.engine.begin() as c:
            c.execute(text("INSERT INTO estates (name,location_coordinates) VALUES ('Race estate','race')"))
            estate = c.scalar(text('SELECT LAST_INSERT_ID()'))
            group = c.scalar(text('SELECT id FROM access_groups WHERE estate_id=:e'), {'e': estate})
            c.execute(text("INSERT INTO users (email,password) VALUES ('race@example.test','hash')"))
            user = c.scalar(text('SELECT LAST_INSERT_ID()'))
            people = []
            for name in ['Race one', 'Race two']:
                c.execute(text('INSERT INTO personal_info (estate_id,name,access_group_id) VALUES (:e,:n,:g)'),
                          {'e':estate,'n':name,'g':group})
                people.append(c.scalar(text('SELECT LAST_INSERT_ID()')))
        barrier = Barrier(2)
        def create(person):
            try:
                with self.engine.begin() as c:
                    # Establish a read before the race to expose stale-snapshot errors.
                    c.scalar(text('SELECT COUNT(*) FROM account_holders'))
                    barrier.wait(timeout=10)
                    c.execute(text("INSERT INTO account_holders (user_id,personal_info_id,house_address) VALUES (:u,:p,'Race')"),
                              {'u':user,'p':person})
                return 0
            except DBAPIError as exc:
                return exc.orig.args[0]
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual([0,1062], sorted(pool.map(create, people)))
        with self.engine.connect() as c:
            self.assertEqual(1,c.scalar(text('SELECT COUNT(*) FROM account_holders WHERE user_id=:u'), {'u':user}))

    def test_rejects_repeatable_read(self):
        with self.engine.connect().execution_options(isolation_level='REPEATABLE READ') as c:
            with c.begin():
                with self.assertRaises(DBAPIError) as error:
                    c.execute(text('INSERT INTO event_registers (event_id,guest_id) VALUES (999999,999999)'))
                self.assertEqual(1644,error.exception.orig.args[0])
                self.assertIn('READ COMMITTED',str(error.exception.orig))

    def test_trigger_migration_preserves_records(self):
        from app.db.database import Base
        def snapshot():
            with self.engine.connect() as c:
                return {table.name: c.execute(table.select().order_by(*table.primary_key.columns)).all()
                        for table in Base.metadata.sorted_tables}
        before = snapshot()
        command.downgrade(self.config, 'mysql_0001')
        command.upgrade(self.config, 'head')
        self.assertEqual(before, snapshot())

    def test_message_gate_migration_and_constraints(self):
        # Start at the deployed pre-change schema with an existing message.
        command.downgrade(self.config, 'mysql_0002')
        with self.engine.begin() as c:
            c.execute(text("INSERT INTO messagedb (topic,message) VALUES ('Legacy test','Keep this message')"))
            message = c.scalar(text('SELECT LAST_INSERT_ID()'))
        command.upgrade(self.config, 'head')
        try:
            from sqlalchemy import inspect
            with self.engine.connect() as c:
                self.assertEqual(('Legacy test', 'Keep this message', None), tuple(c.execute(
                    text('SELECT topic,message,gate_id FROM messagedb WHERE id=:id'), {'id':message}).one()))
                inspector = inspect(c)
                self.assertIn('ix_messagedb_gate_id', [i['name'] for i in inspector.get_indexes('messagedb')])
                c.rollback()
                tx = c.begin()
                try:
                    estates = []
                    gates = []
                    for n in [1, 2]:
                        c.execute(text('INSERT INTO estates (name,location_coordinates) VALUES (:n,:n)'), {'n':f'Message estate {n}'})
                        estates.append(c.scalar(text('SELECT LAST_INSERT_ID()')))
                        c.execute(text("INSERT INTO gates (estate_id,name) VALUES (:e,'Main')"), {'e':estates[-1]})
                        gates.append(c.scalar(text('SELECT LAST_INSERT_ID()')))
                        c.execute(text("INSERT INTO messagedb (gate_id,topic,message) VALUES (:g,'Scoped','Gate alert')"), {'g':gates[-1]})
                    for estate, gate in zip(estates,gates):
                        rows = c.execute(text('SELECT m.gate_id FROM messagedb m JOIN gates g ON g.id=m.gate_id WHERE g.estate_id=:e'), {'e':estate}).scalars().all()
                        self.assertEqual([gate], rows)
                    with self.assertRaises(DBAPIError) as missing:
                        c.execute(text("INSERT INTO messagedb (gate_id,topic,message) VALUES (2000000000,'Bad','Bad gate')"))
                    self.assertEqual(1452, missing.exception.orig.args[0])
                    c.execute(text('UPDATE messagedb SET gate_id=:g WHERE id=:m'), {'g':gates[0],'m':message})
                    c.execute(text('DELETE FROM gates WHERE id=:g'), {'g':gates[0]})
                    self.assertEqual(('Keep this message',None),tuple(c.execute(text('SELECT message,gate_id FROM messagedb WHERE id=:m'), {'m':message}).one()))
                finally:
                    tx.rollback()
            command.downgrade(self.config, 'mysql_0002')
            with self.engine.connect() as c:
                self.assertEqual('Keep this message',c.scalar(text('SELECT message FROM messagedb WHERE id=:m'), {'m':message}))
            command.upgrade(self.config, 'head')
        finally:
            with self.engine.begin() as c:
                c.execute(text('DELETE FROM messagedb WHERE id=:m'), {'m':message})
