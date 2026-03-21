from rest_framework.response import Response
from rest_framework import status as drf_status


def success_response(message: str = "Success", data=None, status_code: int = drf_status.HTTP_200_OK) -> Response:
    payload = {"message": message, "status": status_code}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status_code)


def created_response(message: str = "Created successfully", data=None) -> Response:
    payload = {"message": message, "status": drf_status.HTTP_201_CREATED}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=drf_status.HTTP_201_CREATED)


def error_response(
    error,
    message: str = "Validation failed",
    status_code: int = drf_status.HTTP_400_BAD_REQUEST,
) -> Response:
    return Response(
        {"error": error, "message": message, "status": status_code},
        status=status_code,
    )


def not_found_response(message: str = "Not found") -> Response:
    return Response(
        {"error": message, "message": message, "status": drf_status.HTTP_404_NOT_FOUND},
        status=drf_status.HTTP_404_NOT_FOUND,
    )


def forbidden_response(message: str = "Permission denied") -> Response:
    return Response(
        {"error": message, "message": message, "status": drf_status.HTTP_403_FORBIDDEN},
        status=drf_status.HTTP_403_FORBIDDEN,
    )


def server_error_response(message: str = "Something went wrong.") -> Response:
    return Response(
        {"error": message, "message": message, "status": drf_status.HTTP_500_INTERNAL_SERVER_ERROR},
        status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
    )