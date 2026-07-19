#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安装 MagicStudy Git 钩子

通过 `git config core.hooksPath .githooks` 配置仓库追踪的钩子目录，
让团队成员克隆仓库后即可获得相同的钩子。

使用方法:
  python backend/scripts/install_precommit.py            # 安装
  python backend/scripts/install_precommit.py --uninstall  # 卸载
  python backend/scripts/install_precommit.py --check     # 检查状态

钩子说明:
  .githooks/pre-commit  - 快速检查（仅暂存区文件）
  .githooks/pre-push     - 完整 validate-all 校验
"""
import os
import sys
import subprocess
import stat
from pathlib import Path


def find_git_root(start_dir: str) -> str:
    """从给定目录向上查找 .git 目录"""
    current = Path(start_dir).resolve()
    while True:
        git_dir = current / '.git'
        if git_dir.exists():
            return str(current)
        if current.parent == current:
            return ""
        current = current.parent


def run_git(args: list, cwd: str = None) -> tuple:
    """执行 git 命令"""
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=True, text=True,
            encoding='utf-8', errors='replace',
            cwd=cwd,
        )
        return (result.returncode, result.stdout.strip(), result.stderr.strip())
    except Exception as e:
        return (1, '', str(e))


def set_executable(path: str) -> None:
    """设置文件可执行权限（Linux/Mac）"""
    try:
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    except Exception:
        pass


def main() -> int:
    uninstall = '--uninstall' in sys.argv or '-u' in sys.argv
    check_only = '--check' in sys.argv

    git_root = find_git_root(os.path.dirname(os.path.abspath(__file__)))
    if not git_root:
        print("[ERROR] 未找到 .git 目录")
        return 2

    githooks_dir = os.path.join(git_root, '.githooks')
    pre_commit = os.path.join(githooks_dir, 'pre-commit')
    pre_push = os.path.join(githooks_dir, 'pre-push')

    if check_only:
        # 检查模式
        print("=" * 60)
        print("MagicStudy Git 钩子状态检查")
        print("=" * 60)
        rc, val, _ = run_git(['config', 'core.hooksPath'], cwd=git_root)
        if rc == 0 and val == '.githooks':
            print("[OK] core.hooksPath 已配置为 .githooks")
        else:
            print("[FAIL] core.hooksPath 未配置")
            print("  运行: python backend/scripts/install_precommit.py")
        print()
        print("钩子文件:")
        for name, path in [('pre-commit', pre_commit), ('pre-push', pre_push)]:
            exists = os.path.exists(path)
            status = 'OK' if exists else 'MISSING'
            print("  [" + status + "] " + name + " -> " + path)
            if exists:
                set_executable(path)
        return 0

    if uninstall:
        # 卸载
        rc, _, err = run_git(['config', '--unset', 'core.hooksPath'], cwd=git_root)
        if rc == 0 or rc == 5:  # 5 = 配置项不存在
            print("[OK] 已卸载 core.hooksPath 配置")
        else:
            print("[WARN] 卸载配置失败: " + err)
        print("钩子文件保留在 .githooks/ 中（不影响仓库）")
        print("Git 已恢复使用 .git/hooks/ 目录")
        return 0

    # 安装
    if not os.path.exists(githooks_dir):
        print("[ERROR] .githooks 目录不存在: " + githooks_dir)
        return 2

    # 检查钩子文件
    missing = []
    if not os.path.exists(pre_commit):
        missing.append('pre-commit')
    if not os.path.exists(pre_push):
        missing.append('pre-push')
    if missing:
        print("[ERROR] 缺少钩子文件: " + ", ".join(missing))
        return 2

    # 设置可执行权限
    set_executable(pre_commit)
    set_executable(pre_push)

    # 配置 core.hooksPath
    rc, _, err = run_git(['config', 'core.hooksPath', '.githooks'], cwd=git_root)
    if rc != 0:
        print("[ERROR] 配置 core.hooksPath 失败: " + err)
        return 2

    print("[OK] Git 钩子已安装")
    print()
    print("配置信息:")
    print("  仓库根目录: " + git_root)
    print("  钩子目录:   " + githooks_dir)
    rc, val, _ = run_git(['config', 'core.hooksPath'], cwd=git_root)
    if rc == 0:
        print("  hooksPath:  " + val)
    print()
    print("钩子说明:")
    print("  pre-commit  快速检查（仅暂存区文件，毫秒级）")
    print("              - Windows 非法文件名")
    print("              - JSON 格式合法性")
    print("              - schema_version/course_code/node_code 必需字段")
    print("              - 重复 node_code 检查")
    print("              - 循环依赖检测")
    print("              - 题目答案/难度合法性")
    print("  pre-push    完整校验（运行 validate-all）")
    print("              - 全部课程的 ETL --dry-run")
    print("              - 较慢，可使用 git push --no-verify 跳过")
    print()
    print("退出码:")
    print("  0 = 通过")
    print("  1 = 校验失败")
    print("  2 = 环境错误")
    print()
    print("命令:")
    print("  卸载:   python backend/scripts/install_precommit.py --uninstall")
    print("  检查:   python backend/scripts/install_precommit.py --check")
    print("  手动跑: python backend/manage_knowledge.py validate-all --policy dev")
    return 0


if __name__ == '__main__':
    sys.exit(main())
