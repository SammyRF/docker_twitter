from django.core import serializers
from utils.hbase.models import HBaseModel
from utils.redis.json_encoder import JSONEncoder
import json


class DjangoModelSerializer:
    @classmethod
    def serialize(cls, instance):
        return serializers.serialize('json', [instance], cls=JSONEncoder)

    @classmethod
    def deserialize(cls, serialized_data):
        return list(serializers.deserialize('json', serialized_data))[0].object


class HBaseModelSerializer:
    @classmethod
    def _get_model_class(cls, model_class_name):
        for subclass in HBaseModel.__subclasses__():
            if subclass.__name__ == model_class_name:
                return subclass
        raise Exception(f'HBase "{model_class_name}" not found.')

    @classmethod
    def serialize(cls, instance):
        json_data = {'model_class_name': instance.__class__.__name__}
        for key in instance.get_field_hash():
            json_data[key] = getattr(instance, key)
        return json.dumps(json_data)

    @classmethod
    def deserialize(cls, serialized_data):
        json_data = json.loads(serialized_data)
        model_class = cls._get_model_class(json_data.pop('model_class_name'))
        return model_class(**json_data)

