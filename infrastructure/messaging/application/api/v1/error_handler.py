from typing import Optional
from fastapi import HTTPException, status


def raise_validation_error(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail
    )


def raise_not_found_error(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )


def raise_conflict_error(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail
    )


def raise_too_many_requests_error(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=detail
    )


def raise_internal_error(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail
    )
