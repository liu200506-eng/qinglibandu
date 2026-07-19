#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MagicStudy 路径工具模块

统一执行路径规范:
  1. 所有路径必须使用 Path(__file__).resolve() 计算
  2. 从仓库根目录和 backend 目录执行应产生相同结果
  3. 提供 BACKEND_DIR / REPO_ROOT / KNOWLEDGE_BASE_DIR / REPORTS_DIR 等常量
"""
import os
import unicodedata
from pathlib import Path

# 关键目录（基于当前文件位置，不依赖 cwd）
BACKEND_DIR = Path(__file__).resolve().parent.parent           # backend/
REPO_ROOT = BACKEND_DIR.parent                                  # 仓库根
KNOWLEDGE_BASE_DIR = BACKEND_DIR / 'knowledge_base'             # knowledge_base/
REPORTS_DIR = REPO_ROOT / 'reports'                             # reports/
BACKUPS_DIR = BACKEND_DIR / 'backups'                           # backend/backups/
DATABASE_DIR = BACKEND_DIR / 'database'                         # backend/database/
SCRIPTS_DIR = BACKEND_DIR / 'scripts'                           # backend/scripts/
SERVICES_DIR = BACKEND_DIR / 'services'                         # backend/services/
TESTS_DIR = BACKEND_DIR / 'tests'                               # backend/tests/

# 数据库文件
DATABASE_PATH = BACKEND_DIR / 'database' / 'magicstudy.db'

# Windows 文件名安全检查常量
WINDOWS_INVALID_CHARS = set('\\/:*?"<>|')
WINDOWS_RESERVED_NAMES = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
}
MAX_PATH_LENGTH = 200  # Windows 默认 260，留余量


def ensure_dir(path: Path) -> Path:
    """确保目录存在，不存在则创建"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_windows_reserved_name(name: str) -> bool:
    """判断是否是 Windows 保留文件名

    检查:
      - CON, PRN, AUX, NUL
      - COM1 ~ COM9
      - LPT1 ~ LPT9
    """
    if not name:
        return False
    # 去掉扩展名
    stem = name.split('.')[0].upper()
    return stem in WINDOWS_RESERVED_NAMES


def has_windows_invalid_chars(name: str) -> bool:
    """判断是否包含 Windows 非法字符 \\ / : * ? " < > |"""
    if not name:
        return False
    return bool(set(name) & WINDOWS_INVALID_CHARS)


def has_invalid_ending(name: str) -> bool:
    """判断文件名是否以空格或英文句点结尾

    同时检查：
      - 整个文件名末尾
      - 文件名 stem（去扩展名后）末尾
    """
    if not name:
        return False
    # 整个文件名末尾
    if name != name.rstrip(' .'):
        return True
    # stem 末尾（例如 "trailing_space .md" 的 stem 是 "trailing_space "）
    stem = name
    if '.' in name:
        # 找最后一个点，去除扩展名
        last_dot = name.rfind('.')
        if last_dot > 0:
            stem = name[:last_dot]
    if stem != stem.rstrip(' .'):
        return True
    return False


def is_unicode_normalized(name: str) -> bool:
    """判断文件名是否已做 Unicode NFC 规范化"""
    if not name:
        return True
    return unicodedata.normalize('NFC', name) == name


def is_path_too_long(path: Path, max_length: int = MAX_PATH_LENGTH) -> bool:
    """判断路径是否过长"""
    return len(str(path)) > max_length


def has_unexpected_directory(name: str) -> bool:
    """判断文件名是否包含斜杠导致的意外目录穿越

    例如 "foo/bar.md" 在 Windows 上会被解释为目录
    """
    if not name:
        return False
    return '/' in name or '\\' in name


def check_filename_safety(name: str) -> list:
    """完整文件名安全检查

    检查项:
      1. Windows 非法字符 \\ / : * ? " < > |
      2. CON, PRN, AUX, NUL, COM1-9, LPT1-9
      3. 结尾空格
      4. 结尾英文句点
      5. Unicode 规范化重名
      6. 路径长度
      7. 斜杠导致的意外目录

    Returns:
        问题列表，每项为 (code, message)。空列表表示通过。
    """
    issues = []
    
    if not name:
        issues.append(('EMPTY_NAME', '文件名为空'))
        return issues
    
    # 1. Windows 非法字符
    invalid = set(name) & WINDOWS_INVALID_CHARS
    if invalid:
        issues.append((
            'INVALID_CHARS',
            '包含 Windows 非法字符: ' + ''.join(sorted(invalid))
        ))
    
    # 2. Windows 保留名
    if is_windows_reserved_name(name):
        issues.append((
            'RESERVED_NAME',
            'Windows 保留文件名: ' + name
        ))
    
    # 3. 结尾空格或英文句点
    if has_invalid_ending(name):
        issues.append((
            'INVALID_ENDING',
            '文件名以空格或英文句点结尾: ' + name
        ))
    
    # 4. Unicode 规范化
    if not is_unicode_normalized(name):
        issues.append((
            'NOT_NORMALIZED',
            '文件名未做 Unicode NFC 规范化（可能导致重名）: ' + name
        ))
    
    # 5. 路径长度
    if len(name) > MAX_PATH_LENGTH:
        issues.append((
            'TOO_LONG',
            '文件名过长 (' + str(len(name)) + '>' + str(MAX_PATH_LENGTH) + '): ' + name[:30] + '...'
        ))
    
    # 6. 斜杠导致的意外目录
    if has_unexpected_directory(name):
        issues.append((
            'UNEXPECTED_DIRECTORY',
            '文件名包含路径分隔符（可能导致意外目录）: ' + name
        ))
    
    return issues


def check_all_filenames_in_dir(directory: Path) -> dict:
    """检查目录下所有文件名安全性

    Returns:
        {
            'total_files': 总文件数,
            'issues_count': 有问题的文件数,
            'issues': [
                {'file': 'path', 'issues': [(code, msg), ...]},
                ...
            ]
        }
    """
    result = {
        'total_files': 0,
        'issues_count': 0,
        'issues': [],
    }
    
    if not directory.exists():
        return result
    
    for path in directory.rglob('*'):
        if path.is_file():
            result['total_files'] += 1
            basename = path.name
            file_issues = check_filename_safety(basename)
            if file_issues:
                result['issues_count'] += 1
                result['issues'].append({
                    'file': str(path),
                    'relative': str(path.relative_to(directory)),
                    'issues': [{'code': c, 'message': m} for c, m in file_issues],
                })
    
    return result


def normalize_path(path: Path) -> Path:
    """将路径规范化为绝对路径"""
    if path.is_absolute():
        return path.resolve()
    return (Path.cwd() / path).resolve()


def get_repo_relative_path(path: Path) -> Path:
    """获取相对于仓库根目录的路径"""
    try:
        return Path(path).resolve().relative_to(REPO_ROOT)
    except ValueError:
        # 不在仓库内，返回原路径
        return Path(path)
