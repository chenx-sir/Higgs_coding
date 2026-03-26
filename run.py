#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速运行脚本 - HiggsTools 2HDM 分析
已自动处理 libstdc++ 环境问题
"""

import os
import sys

# ==================== 环境配置 ====================
# 修复 libstdc++ 兼容性问题
os.environ["LD_PRELOAD"] = "/lib/x86_64-linux-gnu/libstdc++.so.6"
os.environ["LD_LIBRARY_PATH"] = "/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:" + os.environ.get("LD_LIBRARY_PATH", "")

from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入分析模块
from higgstools_2hdm_analysis import (
    HiggsToolsAnalyzer, 
    CONFIG,
    main as run_full_analysis
)


def quick_test():
    """快速测试（用较少的点来验证代码)"""
    print("\n【快速测试模式】")
    print("使用较少扫描点来测试代码...")
    
    config = CONFIG.copy()
    config["SCAN_POINTS"] = (10, 10)  # 仅 100 个点用于测试
    
    print(f"测试配置: {config['SCAN_POINTS'][0]}×{config['SCAN_POINTS'][1]} = {config['SCAN_POINTS'][0]*config['SCAN_POINTS'][1]} 点")
    
    analyzer = HiggsToolsAnalyzer(config=config)
    analyzer.run_parameter_scan()
    analyzer.save_results()
    
    # 绘制所有图表
    analyzer.plot_2d_contours()
    analyzer.plot_1d_profiles()
    analyzer.plot_hb_exclusion()
    analyzer.plot_chi2_distribution()
    analyzer.plot_coupling_heatmap()
    analyzer.plot_constraints_comparison()
    analyzer.plot_best_fit_region()
    
    analyzer.generate_summary_report()


def full_scan():
    """完整的顶刊级扫描"""
    print("\n【完整扫描模式】")
    run_full_analysis()


def custom_scan(n_tanb=30, n_sinba=30, mHp=350.0):
    """自定义扫描参数"""
    print(f"\n【自定义扫描模式】")
    print(f"配置: {n_tanb}×{n_sinba} 点, mH± = {mHp} GeV")
    
    config = CONFIG.copy()
    config["SCAN_POINTS"] = (n_tanb, n_sinba)
    config["MHp"] = mHp
    
    analyzer = HiggsToolsAnalyzer(config=config)
    analyzer.run_parameter_scan()
    analyzer.save_results()
    
    # 绘制所有图表
    analyzer.plot_2d_contours()
    analyzer.plot_1d_profiles()
    analyzer.plot_hb_exclusion()
    analyzer.plot_chi2_distribution()
    analyzer.plot_coupling_heatmap()
    analyzer.plot_constraints_comparison()
    analyzer.plot_best_fit_region()
    
    analyzer.generate_benchmark_table()
    analyzer.generate_summary_report()


def reload_and_plot():
    """从已保存的结果重新绘图"""
    print("\n【重新绘图模式 - 从已保存结果】")
    
    import pickle
    import numpy as np
    from pathlib import Path
    
    output_dir = Path(CONFIG["OUTPUT_DIR"])
    pkl_file = output_dir / "results.pkl"
    
    if not pkl_file.exists():
        print(f"错误: 未找到已保存的结果 ({pkl_file})")
        print("请先运行扫描: python run.py full")
        return
    
    with open(pkl_file, "rb") as f:
        data = pickle.load(f)
    
    df = data["df"]
    config = data["config"]
    scan_params = data["scan_params"]
    
    # 重新创建分析器
    analyzer = HiggsToolsAnalyzer(config=config)
    analyzer.df = df
    analyzer.results = df.to_dict("records")
    analyzer.scan_params = scan_params
    
    print(f"已加载 {len(df)} 个扫描点")
    
    # 重新生成所有图表
    analyzer.plot_2d_contours()
    analyzer.plot_1d_profiles()
    analyzer.plot_hb_exclusion()
    analyzer.plot_chi2_distribution()
    analyzer.plot_coupling_heatmap()
    analyzer.plot_constraints_comparison()
    analyzer.plot_best_fit_region()
    analyzer.generate_benchmark_table()
    analyzer.generate_summary_report()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="HiggsTools 2HDM Type-I 分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例子:
  python run.py test              # 快速测试 (10×10 点)
  python run.py full              # 完整扫描 (60×60 点)
  python run.py custom 30 30 350  # 自定义扫描 (30×30 点, mH±=350 GeV)
  python run.py replot            # 从已保存结果重新绘图
        """
    )
    
    parser.add_argument(
        "mode",
        choices=["test", "full", "custom", "replot"],
        help="运行模式"
    )
    parser.add_argument(
        "--n-tanb", type=int, default=30,
        help="tan(β) 扫描点数 (自定义模式)"
    )
    parser.add_argument(
        "--n-sinba", type=int, default=30,
        help="sin(β-α) 扫描点数 (自定义模式)"
    )
    parser.add_argument(
        "--mHp", type=float, default=350.0,
        help="带电 Higgs 质量 (GeV)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "test":
        quick_test()
    elif args.mode == "full":
        full_scan()
    elif args.mode == "custom":
        custom_scan(args.n_tanb, args.n_sinba, args.mHp)
    elif args.mode == "replot":
        reload_and_plot()
