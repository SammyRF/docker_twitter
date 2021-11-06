from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.hbase_models import HBaseNewsFeed
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.decorators import rate_limit
from utils.gatekeeper.models import GateKeeper
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    @rate_limit(hms=(0, 6, 0))
    def list(self, request):
        cached_newsfeeds = NewsFeedService.get_newsfeeds_in_redis(request.user.id)
        page = self.paginator.paginate_cached_list(request, cached_newsfeeds)
        if page is None:
            if not GateKeeper.is_switch_on('switch_newsfeed_to_hbase'):
                # pagination in mysql
                queryset = NewsFeed.objects.filter(user=request.user).order_by('-created_at')
                page = self.paginate_queryset(queryset)
            else:
                # pagination in hbase
                page = self.paginator.paginate_hbase(HBaseNewsFeed, (request.user.id, ), request)
        serializer = NewsFeedSerializer(
            page,
            context={'user': request.user},
            many=True,
        )
        return self.get_paginated_response(serializer.data)
