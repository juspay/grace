
from pathlib import Path


class FileManager:
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(__file__).parent.parent.parent.parent / Path(base_path) # to root of grace
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def update_base_path(self, new_base_path: str) -> None:
        self.base_path = Path(__file__).parent.parent.parent.parent / Path(new_base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def list_files(self, extension: str = ".md") -> list[Path]:
        return list(self.base_path.rglob(f"*{extension}"))

    def read_file(self, file_path: Path) -> str:
        if self.check_file_exists(file_path):
            with open(self.base_path / file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def write_file(self, file_path: Path, content: str) -> None:
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def save_tech_spec(self, content: str,  filename: str = "tech_spec.md") -> Path:
        self.write_file(Path("specs") / Path(filename), content)
        return self.base_path / Path(filename)
    
    def check_file_exists(self, filename: str) -> bool:
        file_path = self.base_path / filename
        return file_path.exists()