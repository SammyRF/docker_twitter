from utils.hbase import models


class HBaseFromUser(models.HBaseModel):
    # row key
    from_user_id = models.IntegerField(reverse=True)
    created_at = models.TimestampField()
    # column key
    to_user_id = models.IntegerField(column_family='cf')

    class Meta:
        table_name = 'twitter_from_users'
        row_key = ('from_user_id', 'created_at')


class HBaseToUser(models.HBaseModel):
    # row key
    to_user_id = models.IntegerField(reverse=True)
    created_at = models.TimestampField()
    # column key
    from_user_id = models.IntegerField(column_family='cf')

    class Meta:
        table_name = 'twitter_to_users'
        row_key = ('to_user_id', 'created_at')
