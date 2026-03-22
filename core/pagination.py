import logging
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

logger = logging.getLogger("api")


class StandardPagination(PageNumberPagination):
    "global pagination: 10 items per page by default, max 100 per page"

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        "call parent logic then log the result so we can monitor heavy queries"
        result = super().paginate_queryset(queryset, request, view)
        if result is not None:
            logger.info(
                f"[PAGINATION] url={request.get_full_path()} "
                f"page={self.page.number} "
                f"page_size={self.get_page_size(request)} "
                f"total={self.page.paginator.count}"
            )
        return result

    def get_paginated_response(self, data):
        "wrap data in a pagination envelope so the client knows total count and navigation links"
        return Response({
            "pagination": {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page": self.page.number,
                "pages": self.page.paginator.num_pages,
            },
            "results": data,
        })