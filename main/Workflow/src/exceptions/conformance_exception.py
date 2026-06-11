from framework.conformance import render_conformance_check_result


class Conformance_Exception(Exception):
    def __init__(self, message: list[str]) -> None:
        super().__init__(message)

    def render(self):
        render_conformance_check_result(self.args[0])