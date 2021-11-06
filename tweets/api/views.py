from newsfeeds.services import NewsFeedService
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from tweets.api.serializers import TweetSerializer, TweetSerializerForCreate, TweetSerializerForDetails
from tweets.models import Tweet
from tweets.services import TweetService
from utils import helpers
from utils.decorators import required_all_params, rate_limit
from utils.paginations import EndlessPagination



class TweetViewSet(viewsets.GenericViewSet):
    queryset = Tweet.objects.all()
    serializer_class = TweetSerializerForCreate
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]

    @required_all_params(method='GET', params=('user_id',))
    @rate_limit(hms=(0, 6, 0))
    def list(self, request):
        # get cached tweets from redis first, even cache hit not means the cached tweets fulfill the page.
        # reason is we introduce the list size limit in redis. In such case it return None and go DB search again.
        # The cached objects will be kept no change, because it always cached objects from newest.
        cached_tweets = TweetService.get_tweets_in_redis(request.query_params['user_id'])
        page = self.paginator.paginate_cached_list(request, cached_tweets)
        if page is None:
            queryset = Tweet.objects.filter(user_id=request.query_params['user_id']).order_by('-created_at')
            page = self.paginate_queryset(queryset)
        serializer = TweetSerializer(page, context={'user': request.user}, many=True)
        return self.get_paginated_response(serializer.data)

    @rate_limit(hms=(0, 6, 0))
    def create(self, request, *args, **kwargs):
        serializer = TweetSerializerForCreate(data=request.data, context={'user': request.user})
        if not serializer.is_valid():
            return helpers.validation_errors_response(serializer.errors)

        tweet = serializer.save()
        NewsFeedService.fan_out(tweet=tweet)
        return Response(TweetSerializer(tweet, context={'user': request.user}).data, status=status.HTTP_201_CREATED)

    @rate_limit(hms=(0, 6, 0))
    def retrieve(self, request, pk):
        tweet = Tweet.objects.filter(id=pk).first()
        if tweet:
            return Response(TweetSerializerForDetails(tweet, context={'user': request.user}).data, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'tweet not exists',
            }, status=status.HTTP_404_NOT_FOUND)

