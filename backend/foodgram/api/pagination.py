from rest_framework.pagination import PageNumberPagination


class PageCustPagination(PageNumberPagination):
    page_size_query_param = 'limit'