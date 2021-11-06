from django.conf import settings
import happybase


class HBaseClient:
    conn = None

    @classmethod
    def get_connection(cls):
        if not cls.conn:
            cls.conn = happybase.Connection(settings.HBASE_HOST)
        return cls.conn

    @classmethod
    def clear(cls):
        from utils.hbase.models import HBaseModel
        for hbase_model in HBaseModel.__subclasses__():
            hbase_model.delete_table()
            hbase_model.create_table()
