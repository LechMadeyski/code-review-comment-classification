import zlib
from hashlib import sha3_256
from pathlib import Path

_DIR = Path(__file__).parent.resolve() / "__apicache__"


class ApiCache:
    def __init__(self) -> None:
        self._hits = 0
        self._misses = 0

    def get(self, url: str) -> str | None:
        try:
            with open(_DIR / ApiCache._filename(url), "rb") as f:
                data = f.read()
                self._hits += 1
                return zlib.decompress(data).decode("utf-8")
        except:
            self._misses += 1
            return None

    def set(self, url: str, content: str) -> None:
        try:
            data = zlib.compress(content.encode("utf-8"))
            _DIR.mkdir(exist_ok=True)
            with open(_DIR / ApiCache._filename(url), "wb") as f:
                f.write(data)
        except:
            pass  # the cache's only purpose is to speed up performance, so we can ignore any errors

    @property
    def hit_ratio(self) -> float:
        accesses = self._hits + self._misses
        return self._hits / accesses if accesses > 0 else 0

    @staticmethod
    def _filename(url: str) -> str:
        return sha3_256(url.encode("utf-8")).hexdigest()
