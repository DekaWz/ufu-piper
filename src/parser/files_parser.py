from pathlib import Path

PATH_STATIC = Path(__file__).resolve().parent.parent / "files"

def get_files(files_path: str = PATH_STATIC) -> list:
    return [str(p) for p in files_path.rglob("*") if p.is_file()]

class Parser():
    def __init__():
        pass

    def is_pdf(self, file: str) -> bool:
        return file.endswith(".pdf")

    def is_djvu(self, file: str) -> bool:
        return file.endswith(".djvu")

    