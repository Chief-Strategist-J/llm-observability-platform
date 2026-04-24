from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    def __init__(self, field: str, message: str, fix_suggestion: str):
        self.field = field
        self.message = message
        self.fix_suggestion = fix_suggestion
        super().__init__(f"{field}: {message}. {fix_suggestion}")


class Preconditions:
    @staticmethod
    def validate_non_empty_string(value: Any, field_name: str) -> None:
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(
                field=field_name,
                message=f"{field_name} cannot be empty",
                fix_suggestion=f"Provide a non-empty {field_name}"
            )

    @staticmethod
    def validate_non_negative(value: int, field_name: str) -> None:
        if value < 0:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} must be non-negative",
                fix_suggestion=f"Provide a {field_name} >= 0"
            )

    @staticmethod
    def validate_positive(value: int, field_name: str) -> None:
        if value <= 0:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} must be positive",
                fix_suggestion=f"Provide a {field_name} > 0"
            )

    @staticmethod
    def validate_range(value: int, field_name: str, min_val: int, max_val: int) -> None:
        if value < min_val or value > max_val:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} must be between {min_val} and {max_val}",
                fix_suggestion=f"Provide a {field_name} in range [{min_val}, {max_val}]"
            )

    @staticmethod
    def validate_not_none(value: Any, field_name: str) -> None:
        if value is None:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} cannot be None",
                fix_suggestion=f"Provide a valid {field_name}"
            )

    @staticmethod
    def validate_not_empty_list(value: List, field_name: str) -> None:
        if not value or len(value) == 0:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} cannot be empty",
                fix_suggestion=f"Provide a non-empty {field_name}"
            )

    @staticmethod
    def validate_list_size(items: List, field_name: str, min_size: int = 0, max_size: int = 1000) -> None:
        if items is None:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} cannot be None",
                fix_suggestion=f"Provide a valid {field_name}"
            )
        if len(items) < min_size:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} must contain at least {min_size} item(s)",
                fix_suggestion=f"Provide at least {min_size} item(s) in {field_name}"
            )
        if len(items) > max_size:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} must contain at most {max_size} item(s)",
                fix_suggestion=f"Provide at most {max_size} item(s) in {field_name}"
            )

    @staticmethod
    def validate_enum(value: str, field_name: str, valid_values: List[str]) -> None:
        if value not in valid_values:
            raise ValidationError(
                field=field_name,
                message=f"Invalid {field_name}: '{value}'",
                fix_suggestion=f"Valid values are: {', '.join(valid_values)}"
            )

    @staticmethod
    def validate_not_empty_list(items: List, field_name: str) -> None:
        if not items or len(items) == 0:
            raise ValidationError(
                field=field_name,
                message=f"{field_name} cannot be empty",
                fix_suggestion=f"Provide at least one item in {field_name}"
            )


class Postconditions:
    @staticmethod
    def validate_not_none(result: Any, operation: str) -> None:
        if result is None:
            raise ValidationError(
                field="result",
                message=f"{operation} returned None",
                fix_suggestion=f"Check if the operation was successful and the resource exists"
            )

    @staticmethod
    def validate_success(result: bool, operation: str) -> None:
        if not result:
            raise ValidationError(
                field="result",
                message=f"{operation} failed",
                fix_suggestion=f"Check the operation parameters and resource state"
            )

    @staticmethod
    def validate_not_empty_list(result: List, operation: str) -> None:
        if not result:
            raise ValidationError(
                field="result",
                message=f"{operation} returned empty list",
                fix_suggestion=f"Check if resources exist for the given query"
            )
