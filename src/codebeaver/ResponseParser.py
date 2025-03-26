import re

class ResponseParser:
    @staticmethod
    def parse(response: str) -> str:
        test_regex_match = re.findall(r"<test>\s*\[test\](.*?)</test>", response, re.DOTALL)
        test_content = test_regex_match[0] if test_regex_match else ""
        test_content = test_content.strip()
        return test_content
