import json
import os
import unittest
from datetime import date, datetime, time, timedelta, timezone

os.environ.setdefault('DATABASE_URL', 'mysql+pymysql://test:test@127.0.0.1/gate_access_test')

from sqlalchemy.dialects.mysql import TIME
from sqlalchemy.dialects.mysql.pymysql import dialect
from scripts.transfer_postgres import canonical


class TemporalChecksumTests(unittest.TestCase):
    def test_postgres_time_matches_mysql_processed_time(self):
        process = TIME().result_processor(dialect(), None)
        for original in (time(0), time(8, 30), time(23, 59, 59, 123456)):
            mysql_value = process(timedelta(hours=original.hour, minutes=original.minute,
                                           seconds=original.second, microseconds=original.microsecond))
            self.assertEqual(canonical(original), canonical(mysql_value))
            json.dumps(canonical([original, mysql_value]))

    def test_date_and_utc_datetime_remain_distinct(self):
        self.assertEqual('2026-09-29', canonical(date(2026, 9, 29)))
        aware = datetime(2026, 9, 29, 10, tzinfo=timezone(timedelta(hours=2)))
        self.assertEqual('2026-09-29T08:00:00.000000', canonical(aware))
        self.assertEqual(canonical(aware), canonical(datetime(2026, 9, 29, 8)))
