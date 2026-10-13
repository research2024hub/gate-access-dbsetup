import os
os.environ.setdefault('DATABASE_URL', 'mysql+pymysql://test:test@127.0.0.1/gate_access_test')
import unittest
from sqlalchemy import create_engine, MetaData, text
from scripts.transfer_ownership import resolve_guest_owners, check_source_relationships, remap_guest
from scripts.transfer_postgres import digest


class OwnershipTests(unittest.TestCase):
    def test_selects_same_estate_not_same_numeric_id(self):
        holders = [{'id': 91, 'user_id': 7, 'estate_id': 1},
                   {'id': 7, 'user_id': 7, 'estate_id': 2}]
        guests = [{'id': 12, 'creator_id': 7, 'estate_id': 1}]
        self.assertEqual({12: 91}, resolve_guest_owners(guests, holders))

    def test_missing_or_ambiguous_owner_is_rejected(self):
        guest = [{'id': 12, 'creator_id': 7, 'estate_id': 1}]
        for holders in [[], [{'id': 91, 'user_id': 7, 'estate_id': 1},
                            {'id': 92, 'user_id': 7, 'estate_id': 1}]]:
            with self.assertRaises(ValueError):
                resolve_guest_owners(guest, holders)

    def test_override_is_validated(self):
        guest = [{'id': 12, 'creator_id': 7, 'estate_id': 1}]
        holders = [{'id': 91, 'user_id': 7, 'estate_id': 1},
                   {'id': 92, 'user_id': 7, 'estate_id': 1},
                   {'id': 93, 'user_id': 8, 'estate_id': 1}]
        self.assertEqual({12: 92}, resolve_guest_owners(guest, holders, {12: 92}))
        for override in [{12: 93}, {12: 999}, {12: 91, 99: 91}]:
            with self.assertRaises(ValueError):
                resolve_guest_owners(guest, holders, override)

    def test_confirmed_holder_interpretation(self):
        guests = [{'id': 179, 'creator_id': 125, 'estate_id': 1},
                  {'id': 180, 'creator_id': 125, 'estate_id': 1}]
        holders = [{'id': 108, 'user_id': 125, 'estate_id': 1},
                   {'id': 125, 'user_id': 149, 'estate_id': 1}]
        self.assertEqual({179: 125, 180: 125}, resolve_guest_owners(
            guests, holders, {179: 125, 180: 125}))
        holders[1]['estate_id'] = 2
        with self.assertRaises(ValueError):
            resolve_guest_owners(guests, holders, {179: 125, 180: 125})

    def test_nullable_owner_and_missing_estate(self):
        guests = [{'id': 1, 'creator_id': None, 'estate_id': None},
                  {'id': 2, 'creator_id': 7, 'estate_id': None}]
        self.assertEqual({1: None, 2: 91}, resolve_guest_owners(
            guests, [{'id': 91, 'user_id': 7, 'estate_id': 1}]))
        with self.assertRaises(ValueError):
            resolve_guest_owners(guests, [{'id': 91, 'user_id': 7, 'estate_id': 1},
                                        {'id': 92, 'user_id': 7, 'estate_id': 2}])

    def test_preflight_and_transformed_checksum(self):
        engine = create_engine('sqlite://')
        with engine.begin() as c:
            for ddl in [
                'CREATE TABLE users (id INTEGER PRIMARY KEY)',
                'CREATE TABLE personal_info (id INTEGER PRIMARY KEY, estate_id INTEGER)',
                'CREATE TABLE account_holders (id INTEGER PRIMARY KEY, user_id INTEGER, personal_info_id INTEGER)',
                'CREATE TABLE guests (id INTEGER PRIMARY KEY, creator_id INTEGER REFERENCES users(id), personal_info_id INTEGER)',
                'CREATE TABLE report_status (id INTEGER PRIMARY KEY, report_id INTEGER)',
                'CREATE TABLE copied_guests (id INTEGER PRIMARY KEY, creator_id INTEGER REFERENCES account_holders(id), personal_info_id INTEGER)',
            ]:
                c.exec_driver_sql(ddl)
            c.exec_driver_sql('INSERT INTO users VALUES (7)')
            c.exec_driver_sql('INSERT INTO personal_info VALUES (3,1)')
            c.exec_driver_sql('INSERT INTO account_holders VALUES (91,7,3)')
            c.exec_driver_sql('INSERT INTO guests VALUES (12,7,3)')
            meta = MetaData()
            meta.reflect(c)
            mapping = check_source_relationships(c, meta)
            self.assertEqual({12: 91}, mapping)
            original = {'id':12, 'creator_id':7, 'personal_info_id':3}
            c.execute(meta.tables['copied_guests'].insert(), remap_guest(original, mapping))
            names = list(original)
            expected = digest(c, meta.tables['guests'], names, lambda row: remap_guest(row, mapping))
            self.assertEqual(expected, digest(c, meta.tables['copied_guests'], names))
            self.assertNotEqual(expected, digest(c, meta.tables['guests'], names))
            self.assertEqual(7, original['creator_id'])
            c.exec_driver_sql('INSERT INTO report_status VALUES (1,5), (2,5)')
            with self.assertRaisesRegex(ValueError, 'multiple rows'):
                check_source_relationships(c, meta)
