from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException
from django.core.paginator import Paginator, EmptyPage
from response_codes import ResponseCodes
import traceback


class CustomAPIException(APIException):
    def __init__(self, detail=None, error_code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        self.error_code = error_code or ResponseCodes.ERROR
        self.detail = detail

    def get_full_details(self):
        return {
            "status": self.status_code,
            "response_code": "request_error",
            "success": False,
            "data": None,
            "error": self.detail,
            "error_code": self.error_code
        }


class NotfoundError(CustomAPIException):
    pass


class RequestError(CustomAPIException):
    pass


class InternalError(CustomAPIException):
    pass


class UtilsResponse:
    @staticmethod
    def success(data, status=status.HTTP_200_OK, request=None):
        response = {
            "response_code": ResponseCodes.SUCCESS,
            "success": True,
            "data": data,
            "error_code": None,
            "error": False,
            "status": status,
        }
        if request:
            page_data = {
                "page": request.query_params.get("page", "1"),
                "page_size": request.query_params.get("page_size", "20")
            }
            for key, value in page_data.items():
                if not value.isnumeric():
                    return UtilsResponse.request_error(data=f"Invalid {key}, must be numeric'")

            page = int(page_data["page"])
            page_size = int(page_data["page_size"])

            total_count = request.count if hasattr(request, "count") else len(data)

            total_pages = (total_count // page_size) + (1 if total_count % page_size else 0)

            paginator = Paginator(data, page_size)
            try:
                info = paginator.page(page)
            except EmptyPage:
                info = paginator.page(paginator.num_pages)
            except ZeroDivisionError:
                return UtilsResponse.request_error(data=f"page cannot be zero.")

            data = {
                "page_details": {
                    "count": total_count,
                    "total_page": total_pages,
                    "current_page": page,
                    "entries_in_this_page": len(info),
                    "has_previous_page": page > 1,
                    "has_next_page": page < total_pages,
                },
                "data": list(info)
            }
            response["data"] = data
        return Response(response, status=status, headers={'Access-Control-Allow-Origin': '*'})

    @staticmethod
    def created(status=status.HTTP_201_CREATED):
        response = {
            "response_code": ResponseCodes.SUCCESS,
            "success": True,
            "error_code": None,
            "error": False,
            "status": status,
        }
        return Response(response, status=status, headers={'Access-Control-Allow-Origin': '*'})

    @staticmethod
    def no_content(status=status.HTTP_204_NO_CONTENT):
        return Response(status=status, headers={'Access-Control-Allow-Origin': '*'})

    @staticmethod
    def notfound_error(data, status_code=status.HTTP_404_NOT_FOUND, error_code=ResponseCodes.ERROR):
        raise NotfoundError(detail=data, error_code=error_code, status_code=status_code)

    @staticmethod
    def request_error(data, status_code=status.HTTP_400_BAD_REQUEST, error_code=ResponseCodes.ERROR):
        if isinstance(data, ResponseCodes):
            data, error_code = data.value, data.name
        raise RequestError(detail=data, error_code=error_code, status_code=status_code)

    @staticmethod
    def internal_error(data, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error_code=ResponseCodes.ERROR):
        print("--------------------------------------------")
        print(traceback.format_exc())
        print("--------------------------------------------")
        raise InternalError(detail=data, error_code=error_code, status_code=status_code)
