import datetime
import logging

import peewee


_logger = logging.getLogger(__name__)


database = peewee.SqliteDatabase(None)


def init(db_path):
    database.init(db_path)
    database.create_tables([Story], safe=True)


def _yesterday():
    return datetime.date.today() - datetime.timedelta(days=1)


def _today():
    return datetime.date.today()


class BaseModel(peewee.Model):
    class Meta:
        database = database


class Story(BaseModel):
    hn_id = peewee.BigIntegerField(primary_key=True)
    next_post = peewee.DateField(default=_yesterday)
    first_saw = peewee.DateField(default=_today)
    last_saw = peewee.DateField(default=_today)
    times = peewee.IntegerField(default=1)
    position = peewee.IntegerField(default=0)
