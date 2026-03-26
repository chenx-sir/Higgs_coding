#!/bin/bash
# HiggsTools 2HDM 分析启动器
# 自动处理 libstdc++ 环境问题

set -e

export LD_PRELOAD="/lib/x86_64-linux-gnu/libstdc++.so.6"
export LD_LIBRARY_PATH="/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# 如果没有参数，显示帮助信息
if [ $# -eq 0 ]; then
    python3 << 'PYTHON_EOF'
print("""
╔════════════════════════════════════════════════════════════════╗
║        HiggsTools 2HDM 顶刊级分析工具启动器                  ║
╚════════════════════════════════════════════════════════════════╝

用法: bash run_higgstools.sh [命令] [参数...]

命令:
  test              - 快速测试 (10×10 点)
  full              - 完整扫描 (60×60 点，顶刊级质量)
  custom n m [mHp]  - 自定义扫描
                      n    = tan(β) 点数
                      m    = sin(β-α) 点数
                      mHp  = 带电 Higgs 质量 (可选，默认 350 GeV)
  replot            - 从已保存结果重新绘图

示例:
  bash run_higgstools.sh test                  # 快速测试
  bash run_higgstools.sh full                  # 完整扫描
  bash run_higgstools.sh custom 40 40 400      # 自定义 40×40 点, mH±=400 GeV
  bash run_higgstools.sh replot                # 重新绘图

环境:
  已自动配置 libstdc++ 兼容性
  Python 版本: $(python3 --version)
  libstdc++ 版本: $(strings /lib/x86_64-linux-gnu/libstdc++.so.6 | grep CXXABI | tail -1)
""")
PYTHON_EOF
    exit 0
fi

# 运行 Python 脚本
exec python3 "$( cd "$(dirname "${BASH_SOURCE[0]}")" && pwd )/main.py" "$@"
