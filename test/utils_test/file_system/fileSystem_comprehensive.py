import sys
import os
import pytest
import tempfile
import threading
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Union


from src.utils.fileSystem import FileSystem, FileSystemError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def filesystem(temp_dir):
    """Create a FileSystem instance with temporary directory."""
    fs = FileSystem(root=temp_dir)
    yield fs


class TestBasicOperations:
    """测试基础文件操作功能"""
    
    def test_save_and_read_text_file(self, filesystem):
        """测试保存和读取文本文件"""
        content = "Hello, World!\nThis is a test file."
        assert filesystem.save_file('test.txt', content)
        
        result = filesystem.read_file('test.txt')
        assert result['content'] == content
        assert result['metadata']['mime'] == 'text/plain'
        assert result['metadata']['size'] > 0

    def test_save_and_read_json_file(self, filesystem):
        """测试保存和读取JSON文件"""
        data = {"name": "test", "value": 123, "nested": {"key": "value"}}
        assert filesystem.save_file('data.json', data)
        
        result = filesystem.read_file('data.json')
        assert '"name": "test"' in result['content']
        assert '"value": 123' in result['content']
        assert result['metadata']['mime'] == 'application/json'

    def test_save_and_read_binary_file(self, filesystem):
        """测试保存和读取二进制文件"""
        binary_data = b'\x00\x01\x02\x03\xFF\xFE\xFD'
        assert filesystem.save_file('data.bin', binary_data)
        
        result = filesystem.read_file('data.bin')
        assert result['content'] == 'AAECA//+/Q=='
        assert result['metadata']['mime'] == 'application/octet-stream'
        assert result['metadata']['has_text'] == True

    def test_save_empty_file(self, filesystem):
        """测试保存空文件"""
        assert filesystem.save_file('empty.txt', '')
        result = filesystem.read_file('empty.txt')
        assert result['content'] == ''
        assert result['metadata']['size'] == 0

    def test_save_none_content(self, filesystem):
        """测试保存None内容"""
        assert filesystem.save_file('none.txt', None)
        result = filesystem.read_file('none.txt')
        assert result['content'] == ''


class TestListFiles:
    """测试文件列表功能"""
    
    def test_list_empty_filesystem(self, filesystem):
        """测试空文件系统列表"""
        files = filesystem.list_files()
        assert len(files) == 0

    def test_list_multiple_files(self, filesystem):
        """测试列出多个文件"""
        filesystem.save_file('file1.txt', 'content1')
        filesystem.save_file('file2.json', {'key': 'value'})
        filesystem.save_file('file3.bin', b'binary')
        
        files = filesystem.list_files()
        assert len(files) == 3
        assert 'file1.txt' in files
        assert 'file2.json' in files
        assert 'file3.bin' in files

    def test_list_with_metadata(self, filesystem):
        """测试带元数据的文件列表"""
        filesystem.save_file('test.txt', 'content')
        files = filesystem.list_files(with_meta=True)
        assert len(files) == 1
        assert files[0]['file_path'] == 'test.txt'
        assert 'size' in files[0]
        assert 'mime' in files[0]

    def test_ignore_patterns(self, temp_dir):
        """测试忽略模式"""
        fs = FileSystem(root=temp_dir, ignore_patterns=['*.tmp', 'temp*'])
        fs.save_file('normal.txt', 'content')
        fs.save_file('temp.txt', 'content')
        fs.save_file('file.tmp', 'content')
        
        files = fs.list_files()
        assert len(files) == 1
        assert 'normal.txt' in files
        assert 'temp.txt' not in files
        assert 'file.tmp' not in files


