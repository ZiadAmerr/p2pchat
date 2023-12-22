class BaseResponse:
    def __init__(self, success_codes, failure_codes):
        self.success_codes = success_codes
        self.failure_codes = failure_codes
        self.all_codes = {**self.success_codes, **self.failure_codes}

    def get_code(self, str_code: str) -> int:
        return next(
            (
                code
                for code, (str_code_, _) in self.all_codes.items()
                if str_code_ == str_code
            ),
            -1,
        )

    def render_code(self, str_code: str) -> str:
        code = self.get_code(str_code)
        alias, description = self.all_codes[code]
        return f"{code} {alias} when {description.lower()}"

    def _response(self, code: int, message: str, is_success: bool, data=None):
        return self.__class__(code, message, is_success, data)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "is_success": self.is_success,
            "data": self.data,
        }

    @classmethod
    def init_from_dict(cls, data: dict):
        return cls(data["code"], data["message"], data["is_success"], data["data"])
