class HBaseField:
    field_type = None

    def __init__(self, reverse=False, column_family=None, required=False):
        self.reverse = reverse
        self.column_family = column_family
        self.required = required

    def serialize(self, value):
        value = str(value)
        value = '0' * (16 - len(value)) + value
        if self.reverse:
            value = value[::-1]
        return value

    def deserialize(self, value):
        if self.reverse:
            value = value[::-1]
        return int(value)


class IntegerField(HBaseField):
    field_type = 'int'


class TimestampField(HBaseField):
    field_type = 'timestamp'
