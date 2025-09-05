import sys
import os

from src.sandbox import (
    run_environment_safely,
    create_true_sandbox,  
    execute_in_sandbox,   
    list_sandbox_sessions,  
    cleanup_sandbox_session,  
    get_requirements,
    exec_bash,
)

if __name__ == "__main__":
    import json
    import os
    import time


    print("=" * 60)
    print(" Python 代码安全执行环境测试")
    print("=" * 60)
    """
    # 方式1：一次性执行（保持不变）
    print("\n【测试1：一次性执行】")
    print("-" * 30)
    try:
        print(" 执行中...")
        result = run_environment_safely('print("Hello World")', debug=True)
        print(f" 执行成功")
        print(f" 输出: '{result.get('stdout', 'NO_OUTPUT')}'")
        print(f"  返回码: {result.get('returncode', 'N/A')}")
        print(f" 成功状态: {result.get('success', False)}")
        if result.get('error'):
            print(f"  错误: {result['error']}")
        print(f" 完整结果键: {list(result.keys())}")
    except Exception as e:
        print(f" 执行失败: {e}")
        import traceback
        traceback.print_exc()

    # 方式2：持久化会话 - 使用新的函数名
    print("\n【测试2：持久化会话 - NumPy】")
    print("-" * 30)
    session = None
    try:
        print(" 创建持久化会话...")
        session = create_true_sandbox(timeout_minutes=5, debug=True)
        print(f" 会话创建成功，ID: {session.session_id}")
        print(" 安装并使用NumPy...")
        numpy_code = '''
print("Installing numpy...")
import numpy as np
print("NumPy imported successfully")
print(f"NumPy版本: {np.__version__}")
arr = np.array([1,2,3])
print(f"测试数组: {arr}")
print(f"数组平均值: {np.mean(arr)}")
print("NumPy测试完成")
'''
        result1 = session.run_code(numpy_code, ['numpy'])
        print(f" NumPy完整测试结果:")
        print(f"   输出: '{result1.get('stdout', 'NO_OUTPUT')}'")
        print(f"   返回码: {result1.get('returncode', 'N/A')}")
        print(f"   成功状态: {result1.get('success', False)}")
        if result1.get('error'):
            print(f"     错误: {result1['error']}")
        print(" 测试会话持久性...")
        persistence_code = '''
# 验证之前导入的numpy是否仍然可用
try:
    print(f"之前的numpy仍可用: {np.__version__}")
    print(f"可以创建新数组: {np.array([4,5,6])}")
    print(" 会话持久性正常")
except NameError as e:
    print(f" 会话持久性失败: {e}")
    print("重新导入numpy...")
    import numpy as np
    print(f"重新导入成功: {np.__version__}")
'''
        result2 = session.run_code(persistence_code)
        print(f" 持久性测试结果:")
        print(f"   输出: '{result2.get('stdout', 'NO_OUTPUT')}'")
        print(f"   返回码: {result2.get('returncode', 'N/A')}")
        print(f"   成功状态: {result2.get('success', False)}")
        if result2.get('error'):
            print(f"     错误: {result2['error']}")
        
    except Exception as e:
        print(f" 持久化会话失败: {e}")
        import traceback
        traceback.print_exc()

    # 方式3：通过会话ID管理 - 使用新的函数名
    print("\n【测试3：会话ID管理】")
    print("-" * 30)
    try:
        if session and hasattr(session, 'session_id'):
            session_id = session.session_id
            print(" 通过会话ID执行中...")
            result3 = execute_in_sandbox(session_id, 'print("Hello from session")')
            print(f" 会话ID执行结果:")
            print(f"   输出: '{result3.get('stdout', 'NO_OUTPUT')}'")
            print(f"   返回码: {result3.get('returncode', 'N/A')}")
            print(f"   成功状态: {result3.get('success', False)}")
            if result3.get('error'):
                print(f"     错误: {result3['error']}")
        else:
            print("  没有可用的会话")  
        print(" 获取会话列表中...")
        sessions = list_sandbox_sessions()
        print(f" 当前活跃会话数: {len(sessions)}")
        
    except Exception as e:
        print(f" 会话ID管理失败: {e}")
        import traceback
        traceback.print_exc()


    # 测试4：修复后的依赖测试 - 放宽安全限制
    print("\n【测试4：修复后的依赖测试】")
    print("-" * 30)
    try:
        print(" 测试常用依赖安装...")
        simple_requirements = ['requests', 'urllib3']
        requests_code = '''
import requests
import urllib3
print(f"Requests版本: {requests.__version__}")
print(f"Urllib3版本: {urllib3.__version__}")
print(" 网络库导入成功")
print("可以正常使用HTTP客户端库")
'''
        
        result = run_environment_safely(requests_code, simple_requirements, debug=True)
        print(f" 网络库测试结果:")
        print(f"   输出: '{result.get('stdout', 'NO_OUTPUT')}'")
        print(f"   返回码: {result.get('returncode', 'N/A')}")
        print(f"   成功状态: {result.get('success', False)}")
        if result.get('error'):
            print(f"     错误: {result['error']}")
            
    except Exception as e:
        print(f" 依赖测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试5：大规模依赖测试 - 移除数量限制
    print("\n【测试5：大规模依赖测试 - 无限制版】")
    print("-" * 30)
    try:
        print(" 测试大规模依赖...")
        large_requirements = [
            'requests', 'urllib3', 'python-dotenv', 'pydantic', 'httpx',
            'aiohttp', 'fastapi', 'uvicorn', 'lxml', 'beautifulsoup4'
        ]
        print(f" 测试依赖数量: {len(large_requirements)}")
        print(f" 依赖列表: {large_requirements}")
        
        large_code = '''
print("开始导入大规模依赖...")
import_results = []

# 测试所有依赖的导入
dependencies = [
    ('requests', 'requests'),
    ('urllib3', 'urllib3'),
    ('python-dotenv', 'dotenv'),
    ('pydantic', 'pydantic'),
    ('httpx', 'httpx'),
    ('aiohttp', 'aiohttp'),
    ('fastapi', 'fastapi'),
    ('uvicorn', 'uvicorn'),
    ('lxml', 'lxml'),
    ('beautifulsoup4', 'bs4')
]

for pkg_name, import_name in dependencies:
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f" {pkg_name}: {version}")
        import_results.append(f"{pkg_name}: 成功")
    except ImportError as e:
        print(f" {pkg_name}: 导入失败 - {e}")
        import_results.append(f"{pkg_name}: 失败")
    except Exception as e:
        print(f"  {pkg_name}: 其他错误 - {e}")
        import_results.append(f"{pkg_name}: 错误")

print(f"\\n 导入结果统计:")
success_count = len([r for r in import_results if "成功" in r])
total_count = len(import_results)
print(f"成功: {success_count}/{total_count}")
print("大规模依赖测试完成")
'''
        result = run_environment_safely(large_code, large_requirements, debug=True, timeout_sec=300)
        print(f" 大规模依赖测试结果:")
        print(f"   输出: '{result.get('stdout', 'NO_OUTPUT')}'")
        print(f"   返回码: {result.get('returncode', 'N/A')}")
        print(f"   成功状态: {result.get('success', False)}")
        if result.get('error'):
            print(f"     错误: {result['error']}")
            
    except Exception as e:
        print(f" 大规模依赖测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试6：Xiaohongshu API MCP Server - 完整版（无限制）
    print("\n【测试6：Xiaohongshu API MCP Server - 完整版】")
    print("-" * 30)
    try:
        print(" 获取依赖信息中...")
        sample_code = '''
print("hello sandbox - Xiaohongshu API MCP Server")
print("开始测试所有依赖...")

# 尝试导入所有可能的依赖
test_imports = [
    'google.cloud.core',
    'google.adk', 
    'mcp',
    'requests',
    'aiohttp',
    'httpx',
    'dotenv',
    'pydantic',
    'fastapi',
    'uvicorn',
    'lxml'
]

success_imports = []
failed_imports = []

for import_name in test_imports:
    try:
        module = __import__(import_name)
        success_imports.append(import_name)
        print(f" {import_name}: 导入成功")
    except ImportError:
        failed_imports.append(import_name)
        print(f" {import_name}: 导入失败")
    except Exception as e:
        failed_imports.append(import_name)
        print(f"  {import_name}: 其他错误 - {e}")

print(f"\\n Xiaohongshu MCP Server 依赖测试结果:")
print(f" 成功导入: {len(success_imports)}")
print(f" 失败导入: {len(failed_imports)}")
print(f" 成功率: {len(success_imports)/(len(success_imports)+len(failed_imports))*100:.1f}%")
print("Xiaohongshu API MCP Server 测试完成")
'''
        
        tools_jsons_path = os.getcwd() + f"/data/tools/combined_tools.json"
        mcp_server_name = "Xiaohongshu API MCP Server"
        
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("获取依赖信息超时")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(15)
        
        try:
            mcp_requirements = get_requirements(tools_jsons_path, mcp_server_name)
            signal.alarm(0)
            
            print(f" 完整依赖列表 ({len(mcp_requirements) if mcp_requirements else 0}个): {mcp_requirements}")
            
            if mcp_requirements:
                print(" 执行完整依赖安装测试...")
                print(f" 将安装 {len(mcp_requirements)} 个依赖包")
                print("  预计需要 2-5 分钟，请耐心等待...")
                
                result = run_environment_safely(sample_code, mcp_requirements, debug=True, timeout_sec=400)
                print(f" Xiaohongshu API MCP Server 完整测试结果:")
                print(f"   输出: '{result.get('stdout', 'NO_OUTPUT')}'")
                print(f"   返回码: {result.get('returncode', 'N/A')}")
                print(f"   成功状态: {result.get('success', False)}")
                if result.get('error'):
                    print(f"     错误: {result['error']}")
            else:
                print("  未找到依赖信息")
                
        except TimeoutError as e:
            signal.alarm(0)
            print(f" 获取依赖信息超时: {e}")
            print("  跳过Xiaohongshu测试")
            
    except Exception as e:
        print(f" Xiaohongshu测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试7：极限依赖测试
    print("\n【测试7：极限依赖测试】")
    print("-" * 30)
    try:
        print(" 测试极限数量依赖...")
        # 创建一个包含20+个依赖的列表
        extreme_requirements = [
            'requests', 'urllib3', 'python-dotenv', 'pydantic', 'httpx',
            'aiohttp', 'fastapi', 'uvicorn', 'lxml', 'beautifulsoup4',
            'click', 'rich', 'typer', 'pytest', 'black',
            'flake8', 'mypy', 'isort', 'pre-commit', 'tox'
        ]
        
        print(f" 极限测试: {len(extreme_requirements)} 个依赖")
        print(f" 依赖列表: {extreme_requirements}")
        print("  预计需要 3-8 分钟...")
        
        extreme_code = '''
print(" 极限依赖测试开始...")
print(f"Python版本: {__import__('sys').version}")

# 测试所有依赖
test_packages = [
    'requests', 'urllib3', 'dotenv', 'pydantic', 'httpx',
    'aiohttp', 'fastapi', 'uvicorn', 'lxml', 'bs4',
    'click', 'rich', 'typer', 'pytest', 'black',
    'flake8', 'mypy', 'isort', 'pre_commit', 'tox'
]

results = {'success': 0, 'failed': 0, 'details': []}

for pkg in test_packages:
    try:
        module = __import__(pkg)
        version = getattr(module, '__version__', 'unknown')
        results['success'] += 1
        results['details'].append(f" {pkg}: {version}")
        print(f" {pkg}: {version}")
    except ImportError:
        results['failed'] += 1
        results['details'].append(f" {pkg}: 导入失败")
        print(f" {pkg}: 导入失败")
    except Exception as e:
        results['failed'] += 1
        results['details'].append(f"  {pkg}: {str(e)}")
        print(f"  {pkg}: {str(e)}")

total = results['success'] + results['failed']
success_rate = (results['success'] / total * 100) if total > 0 else 0

print(f"\\n 极限依赖测试结果:")
print(f"总计: {total} 个包")
print(f"成功: {results['success']} 个")
print(f"失败: {results['failed']} 个")
print(f"成功率: {success_rate:.1f}%")
print("极限依赖测试完成!")
'''
        
        result = run_environment_safely(extreme_code, extreme_requirements, debug=True, timeout_sec=600)
        print(f"极限依赖测试结果:")
        print(f"   输出: '{result.get('stdout', 'NO_OUTPUT')}'")
        print(f"   返回码: {result.get('returncode', 'N/A')}")
        print(f"   成功状态: {result.get('success', False)}")
        if result.get('error'):
            print(f"错误: {result['error']}")
            
    except Exception as e:
        print(f"极限依赖测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    try:
        sessions = list_sandbox_sessions()
        print(f"会话统计:")
        print(f"   总会话数: {len(sessions)}")
        
        if sessions:
            print(f"\n会话详情:")
            for i, sess in enumerate(sessions, 1):
                session_id = sess.get('session_id', 'Unknown')
                short_id = session_id[:8] + "..." if len(session_id) > 8 else session_id
                time_remaining = sess.get('time_remaining', 'unknown')
                print(f"   {i}. ID: {short_id} | 剩余时间: {time_remaining}")
        
        if 'session' in locals() and session and hasattr(session, 'session_id'):
            print(f"\n清理测试会话: {session.session_id[:8]}...")
            cleanup_sandbox_session(session.session_id)  # 修复：使用正确的函数名
            print("清理完成")
        
    except Exception as e:
        print(f"统计信息获取失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
    print("无限制沙箱环境测试完成")
    print("支持任意数量依赖的安装和使用")
    print("=" * 60)
"""
    # 测试8：Bash基础功能测试
    session = None
    try:
        print(" 创建测试会话...")
        session = create_true_sandbox(timeout_minutes=10, debug=True)
        print(f" 会话创建成功，ID: {session.session_id}")
    except Exception as e:
        print(f" 会话创建失败: {e}")
        import traceback
        traceback.print_exc()


    print("\n【测试8：Bash基础功能测试】")
    print("-" * 30)
    if 'session' in locals() and session and hasattr(session, 'session_id'):
        try:
            session_id = session.session_id
            
            # 基础命令测试
            print(" 测试基础bash命令...")
            result = exec_bash(session_id, 'echo "Hello from Bash!" && pwd && whoami')
            print(f" bash基础命令结果:")
            print(f"   输出: '{result.get('stdout', 'NO_OUTPUT')}'")
            print(f"   成功: {result.get('success', False)}")
            if result.get('error'):
                print(f"   错误: {result['error']}")
            
        except Exception as e:
            print(f" Bash基础测试失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(" 跳过：无可用会话")

    # 测试9：Bash + Python混合使用
    print("\n【测试9：Bash + Python混合使用】")
    print("-" * 30)
    if 'session' in locals() and session and hasattr(session, 'session_id'):
        try:
            session_id = session.session_id
            
            # 先用bash创建文件
            print(" 用bash创建测试文件...")
            result = exec_bash(session_id, 'echo "Hello from bash file" > test.txt && ls -la test.txt')
            print(f" bash文件创建结果:")
            print(f"   输出: '{result.get('stdout', 'NO_OUTPUT')}'")
            print(f"   成功: {result.get('success', False)}")
            
            # 再用Python读取文件
            print(" 用Python读取bash创建的文件...")
            python_code = '''
try:
    with open('test.txt', 'r') as f:
        content = f.read().strip()
    print(f"Python读取到: {content}")
    print("bash和Python混合使用成功")
except Exception as e:
    print(f"Python读取失败: {e}")
'''
            result = execute_in_sandbox(session_id, python_code)
            print(f" Python读取结果:")
            print(f"   输出: '{result.get('stdout', 'NO_OUTPUT')}'")
            print(f"   成功: {result.get('success', False)}")
            
        except Exception as e:
            print(f" 混合使用测试失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(" 跳过：无可用会话")

    # 测试10：用Bash安装和测试Python包
    print("\n【测试10：用Bash安装Python包】")
    print("-" * 30)
    if 'session' in locals() and session and hasattr(session, 'session_id'):
        try:
            session_id = session.session_id
            
            # 用bash安装包
            print(" 用bash安装requests包...")
            result = exec_bash(session_id, 'pip install requests', timeout=120)
            print(f" pip安装结果:")
            print(f"   输出: '{result.get('stdout', 'NO_OUTPUT')[:200]}...'")  # 截断长输出
            print(f"   成功: {result.get('success', False)}")
            
            if result.get('success'):
                # 用bash测试安装的包
                print(" 用bash测试安装的包...")
                test_result = exec_bash(session_id, 'python -c "import requests; print(f\\"Requests版本: {requests.__version__}\\")"')
                print(f" bash测试包结果:")
                print(f"   输出: '{test_result.get('stdout', 'NO_OUTPUT')}'")
                print(f"   成功: {test_result.get('success', False)}")
            
        except Exception as e:
            print(f" Bash安装包测试失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(" 跳过：无可用会话")

    # 测试11：复杂Bash脚本
    print("\n【测试11：复杂Bash脚本】")
    print("-" * 30)
    if 'session' in locals() and session and hasattr(session, 'session_id'):
        try:
            session_id = session.session_id
            
            print(" 执行复杂bash脚本...")
            complex_script = '''
echo "=== 环境信息 ==="
echo "当前目录: $(pwd)"
echo "Python版本: $(python --version 2>&1)"
echo "可用磁盘空间: $(df -h . | tail -1 | awk '{print $4}')"

echo -e "\\n=== 创建项目结构 ==="
mkdir -p project/{src,tests,docs}
echo "print('Hello World')" > project/src/main.py
echo "# 项目文档" > project/docs/README.md

echo -e "\\n=== 项目结构 ==="
tree project 2>/dev/null || find project -type f

echo -e "\\n=== 运行Python代码 ==="
cd project/src && python main.py

echo -e "\\n=== 脚本执行完成 ==="
'''
            result = exec_bash(session_id, complex_script, timeout=60)
            print(f" 复杂脚本结果:")
            print(f"   输出: '{result.get('stdout', 'NO_OUTPUT')}'")
            print(f"   成功: {result.get('success', False)}")
            if result.get('stderr'):
                print(f"   错误输出: '{result.get('stderr', '')}'")
            
        except Exception as e:
            print(f" 复杂脚本测试失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(" 跳过：无可用会话")

    # 测试12：验证Bash在沙箱环境中运行
    print("\n【测试12：验证Bash在沙箱环境中运行】")
    print("-" * 30)
    if 'session' in locals() and session and hasattr(session, 'session_id'):
        try:
            session_id = session.session_id
            
            print(" 测试Bash是否在沙箱环境中运行...")
            
            # 测试1：验证工作目录是沙箱目录
            print("\n 1. 验证工作目录:")
            result1 = exec_bash(session_id, "pwd", timeout=10)
            sandbox_dir = result1.get('stdout', '').strip()
            print(f"   Bash工作目录: {sandbox_dir}")
            
            # 通过Python获取工作目录对比
            python_result = session.run_code("import os; print(os.getcwd())")
            python_dir = python_result.get('stdout', '').strip()
            print(f"   Python工作目录: {python_dir}")
            print(f"   目录一致: {sandbox_dir == python_dir}")
            
            # 测试2：验证文件系统隔离
            print("\n 2. 验证文件系统隔离:")
            
            # 在Python中创建文件
            session.run_code("""
    with open('python_created.txt', 'w') as f:
        f.write('Created by Python in sandbox')
    """)
            
            # 在Bash中创建文件
            exec_bash(session_id, "echo 'Created by Bash in sandbox' > bash_created.txt")
            
            # 验证两者都能看到对方创建的文件
            result2 = exec_bash(session_id, "ls -la *.txt", timeout=10)
            print(f"   Bash看到的文件: {result2.get('stdout', '').strip()}")
            
            python_result2 = session.run_code("""
    import os
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]
    print('Python看到的txt文件:', txt_files)
    """)
            print(f"   Python看到的文件: {python_result2.get('stdout', '').strip()}")
            
            # 测试3：验证环境变量共享
            print("\n 3. 验证环境变量:")
            
            # Python设置环境变量
            session.run_code("""
    import os
    os.environ['SANDBOX_TEST'] = 'python_set_value'
    print('Python设置环境变量: SANDBOX_TEST =', os.environ.get('SANDBOX_TEST'))
    """)
            
            # Bash读取环境变量（注意：这个可能不会共享，因为是不同进程）
            result3 = exec_bash(session_id, "echo 'Bash读取环境变量: SANDBOX_TEST = '$SANDBOX_TEST", timeout=10)
            print(f"   {result3.get('stdout', '').strip()}")
            
            # 测试4：验证进程隔离
            print("\n 4. 验证进程隔离:")
            
            # 获取Python进程信息
            python_result3 = session.run_code("""
    import os
    print(f'Python PID: {os.getpid()}')
    print(f'Python PPID: {os.getppid()}')
    """)
            print(f"   {python_result3.get('stdout', '').strip()}")
            
            # 获取Bash进程信息
            result4 = exec_bash(session_id, "echo 'Bash PID: '$$; echo 'Bash PPID: '$PPID", timeout=10)
            print(f"   {result4.get('stdout', '').strip()}")
            
            # 测试5：验证资源限制（尝试危险操作）
            print("\n 5. 验证安全限制:")
            
            dangerous_commands = [
                ("访问根目录", "ls /root"),
                ("访问系统文件", "cat /etc/passwd"),
                ("查看系统进程", "ps aux"),
                ("网络操作", "ping -c 1 google.com"),
                ("系统信息", "uname -a")
            ]
            
            for desc, cmd in dangerous_commands:
                result = exec_bash(session_id, cmd, timeout=5)
                success = result.get('success', False)
                output = result.get('stdout', '').strip()[:50] + "..." if len(result.get('stdout', '')) > 50 else result.get('stdout', '').strip()
                error = result.get('stderr', '').strip()[:50] + "..." if len(result.get('stderr', '')) > 50 else result.get('stderr', '').strip()
                
                print(f"   {desc}: {'✅ 成功' if success else '❌ 受限'}")
                if output:
                    print(f"     输出: {output}")
                if error:
                    print(f"     错误: {error}")
            
            # 测试6：验证超时机制
            print("\n 6. 验证超时机制:")
            result5 = exec_bash(session_id, "sleep 3", timeout=1)  # 1秒超时，但命令需要3秒
            print(f"   超时测试成功: {not result5.get('success', True)}")
            print(f"   错误信息: {result5.get('error', 'No error')}")
            
            print("\n ✅ Bash沙箱环境验证完成")
            
        except Exception as e:
            print(f" Bash沙箱环境验证失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(" 跳过：无可用会话")
