"""RFC 7807 problem+json exception handler.

All errors return application/problem+json with type/title/status/detail/instance/errors.
Per docs/ICD.md conventions.
"""
from rest_framework.response import Response
from rest_framework.views import exception_handler

ERROR_TYPE_BASE = "https://yakimaweb.com/errors"


def problem_detail_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    request = context.get("request")
    status = response.status_code
    title_map = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }

    detail = response.data
    errors: list[dict] | None = None
    if isinstance(detail, dict):
        if "detail" in detail:
            detail_text = str(detail["detail"])
        else:
            errors = []
            for field, msgs in detail.items():
                if isinstance(msgs, list):
                    for m in msgs:
                        errors.append({"field": field, "message": str(m)})
                else:
                    errors.append({"field": field, "message": str(msgs)})
            detail_text = "Validation failed."
    elif isinstance(detail, list):
        detail_text = "; ".join(str(d) for d in detail)
    else:
        detail_text = str(detail)

    body = {
        "type": f"{ERROR_TYPE_BASE}/{status}",
        "title": title_map.get(status, "Error"),
        "status": status,
        "detail": detail_text,
        "instance": request.build_absolute_uri() if request else None,
    }
    if errors:
        body["errors"] = errors

    return Response(body, status=status, content_type="application/problem+json")
