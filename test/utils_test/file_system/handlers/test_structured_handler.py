import pytest
import os
import sys
import tempfile
import shutil

# 计算项目根路径并添加到 sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from src.file_system.handlers.structured_handler import StructuredFileHandler

@pytest.fixture
def handler():
    return StructuredFileHandler()

@pytest.fixture
def temp_dir():
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)

def test_json_read_write(handler, temp_dir):
    file_path = os.path.join(temp_dir, 'test.json')
    content = {'key': 'value'}
    assert handler.write(file_path, content)
    assert os.path.exists(file_path)
    read_content = handler.read(file_path)
    assert isinstance(read_content, str)
    assert 'key: value' in read_content

def test_jsonl_read_write(handler, temp_dir):
    file_path = os.path.join(temp_dir, 'test.jsonl')
    content = [{'key': 'value1'}, {'key': 'value2'}]
    assert handler.write(file_path, content)
    assert os.path.exists(file_path)
    read_content = handler.read(file_path)
    assert isinstance(read_content, str)
    assert 'key: value1' in read_content

def test_csv_read_write(handler, temp_dir):
    file_path = os.path.join(temp_dir, 'test.csv')
    content = [['header1', 'header2'], ['data1', 'data2']]
    assert handler.write(file_path, content)
    assert os.path.exists(file_path)
    read_content = handler.read(file_path)
    assert isinstance(read_content, str)
    assert '- header1' in read_content

def test_excel_read_write(handler, temp_dir):
    file_path = os.path.join(temp_dir, 'test.xlsx')
    content = [{'header1': 'data1', 'header2': 'data2'}]
    assert handler.write(file_path, content)
    assert os.path.exists(file_path)
    read_content = handler.read(file_path)
    assert isinstance(read_content, str)
    assert 'header1: data1' in read_content

def test_xml_read_write(handler, temp_dir):
    file_path = os.path.join(temp_dir, 'test.xml')
    content = {'root': {'key': 'value'}}
    assert handler.write(file_path, content)
    assert os.path.exists(file_path)
    read_content = handler.read(file_path)
    assert isinstance(read_content, str)
    assert 'root:\n    key: value' in read_content

def test_yaml_read_write(handler, temp_dir):
    file_path = os.path.join(temp_dir, 'test.yaml')
    content = {'key': 'value'}
    assert handler.write(file_path, content)
    assert os.path.exists(file_path)
    read_content = handler.read(file_path)
    assert isinstance(read_content, str)
    assert 'key: value' in read_content

def test_toml_read_write(handler, temp_dir):
    file_path = os.path.join(temp_dir, 'test.toml')
    content = {'key': 'value'}
    assert handler.write(file_path, content)
    assert os.path.exists(file_path)
    read_content = handler.read(file_path)
    assert isinstance(read_content, str)
    assert 'key: value' in read_content

def test_ini_read_write(handler, temp_dir):
    file_path = os.path.join(temp_dir, 'test.ini')
    content = {'section': {'key': 'value'}}
    assert handler.write(file_path, content)
    assert os.path.exists(file_path)
    read_content = handler.read(file_path)
    assert isinstance(read_content, str)
    assert 'section:\n    key: value' in read_content
