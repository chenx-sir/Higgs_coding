#!/usr/bin/env python3
"""HiggsTools 2HDM 分析启动器 - 自动处理环境"""

import os
import sys

# 在导入任何其他模块之前，修复环境
os.environ["LD_PRELOAD"] = "/lib/x86_64-linux-gnu/libstdc++.so.6"
os.environ["LD_LIBRARY_PATH"] = "/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:" + os.environ.get("LD_LIBRARY_PATH", "")

if __name__ == "__main__":
    # 现在才导入主模块
    from run import *
    
    if len(sys.argv) == 1:
        print("使用方法: python main.py [test|full|custom|replot]")
        print("示例:")
        print("  python main.py test              # 快速测试")
        print("  python main.py full              # 完整扫描")
        print("  python main.py custom 40 40 350  # 自定义参数")
        print("  python main.py replot            # 重新绘图")
        sys.exit(0)
    
    mode = sys.argv[1]
    
    if mode == "test":
        quick_test()
    elif mode == "full":
        full_scan()
    elif mode == "custom":
        n_tanb = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        n_sinba = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        mHp = float(sys.argv[4]) if len(sys.argv) > 4 else 350.0
        custom_scan(n_tanb, n_sinba, mHp)
    elif mode == "replot":
        reload_and_plot()
    else:
        print(f"未知模式: {mode}")
        sys.exit(1)
