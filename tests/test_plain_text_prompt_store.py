import unittest
from freetext.prompt_stores.PlainTextPromptStore import PlainTextPromptStore
import tempfile
import shutil
import pathlib


class TestPlainTextPromptStore(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the file storage
        self.test_dir = tempfile.mkdtemp()
        self.store = PlainTextPromptStore(self.test_dir)

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test the initialization of the PlainTextPromptStore."""
        self.assertEqual(self.store._root, pathlib.Path(self.test_dir))
        self.assertIsInstance(self.store._keys, set)
        # Assuming the directory is empty to begin with, keys should be empty
        self.assertEqual(len(self.store._keys), 0)

    def test_path_and_key_conversion(self):
        """Test conversion between paths and keys."""
        p = pathlib.Path(self.test_dir).joinpath("a", "b", "c.txt")
        self.assertEqual(self.store._path_to_key(p), "a.b.c")

    def test_addition_and_deletion_of_files(self):
        """Test adding and deleting files updates keys and filesystem."""
        key, content = "a.b.c", "This is a test prompt."
        self.assertFalse(
            pathlib.Path(self.test_dir).joinpath("a", "b", "c.txt").exists()
        )
        self.store.set_prompt(key, content)
        self.assertTrue(
            pathlib.Path(self.test_dir).joinpath("a", "b", "c.txt").exists()
        )
        self.assertEqual(len(self.store._keys), 1)
        self.assertIn(key, self.store._keys)
        self.assertEqual(self.store.get_prompt(key), content)
        del self.store[key]
        self.assertFalse(
            pathlib.Path(self.test_dir).joinpath("a", "b", "c.txt").exists()
        )
        self.assertEqual(len(self.store._keys), 0)
        self.assertNotIn(key, self.store._keys)
        with self.assertRaises(FileNotFoundError):
            self.store.get_prompt(key)

    def test_get_prompt_ids(self):
        """Test get_prompt_ids method."""
        self.store.set_prompt("a.b.c", "This is a test prompt.")
        self.store.set_prompt("a.b.d", "This is another test prompt.")
        self.assertEqual(len(self.store.get_prompt_ids()), 2)
        self.assertSetEqual(set(self.store.get_prompt_ids()), {"a.b.c", "a.b.d"})

    def test_no_modification_outside_of_root(self):
        with self.assertRaises(ValueError):
            self.store._add_file(pathlib.Path("/not/root/a/b/c.data"))

    def test_init_from_existing_files(self):
        self.assertEqual(len(self.store._keys), 0)
        content = "This is a test prompt, hard-coded."
        path = pathlib.Path(self.test_dir).joinpath("a", "b", "c.txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            f.write(content)

        # Re-initialize store and check that the file was loaded
        self.store = PlainTextPromptStore(self.test_dir)
        self.assertEqual(len(self.store._keys), 1)
        self.assertTrue("a.b.c" in self.store)

    def test_value_error_on_wrong_extension(self):
        with self.assertRaises(ValueError):
            self.store._add_file(
                pathlib.Path(self.test_dir).joinpath("a", "b", "c.data")
            )

    def test_cache_invalidated_on_set(self):
        key, content = "a.b.c", "This is a test prompt."
        self.store.set_prompt(key, content)
        self.assertEqual(self.store.get_prompt(key), content)
        new_content = "This is a new test prompt."
        self.store.set_prompt(key, new_content)
        self.assertEqual(self.store.get_prompt(key), new_content)

    def test_cache_invalidated_on_del(self):
        key, content = "a.b.c", "This is a test prompt."
        self.store.set_prompt(key, content)
        self.assertEqual(self.store.get_prompt(key), content)
        del self.store[key]
        with self.assertRaises(FileNotFoundError):
            self.store.get_prompt(key)


if __name__ == "__main__":
    unittest.main()