class TestDeleteOperations:
    """测试删除操作"""
    
    def test_delete_existing_file(self, filesystem):
        """测试删除存在的文件"""
        filesystem.save_file('to_delete.txt', 'content')
        assert filesystem.delete_file('to_delete.txt')
        assert not filesystem.list_files()
        
        with pytest.raises(FileSystemError):
            filesystem.read_file('to_delete.txt')

    def test_delete_nonexistent_file(self, filesystem):
        """测试删除不存在的文件"""
        assert not filesystem.delete_file('nonexistent.txt')

    def test_delete_binary_file_with_description(self, filesystem):
        """测试删除二进制文件及其描述文件"""
        filesystem.save_file('test.bin', b'binary')
        assert filesystem.delete_file('test.bin')
        
        files = filesystem.list_files()
        assert len(files) == 0


class TestEditOperations:
    """测试文件编辑功能"""
    
    def test_edit_text_file(self, filesystem):
        """测试编辑文本文件"""
        original = "line1\nline2\nline3"
        filesystem.save_file('test.txt', original)
        
        patch = """--- a/test.txt
+++ b/test.txt
@@ -1,3 +1,3 @@
 line1
-line2
+modified line2
 line3"""
        
        result = filesystem.edit_file('test.txt', patch)
        assert result['changed'] == True
        
        updated = filesystem.read_file('test.txt')
        assert 'modified line2' in updated['content']

    def test_edit_binary_description(self, filesystem):
        """测试编辑二进制文件的描述"""
        filesystem.save_file('test.bin', b'binary data')
        
        patch = """--- a/test.bin.description.txt
+++ b/test.bin.description.txt
@@ -1 +1 @@
 YmluYXJ5IGRhdGE=
+additional info"""
        
        result = filesystem.edit_file('test.bin', patch)
        assert result['changed'] == True

    def test_edit_nonexistent_file(self, filesystem):
        """测试编辑不存在的文件"""
        patch = """--- a/nonexistent.txt
+++ b/nonexistent.txt
@@ -0,0 +1 @@
+new content"""
        
        with pytest.raises(FileSystemError):
            filesystem.edit_file('nonexistent.txt', patch)


class TestSecurity:
    """测试安全性功能"""
    
    def test_path_traversal_prevention(self, filesystem):
        """测试路径遍历攻击防护"""
        with pytest.raises(FileSystemError):
            filesystem.save_file('../../../etc/passwd', 'content')
        
        with pytest.raises(FileSystemError):
            filesystem.read_file('../../../etc/passwd')
        
        with pytest.raises(FileSystemError):
            filesystem.delete_file('../../../etc/passwd')

    def test_absolute_path_handling(self, filesystem):
        """测试绝对路径处理"""
        with pytest.raises(FileSystemError):
            filesystem.save_file('/etc/passwd', 'content')

    def test_path_normalization(self, filesystem):
        """测试路径规范化"""
        filesystem.save_file('dir/../test.txt', 'content')
        files = filesystem.list_files()
        assert 'test.txt' in files


class TestMetadata:
    """测试元数据功能"""
    
    def test_registry_consistency(self, filesystem):
        """测试注册表一致性"""
        content = "test content"
        filesystem.save_file('test.txt', content)
        
        reg = filesystem._read_registry()
        entry = reg['test.txt']
        
        assert entry['file_path'] == 'test.txt'
        assert entry['size'] == len(content)
        assert entry['mime'] == 'text/plain'
        assert 'content_hash' in entry
        assert 'last_modified' in entry

    def test_hash_consistency(self, filesystem):
        """测试哈希值一致性"""
        content = "test content for hashing"
        filesystem.save_file('test.txt', content)
        
        reg1 = filesystem._read_registry()
        hash1 = reg1['test.txt']['content_hash']
        
        # 重新读取相同内容应该产生相同的哈希
        filesystem.save_file('test2.txt', content)
        reg2 = filesystem._read_registry()
        hash2 = reg2['test2.txt']['content_hash']
        
        assert hash1 == hash2


