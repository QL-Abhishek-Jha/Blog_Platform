import logging
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

logger = logging.getLogger("api")


class StandardPagination(PageNumberPagination):
    page_size             = 10
    page_size_query_param = "page_size"
    max_page_size         = 100

    def paginate_queryset(self, queryset, request, view=None):
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
        return Response({
            "pagination": {
                "count":    self.page.paginator.count,
                "next":     self.get_next_link(),
                "previous": self.get_previous_link(),
                "page":     self.page.number,
                "pages":    self.page.paginator.num_pages,
            },
            "results": data,
        })