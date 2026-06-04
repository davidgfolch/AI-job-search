from pathlib import Path
from commonlib.terminalColor import yellow, red, cyan


class ContextLoader:
    def __init__(self, cv_path: str, looking_for_path: str):
        self.cv_path = Path(cv_path)
        self.looking_for_path = Path(looking_for_path)
        self._cv_content: str | None = None
        self._looking_for_content: str | None = None
        self._cv_mtime: float = 0
        self._looking_for_mtime: float = 0

    def _read_file(self, path: Path) -> str | None:
        if not path.exists():
            print(red(f"File not found: {path}"))
            return None
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            print(yellow(f"File is empty: {path}"))
            return None
        return content

    def load(self) -> bool:
        cv = self._read_file(self.cv_path)
        if cv is not None:
            self._cv_content = cv
            self._cv_mtime = self.cv_path.stat().st_mtime
            print(cyan(f"CV loaded: {self.cv_path} ({len(cv)} chars)"))
        lf = self._read_file(self.looking_for_path)
        if lf is not None:
            self._looking_for_content = lf
            self._looking_for_mtime = self.looking_for_path.stat().st_mtime
            print(cyan(f"Looking-for loaded: {self.looking_for_path} ({len(lf)} chars)"))
        return self._cv_content is not None or self._looking_for_content is not None

    def reload_if_changed(self):
        if self.cv_path.exists() and self.cv_path.stat().st_mtime != self._cv_mtime:
            cv = self._read_file(self.cv_path)
            if cv is not None:
                self._cv_content = cv
                self._cv_mtime = self.cv_path.stat().st_mtime
                print(cyan(f"CV reloaded ({len(cv)} chars)"))
        if self.looking_for_path.exists() and self.looking_for_path.stat().st_mtime != self._looking_for_mtime:
            lf = self._read_file(self.looking_for_path)
            if lf is not None:
                self._looking_for_content = lf
                self._looking_for_mtime = self.looking_for_path.stat().st_mtime
                print(cyan(f"Looking-for reloaded ({len(lf)} chars)"))

    @property
    def cv_content(self) -> str | None:
        return self._cv_content

    @property
    def looking_for_content(self) -> str | None:
        return self._looking_for_content

    def get_context_text(self) -> str:
        parts = []
        if self._cv_content:
            parts.append(f"<CV>\n{self._cv_content}\n</CV>")
        if self._looking_for_content:
            parts.append(f"<LOOKING_FOR>\n{self._looking_for_content}\n</LOOKING_FOR>")
        return "\n\n".join(parts)
