from time import time

class ReportTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time()
        response = self.get_response(request)
        end_time = time()
        # print(end_time - start_time)
        return response