from dateutil import parser
from django.conf import settings
from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class EndlessPagination(BasePagination):
    page_size = 5

    def __init__(self):
        super(EndlessPagination, self).__init__()
        self.has_next_page = False

    def to_html(self):
        pass

    def _pagination_ordered_list(self, request, objects):
        if 'created_at__gt' in request.query_params:
            try:
                created_at__gt = parser.isoparse(request.query_params['created_at__gt'])
            except ValueError:
                created_at__gt = int(request.query_params['created_at__gt'])
            self.has_next_page = False
            return [obj for obj in objects if obj.created_at > created_at__gt]

        idx = 0
        if 'created_at__lt' in request.query_params:
            try:
                created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            except ValueError:
                created_at__lt = int(request.query_params['created_at__lt'])
            for idx, obj in enumerate(objects):
                if obj.created_at < created_at__lt:
                    break

        self.has_next_page = len(objects) > idx + self.page_size
        return objects[idx : idx + self.page_size]

    def paginate_cached_list(self, request, cached_list):
        paginated_list = self._pagination_ordered_list(request, cached_list)
        # if page-up, this will anyway get the newest list
        if 'created_at__gt' in request.query_params:
            return paginated_list
        # if has_next_page, this means this page is fulfill this request
        if self.has_next_page:
            return paginated_list
        # if cache list not fully loaded, means all objects are loaded from DB anyway.
        if len(cached_list) < settings.REDIS_LIST_LENGTH_LIMIT:
            return paginated_list
        # otherwise, cached list is not fulfill the page, need to reload from DB
        return None

    def paginate_queryset(self, queryset, request, view=None):
        if 'created_at__gt' in request.query_params:
            created_at__gt = request.query_params['created_at__gt']
            queryset = queryset.filter(created_at__gt=created_at__gt)
            self.has_next_page = False
            return queryset.order_by('created_at')

        if 'created_at__lt' in request.query_params:
            created_at__lt = request.query_params['created_at__lt']
            queryset = queryset.filter(created_at__lt=created_at__lt)

        queryset = queryset.order_by('-created_at')[:self.page_size + 1]
        self.has_next_page = len(queryset) > self.page_size
        return queryset[:self.page_size]

    def paginate_hbase(self, hbase_model, row_key_prefix, request):
        if 'created_at__gt' in request.query_params:
            created_at__gt = int(request.query_params['created_at__gt'])
            start = (*row_key_prefix, 9999999999999999)
            stop = (*row_key_prefix, created_at__gt)
            objects = hbase_model.filter(start=start, stop=stop, reverse=True)
            if objects and objects[-1].created_at == created_at__gt:
                objects.pop()
            return objects

        if 'created_at__lt' in request.query_params:
            created_at__lt = int(request.query_params['created_at__lt'])
            start = (*row_key_prefix, created_at__lt)
            stop = (*row_key_prefix, )
            objects = hbase_model.filter(start=start, stop=stop, limit=self.page_size + 2, reverse=True)
            if objects and objects[0].created_at == created_at__lt:
                objects.pop(0)
            if len(objects) > self.page_size:
                self.has_next_page = True
                objects.pop()
            else:
                self.has_next_page = False
            return objects

        # if no param, load first page
        prefix = (*row_key_prefix, )
        objects = hbase_model.filter(prefix=prefix, limit=self.page_size + 1, reverse=True)
        if len(objects) > self.page_size:
            self.has_next_page = True
            objects.pop()
        else:
            self.has_next_page = False
        return objects

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data,
        }, status=200)
