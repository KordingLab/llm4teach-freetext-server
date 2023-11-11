from .PromptStore import PromptStore, PromptID
import pathlib
from typing import Union
from functools import lru_cache


class PlainTextPromptStore(PromptStore):
    extension = ".txt"
    delimiter = "."

    def __init__(self, path: Union[str, pathlib.Path]):
        self._root = pathlib.Path(path)
        self._keys = set()
        self._update_by_traversal()

    def _validate_path(self, path: Union[str, pathlib.Path]) -> pathlib.Path:
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)

        # All paths must be relative OR absolute and in the root directory
        if path.is_absolute() and not path.is_relative_to(self._root):
            raise ValueError(f"Path {path} is not in root {self._root}.")

        # All paths must point to files with the correct extension
        if path.suffix != self.extension:
            raise ValueError(f"File {path} is not a {self.extension} file.")

        # Return the combined root + path
        return self._root.joinpath(path.relative_to(self._root))

    def _relative_path(self, path: Union[str, pathlib.Path]) -> pathlib.Path:
        return self._validate_path(path).relative_to(self._root)

    def _path_to_key(self, path: Union[str, pathlib.Path]) -> PromptID:
        rel_path = self._relative_path(path)
        return self.delimiter.join(rel_path.parts[:-1] + (rel_path.stem,))

    def _key_to_path(self, key: PromptID) -> pathlib.Path:
        parts = key.split(self.delimiter)
        parts[-1] += self.extension
        return self._validate_path(self._root.joinpath(*parts))

    def _add_file(self, path: pathlib.Path):
        path = self._validate_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        self._keys.add(self._path_to_key(path))

    def _add_key(self, key: PromptID):
        self._add_file(self._key_to_path(key))

    def _del_file(self, path: pathlib.Path):
        path = self._validate_path(path)
        path.unlink()
        self._keys.remove(self._path_to_key(path))
        # TODO - more efficient clear that only clears the cache for this key. Can't be done with built-in lru_cache.
        #  See here: https://bugs.python.org/issue28178
        self.get_prompt.cache_clear()

    def _del_key(self, key: PromptID):
        self._del_file(self._key_to_path(key))

    def _update_by_traversal(self):
        for path in self._root.glob("**/*" + self.extension):
            self._add_file(path)

    @lru_cache(maxsize=128)
    def get_prompt(self, prompt_id: PromptID) -> str:
        with self._key_to_path(prompt_id).open("r") as f:
            return f.read()

    def set_prompt(self, prompt_id: PromptID, prompt: str):
        path = self._key_to_path(prompt_id)
        self._add_file(path)
        with path.open("w") as f:
            f.write(prompt)
        # TODO - more efficient clear that only clears the cache for this key. Can't be done with built-in lru_cache.
        #  See here: https://bugs.python.org/issue28178
        self.get_prompt.cache_clear()

    def __delitem__(self, key: PromptID):
        self._del_key(key)

    def get_prompt_ids(self) -> list[PromptID]:
        return list(self._keys)

    def __contains__(self, key: PromptID) -> bool:
        return key in self._keys
