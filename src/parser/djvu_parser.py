from pathlib import Path
from typing import Union

from files_parser import Parser

import subprocess


class DjvuParser(Parser):
    def __init__(self):
        pass

    def get_djvu_text(self, file_name):
        result = subprocess.run(
            ["djvutxt", file_name], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            encoding="utf-8"
        )
        return result.stdout


if __name__ == "__main__":
    pass