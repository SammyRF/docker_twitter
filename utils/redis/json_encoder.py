from django.core.serializers.json import DjangoJSONEncoder
import datetime

class JSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            # 唯一修改的地方，保留 mirco second 增加时间精度
            # if o.microsecond:
            #     r = r[:23] + r[26:]
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        else:
            return DjangoJSONEncoder.default(o)

