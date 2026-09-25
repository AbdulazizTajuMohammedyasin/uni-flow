from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Default list pagination: `?page=` and `?page_size=` (20 by default, at most 100).

    Response shape: {"count": ..., "next": ..., "previous": ..., "results": [...]}.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
