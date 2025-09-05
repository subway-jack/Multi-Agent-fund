import sys
import os
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning:PyPDF2")

# Adjust sys.path to include the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

from src.file_system.fileSystem import FileSystem, FileSystemError
@pytest.fixture
def filesystem(tmp_path):
    fs = FileSystem(root=tmp_path)
    yield fs
    # Cleanup if necessary


def test_save_file_text(filesystem):
    file_path = 'test.txt'
    content = 'Hello, world!'
    assert filesystem.save_file(file_path, content)
    assert (filesystem.root / file_path).exists()
    reg = filesystem._read_registry()
    assert file_path in reg
    assert not reg[file_path]['has_text']

def test_save_file_structured(filesystem):
    file_path = 'test.json'
    content = {"key": "value"}  # Change to dict
    assert filesystem.save_file(file_path, content)
    assert (filesystem.root / file_path).exists()
    reg = filesystem._read_registry()
    assert file_path in reg
    assert not reg[file_path]['has_text']

def test_read_file_structured(filesystem):
    file_path = 'test.json'
    content = {"key": "value"}
    filesystem.save_file(file_path, content)
    result = filesystem.read_file(file_path)
    assert 'key: value' in result['content']

def test_save_file_binary(filesystem):
    file_path = 'test.bin'
    content = b'\x00\x01\x02'
    assert filesystem.save_file(file_path, content)
    assert (filesystem.root / file_path).exists()
    desc_path = f'{file_path}.description.txt'
    assert (filesystem.root / desc_path).exists()
    reg = filesystem._read_registry()
    assert file_path in reg
    assert reg[file_path]['has_text']
    assert reg[file_path]['text_path'] == desc_path

def test_read_file_text(filesystem):
    file_path = 'test.txt'
    content = 'Hello, world!'
    filesystem.save_file(file_path, content)
    result = filesystem.read_file(file_path)
    assert result['content'] == content

def test_read_file_structured(filesystem):
    file_path = 'test.json'
    content = '{"key": "value"}'
    filesystem.save_file(file_path, content)
    result = filesystem.read_file(file_path)
    assert 'key: value' in result['content']  # Adjust if necessary based on actual format

def test_read_file_binary(filesystem):
    file_path = 'test.bin'
    content = b'\x00\x01\x02'
    filesystem.save_file(file_path, content)
    result = filesystem.read_file(file_path)
    assert result['content'] == 'AAEC'  # Adjust to match actual base64

def test_list_files(filesystem):
    filesystem.save_file('test1.txt', 'content1')
    filesystem.save_file('test2.json', '{"key": "value"}')
    files = filesystem.list_files()
    assert 'test1.txt' in files
    assert 'test2.json' in files
    assert len(files) == 2

def test_delete_file(filesystem):
    file_path = 'test.txt'
    filesystem.save_file(file_path, 'content')
    assert filesystem.delete_file(file_path)
    assert not (filesystem.root / file_path).exists()
    reg = filesystem._read_registry()
    assert file_path not in reg

def test_delete_nonexistent_file(filesystem):
    assert not filesystem.delete_file('nonexistent.txt')