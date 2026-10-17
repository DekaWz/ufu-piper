
from pathlib import Path
import hashlib

from files_parser import get_files
from pdf_parser import PdfParser
from djvu_parser import DjvuParser


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILES_PATH = PROJECT_ROOT / "data" / "files"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

PDF_OUT_PATH = PROCESSED_PATH / "pdf"
DJVU_OUT_PATH = PROCESSED_PATH / "djvu"


class Writer(DjvuParser, PdfParser):
    def __init__(self, files_path=None):
        if files_path is None:
            files_path = DATA_FILES_PATH

        self.files = get_files(files_path)

    def _get_output_path(self, file_path: str, output_dir: Path) -> Path:
        source = Path(file_path).resolve()

        try:
            relative = source.relative_to(DATA_FILES_PATH.resolve())
            identity = relative.as_posix()
        except ValueError:
            identity = str(source)

        suffix = hashlib.sha256(
            identity.encode("utf-8")
        ).hexdigest()[:12]

        return output_dir / f"{source.stem}__{suffix}.txt"

    def write_all_textes(self) -> int:
        written = 0

        PDF_OUT_PATH.mkdir(parents=True, exist_ok=True)
        DJVU_OUT_PATH.mkdir(parents=True, exist_ok=True)

        for file_path in self.files:
            try:
                if self.is_pdf(file_path):
                    output_dir = PDF_OUT_PATH
                    extract = self.get_pdf_text

                elif self.is_djvu(file_path):
                    output_dir = DJVU_OUT_PATH
                    extract = self.get_djvu_text

                else:
                    continue

                out_file = self._get_output_path(
                    file_path, output_dir
                )

                if out_file.exists():
                    continue

                text = extract(file_path)

                if not text or not text.strip():
                    print(f"Пустой текст: {file_path}")
                    continue

                tmp_file = out_file.with_suffix(".txt.tmp")

                try:
                    tmp_file.write_text(text, encoding="utf-8")
                    tmp_file.replace(out_file)
                finally:
                    tmp_file.unlink(missing_ok=True)

                written += 1
                print(f"[OK] {file_path} -> {out_file}")

            except Exception as e:
                print(f"[ERROR] {file_path}: {e}")

        return written


if __name__ == "__main__":
    writer = Writer()

    print(f"Всего файлов: {len(writer.files)}")
    print(f"Обработано новых файлов: {writer.write_all_textes()}")