class TestLargeFiles:
    """测试大文件处理"""
    
    def test_large_text_file(self, filesystem):
        """测试大文本文件"""
        large_content = "x" * 100000  # 100KB
        filesystem.save_file('large.txt', large_content)
        
        result = filesystem.read_file('large.txt')
        assert len(result['content']) == 100000

    def test_large_binary_file(self, filesystem):
        """测试大二进制文件"""
        large_binary = b"x" * 50000  # 50KB
        filesystem.save_file('large.bin', large_binary)
        
        result = filesystem.read_file('large.bin')
        # 应该被base64编码
        assert len(result['content']) > 50000


class TestConcurrentAccess:
    """测试并发访问"""
    
    def test_concurrent_writes(self, filesystem):
        """测试并发写入"""
        def write_file(file_id):
            content = f"content from thread {file_id}"
            filesystem.save_file(f'thread_{file_id}.txt', content)
        
        threads = []
        for i in range(10):
            thread = threading.Thread(target=write_file, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        files = filesystem.list_files()
        assert len(files) == 10
        
        for i in range(10):
            assert f'thread_{i}.txt' in files

    def test_concurrent_reads(self, filesystem):
        """测试并发读取"""
        filesystem.save_file('shared.txt', 'shared content')
        
        results = []
        def read_file():
            result = filesystem.read_file('shared.txt')
            results.append(result['content'])
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=read_file)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 10
        assert all(content == 'shared content' for content in results)


class TestSpecialCases:
    """测试特殊情况"""
    
    def test_unicode_content(self, filesystem):
        """测试Unicode内容"""
        unicode_content = "Hello 世界 🌍 こんにちは"
        filesystem.save_file('unicode.txt', unicode_content)
        
        result = filesystem.read_file('unicode.txt')
        assert result['content'] == unicode_content

    def test_special_characters_in_filename(self, filesystem):
        """测试特殊字符文件名"""
        filename = 'test-file_name@2024.txt'
        filesystem.save_file(filename, 'content')
        
        files = filesystem.list_files()
        assert filename in files

    def test_nested_directory_creation(self, filesystem):
        """测试嵌套目录创建"""
        nested_path = 'level1/level2/level3/test.txt'
        filesystem.save_file(nested_path, 'nested content')
        
        result = filesystem.read_file(nested_path)
        assert result['content'] == 'nested content'

    def test_file_overwrite(self, filesystem):
        """测试文件覆盖"""
        filesystem.save_file('overwrite.txt', 'original')
        filesystem.save_file('overwrite.txt', 'overwritten')
        
        result = filesystem.read_file('overwrite.txt')
        assert result['content'] == 'overwritten'


class TestErrorHandling:
    """测试错误处理"""
    
    def test_read_nonexistent_file(self, filesystem):
        """测试读取不存在的文件"""
        with pytest.raises(FileSystemError):
            filesystem.read_file('nonexistent.txt')

    def test_edit_unsupported_file_type(self, filesystem):
        """测试编辑不支持的文件类型"""
        filesystem.save_file('test.xyz', 'content')
        with pytest.raises(FileSystemError):
            filesystem.edit_file('test.xyz', 'invalid patch')

    def test_invalid_patch_format(self, filesystem):
        """测试无效的补丁格式"""
        filesystem.save_file('test.txt', 'content')
        with pytest.raises(FileSystemError):
            filesystem.edit_file('test.txt', 'invalid patch format')


class TestAPI:
    """测试API功能"""
    
    def test_describe_api(self):
        """测试API描述功能"""
        description = FileSystem.describe_api()
        assert 'FileSystem API' in description
        assert 'list_files' in description
        assert 'read_file' in description
        assert 'save_file' in description
        assert 'delete_file' in description
        assert 'edit_file' in description

    def test_describe_specific_methods(self):
        """测试特定方法的API描述"""
        description = FileSystem.describe_api(['save_file', 'read_file'])
        assert 'save_file' in description
        assert 'read_file' in description
        assert 'delete_file' not in description


if __name__ == '__main__':
    pytest.main([__file__, '-v'])