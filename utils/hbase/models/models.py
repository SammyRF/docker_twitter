from django.conf import settings
from utils.hbase.hbase_client import HBaseClient
from utils.hbase.models import HBaseField
from utils.hbase.models.exceptions import EmptyColumnError, BadRowKeyError


# example
# 1. HBaseModel.create(from_user_id=1, to_user_id=2, created_at=ts)
# 2. instance = HBaseModel(from_user_id=1, to_user_id=2, created_at=ts)
#    instance.save()
# 3. instance.from_user_id = 1
#    instance.save()
class HBaseModel:
    def __init__(self, **kwargs):
        for field, _ in self.get_field_hash().items():
            setattr(self, field, kwargs.get(field))

    def save(self):
        if len(self.row_data) == 0:
            raise EmptyColumnError()
        table = self.get_table()
        table.put(self.row_key, self.row_data)

    class Meta:
        table_name = None
        row_key = ()

    @property
    def row_key(self):
        return self.serialize_row_key(self.__dict__)

    # alias for row_key used by model
    @property
    def id(self):
        return self.row_key

    @property
    def row_data(self):
        return self.serialize_row_data(self.__dict__)

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance

    @classmethod
    def bulk_create(cls, bulk_data):
        table = cls.get_table()
        batch = table.batch()
        instances = []
        for data in bulk_data:
            instance = cls(**data)
            instances.append(instance)
            batch.put(instance.row_key, instance.row_data)
        batch.send()
        return instances

    @classmethod
    def delete(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs)
        table = cls.get_table()
        return table.delete(row_key)

    @classmethod
    def get(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs)
        table = cls.get_table()
        row_data = table.row(row_key)
        return cls.deserialize_row_data(row_key, row_data)

    @classmethod
    def get_table(cls):
        conn = HBaseClient.get_connection()
        return conn.table(cls.get_table_name())

    @classmethod
    def get_field_hash(cls):
        field_hash = {}
        for key, obj in cls.__dict__.items():
            if isinstance(obj, HBaseField):
                field_hash[key] = obj
        return field_hash

    @classmethod
    def serialize_row_key(cls, data, is_prefix=False):
        """
        serialize dict to bytes (not str)
        {key1: val1} => b"val1"
        {key1: val1, key2: val2} => b"val1:val2"
        {key1: val1, key2: val2, key3: val3} => b"val1:val2:val3"
        """
        fields = cls.get_field_hash()
        values = []
        for key, field in fields.items():
            if field.column_family: # column_family means column key
                continue
            value = data.get(key)
            if value is None:
                if not is_prefix:
                    raise BadRowKeyError(f'{key} is missing in row key')
                break
            value = field.serialize(value)
            if ':' in value:
                raise BadRowKeyError(f'{key} should not contain ":" in value {value}')
            values.append(value)
        return bytes(':'.join(values), encoding='utf-8')

    @classmethod
    def deserialize_row_key(cls, row_key):
        """
        "val1" => {'key1': val1, 'key2': None, 'key3': None}
        "val1:val2" => {'key1': val1, 'key2': val2, 'key3': None}
        "val1:val2:val3" => {'key1': val1, 'key2': val2, 'key3': val3}
        """
        if isinstance(row_key, bytes):
            row_key = row_key.decode('utf-8')
        values = row_key.split(':')
        data = {}
        fields = cls.get_field_hash()
        for i in range(len(values)):
            key = cls.Meta.row_key[i]
            value = fields[key].deserialize(values[i])
            data[key] = value
        return data

    @classmethod
    def serialize_row_key_from_tuple(cls, row_key_tuple):
        if not row_key_tuple:
            return None
        data = {
            key: value
            for key, value in zip(cls.Meta.row_key, row_key_tuple)
        }
        return cls.serialize_row_key(data, is_prefix=True)

    @classmethod
    def serialize_row_data(cls, data):
        row_data = {}
        field_hash = cls.get_field_hash()
        for key, field in field_hash.items():
            if not field.column_family:
                continue
            column_key = f'{field.column_family}:{key}'
            column_value = data.get(key)
            if column_value is None:
                continue
            row_data[column_key] = field.serialize(column_value)
        return row_data

    @classmethod
    def deserialize_row_data(cls, row_key, row_data):
        if not row_data:
            return None
        data = cls.deserialize_row_key(row_key)
        fields = cls.get_field_hash()
        for column_key, column_value in row_data.items():
            column_key = column_key.decode('utf-8')
            # remove column family
            key = column_key[column_key.index(':') + 1:]
            data[key] = fields[key].deserialize(column_value)
        return cls(**data)

    @classmethod
    def get_table_name(cls):
        if not cls.Meta.table_name:
            raise NotImplementedError('Missing table_name in meta class')
        if settings.TESTING:
            return f'testing_{cls.Meta.table_name}'
        return cls.Meta.table_name

    @classmethod
    def create_table(cls):
        conn = HBaseClient.get_connection()
        tables = [table.decode('utf_8') for table in conn.tables()]
        # check if table exists already
        if cls.get_table_name() in tables:
            return
        column_families = {
            field.column_family : dict()
            for key, field in cls.get_field_hash().items()
            if field.column_family is not None
        }
        conn.create_table(cls.get_table_name(), column_families)

    @classmethod
    def delete_table(cls):
        conn = HBaseClient.get_connection()
        tables = [table.decode('utf_8') for table in conn.tables()]
        if not cls.get_table_name() in tables:
            return
        conn.delete_table(cls.get_table_name(), True)

    @classmethod
    def filter(cls, start=None, stop=None, prefix=None, limit=None, reverse=False):
        row_start = cls.serialize_row_key_from_tuple(start)
        row_stop = cls.serialize_row_key_from_tuple(stop)
        row_prefix = cls.serialize_row_key_from_tuple(prefix)

        # scan table with conditions
        rows = cls.get_table().scan(
            row_start=row_start,
            row_stop=row_stop,
            row_prefix=row_prefix,
            limit=limit,
            reverse=reverse
        )

        # deserialize
        return [
            cls.deserialize_row_data(row_key, row_data)
            for row_key, row_data in rows
        ]

