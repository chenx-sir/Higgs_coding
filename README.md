#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HiggsTools 2HDM Type-I 顶刊级分析 - 快速入门指南
================================================

此脚本提供了完整的 HiggsTools 2HDM 限制分析框架，适用于投稿到 JHEP / Phys. Rev. D 等顶刊。
"""

# ==================== 【1】快速开始 ====================

print("""
╔════════════════════════════════════════════════════════════════╗
║     HiggsTools 2HDM Type-I 顶刊级分析工具 - 快速开始         ║
╚════════════════════════════════════════════════════════════════╝

【基本用法】

1. 快速测试（推荐先用这个验证环境）
   $ python run.py test
   → 运行 10×10 = 100 个点的小规模测试
   → 验证代码和 HiggsTools 安装是否正常

2. 完整扫描（顶刊级）
   $ python run.py full
   → 运行 60×60 = 3600 个点的完整扫描
   → 适合投稿结果（~1-2 小时，取决于硬件）

3. 自定义扫描
   $ python run.py custom --n-tanb 40 --n-sinba 40 --mHp 400
   → 自定义扫描点数和带电 Higgs 质量
   
4. 重新绘图（不需要重新计算）
   $ python run.py replot
   → 从已保存的结果快速重新生成所有图表

【输出文件说明】

highstools_2hdm_results/
├── scan_results.csv              ← 完整扫描数据（CSV 格式）
├── scan_data.npz                 ← 压缩数据（高效加载）
├── results.pkl                   ← Python pickle 格式（保留所有信息）
├── metadata.json                 ← 元数据和扫描配置
├── contours_2d.pdf               ← 主要结果图：2D χ² 轮廓
├── contours_2d.png               ← PNG 版本（预览用）
├── profiles_1d.pdf               ← 1D 轮廓似然（tan β 和 sin(β-α)）
├── hb_exclusion.pdf              ← HiggsBounds 允许/排除区域
├── benchmark_table.tex           ← LaTeX 基准点表（直接复制到论文）
├── analysis_report.txt           ← 分析总结报告
└── README.md                     ← 生成的方法说明

【论文中使用结果的建议】

1. 主要结果图：
   - 使用 contours_2d.pdf，显示 χ² 轮廓和 HiggsBounds 约束
   - 可在 caption 中说明：
     "Allowed parameter space at 68% and 95% CL from HiggsSignals,
      with theoretical constraints from HiggsBounds shown by red shading"

2. 基准点表格：
   - benchmark_table.tex 可直接粘贴到 LaTeX 文件中
   - 包含最佳拟合的几个典型点

3. 数据可用性声明：
   - 完整扫描数据保存在 scan_results.csv
   - 可在附录或 supplementary materials 中提供

4. 方法部分参考文献：
   - 引用 HiggsTools: https://higgsbounds.gitlab.io/higgstools/
   - P. Bechtle et al., Comput. Phys. Commun. 181 (2010) 138
   - P. Bechtle et al., Comput. Phys. Commun. 191 (2015) 52
""")


# ==================== 【2】关键参数说明 ====================

print("""
【可配置参数详解】

在 higgstools_2hdm_analysis.py 的 CONFIG 字典中修改：

1. 数据路径（必填）
   HB_DATA: HiggsBounds 数据文件路径
   HS_DATA: HiggsSignals 数据文件路径
   
2. 物理参数
   MH_REF = 125.09        → 参考 Higgs 质量（建议固定为 125.09）
   MHp = 350.0            → 带电 Higgs 质量（可根据模型变化）
   
3. 扫描范围
   TANB_RANGE = (0.5, 30.0)      → tan(β) 的范围
   SINBA_RANGE = (0.1, 1.0)      → sin(β-α) 的范围
   SCAN_POINTS = (60, 60)        → 扫描点数（推荐 50-100）
   
4. 置信水平
   CL_68 = 2.3                   → 68% 置信水平的 χ² 阈值
   CL_95 = 5.99                  → 95% 置信水平的 χ² 阈值
   
5. 输出选项
   OUTPUT_DIR = "..."            → 输出目录名称
   ATLAS_STYLE = True            → 是否使用 ATLAS 绘图风格

【常见修改案例】

案例 1: 扫描不同的带电 Higgs 质量
  config["MHp"] = 500.0        # 改为 500 GeV
  config["OUTPUT_DIR"] = "results_mHp500"
  analyzer = THDM2HDMAnalyzer(config=config)
  analyzer.run_parameter_scan()

案例 2: 精细扫描（发论文用）
  config["SCAN_POINTS"] = (100, 100)  # 1 万个点
  # 注意：会需要 2-3 小时计算

案例 3: 扩展扫描范围
  config["TANB_RANGE"] = (0.1, 100.0)   # 更大的范围
  config["SINBA_RANGE"] = (0.01, 1.0)   # 包括更小的 sin(β-α)
  
案例 4: 只看 alignment limit
  config["SINBA_RANGE"] = (0.95, 1.0)   # sin(β-α) 接近 1

""")


# ==================== 【3】常见问题解决 ====================

print("""
【常见问题 (FAQ)】

Q1: 代码运行报错 "ModuleNotFoundError: No module named 'Higgs'"
→ 检查 HiggsTools 是否正确安装
  $ python -c "import Higgs; print(Higgs.__version__)"
  如果报错，参考官方文档重新安装

Q2: HiggsBounds/HiggsSignals 初始化很慢
→ 这是正常的，首次加载数据文件可能需要 30 秒
  后续使用会更快

Q3: 某个扫描点的 χ² 计算失败
→ 代码已处理，会输出 NaN，并在日志中显示警告
  通常是参数空间边界的数值问题

Q4: 如何限制只计算某个参数范围?
→ 修改 CONFIG 中的 TANB_RANGE 和 SINBA_RANGE
  或在代码中调用:
  tanb_vals = np.linspace(1.0, 10.0, 50)  # 只计算 1 < tan β < 10
  analyzer.run_parameter_scan(tanb_vals=tanb_vals)

Q5: 如何添加其他物理限制?
→ 在 run_parameter_scan() 中修改结果字典，添加新列
  例如：results.append({..., "extra_limit": value})

Q6: 图表太大/太小，如何调整?
→ 修改绘图函数中的 figsize 参数
  例：fig, ax = plt.subplots(figsize=(12, 10))  # 更大

Q7: 如何导出为其他格式（PNG、LaTeX）?
→ 代码已支持 PDF 和 PNG
  修改保存格式：plt.savefig(..., format='eps')

Q8: 如何并行计算以加快速度?
→ 修改 run_parameter_scan() 使用 multiprocessing 或 joblib
  这是一个高级使用案例

""")


# ==================== 【4】论文写作建议 ====================

print("""
【论文写作建议】

方法部分框架：
-----------
"We constrain the 2HDM Type-I parameter space using the HiggsTools 
framework, which combines HiggsSignals (fit to Higgs measurements) 
and HiggsBounds (theoretical and experimental constraints).

We perform a parameter scan in the (tan β, sin(β-α)) plane with 
{n_points} points, covering tan β ∈ [{tanb_min}, {tanb_max}] and 
sin(β-α) ∈ [{sinba_min}, {sinba_max}]. The reference Higgs mass is 
set to {mH} GeV, and the charged Higgs mass to {mHp} GeV.

Results are presented as profile likelihoods in terms of Δχ², with 
68% and 95% confidence level contours. The allowed parameter space 
is further constrained by theoretical consistency and LHC experimental 
limits implemented in HiggsBounds."

结果部分框架：
-----------
"Figure {X} shows the allowed parameter space at 68% and 95% CL from 
HiggsSignals (green and yellow regions), with experimental constraints 
from HiggsBounds (red shading indicates excluded regions). The best-fit 
point is marked by a red star, corresponding to...

The profile likelihood scans in Figure {Y} show the one-dimensional 
constraints on tan β and sin(β-α). At 95% CL, we find...
tan β < {value}  or  sin(β-α) > {value}"

表格框架：
--------
使用 benchmark_table.tex 中的表格，caption 示例：
"Benchmark points in the 2HDM Type-I parameter space consistent with 
all constraints at 95% CL. The Δχ² values are relative to the best fit."

补充材料：
--------
- 提供 scan_results.csv 作为附录
- 说明：CSV 包含所有扫描点的 tan β, sin(β-α), χ², HiggsBounds 结果

引用文献：
--------
[1] P. Bechtle et al., Comput. Phys. Commun. 181 (2010) 138, 1102.1898
[2] P. Bechtle et al., Comput. Phys. Commun. 191 (2015) 52, 1502.04199
[3] HiggsTools: https://higgsbounds.gitlab.io/higgstools/

""")


# ==================== 【5】预期输出 ====================

print("""
【预期输出示例】

扫描将输出类似信息：

[初始化] 加载 HiggsTools...
[初始化] HiggsTools 加载完成

[扫描] 参数空间扫描配置：
    tan(β): 0.50 - 30.00 (60 点)
    sin(β-α): 0.10 - 1.00 (60 点)
    总点数: 3600
    mH±: 350.0 GeV

[扫描] 启动 HiggsTools 扫描...
tan(β): 100%|███████| 60/60
sin(β-α): 100%|███████| 3600/3600  [~60 min on Intel i7]

[扫描] 完成！扫描点数: 3600
    χ²_min = 0.342
    χ²_max = 287.543
    HiggsBounds 允许: 1842 点
    HiggsBounds 排除: 1758 点

[输出] 保存数据...
    ✓ CSV: higgstools_2hdm_results/scan_results.csv
    ✓ 压缩数据: higgstools_2hdm_results/scan_data.npz
    ✓ Pickle: higgstools_2hdm_results/results.pkl
    ✓ 元数据: higgstools_2hdm_results/metadata.json

[绘图] 生成 2D 轮廓图...
    ✓ /path/to/contours_2d.pdf
    ✓ /path/to/contours_2d.png

[绘图] 生成 1D 轮廓图...
    ✓ /path/to/profiles_1d.pdf

[分析] 生成基准点表格...
    ✓ LaTeX 表格: /path/to/benchmark_table.tex

╔════════════════════════════════════════════════════════════════╗
║        HiggsTools 2HDM Type-I 分析总结报告                    ║
╚════════════════════════════════════════════════════════════════╝

【扫描配置】
  - 参数空间: tan(β) ∈ [0.50, 30.00]
  - 参数空间: sin(β-α) ∈ [0.10, 1.00]
  - 总扫描点数: 3600

【最佳拟合点】
  - tan(β) = 2.3456
  - sin(β-α) = 0.9876
  - χ² = 0.342
  - HiggsBounds 允许: ✓

【约束结果】
  - 68% CL 置信区域: 892 点
  - 95% CL 置信区域: 1842 点
  - HiggsBounds 排除: 1758 点 (48.8%)

✓ 分析完成！所有结果已保存到: higgstools_2hdm_results/
""")


# ==================== 【6】高级技巧 ====================

print("""
【高级技巧】

技巧 1: 批量运行多个 mHp 值
------
for mHp_val in [300, 350, 400, 500]:
    config = CONFIG.copy()
    config["MHp"] = mHp_val
    config["OUTPUT_DIR"] = f"results_mHp{mHp_val}"
    analyzer = THDM2HDMAnalyzer(config=config)
    analyzer.run_parameter_scan()
    analyzer.save_results()

技巧 2: 生成动画对比不同参数
------
import matplotlib.animation as animation
# 为多个 mHp 值的结果生成轮廓变化动画

技巧 3: 统计学分析（Feldman-Cousins）
------
df = pd.read_csv("scan_results.csv")
# 应用 Feldman-Cousins 方法得到正确的置信区间
# （需要自己实现或调用 scipy 统计库）

技巧 4: 与其他模型对比
------
# 在同一图上绘制不同模型的约束
# 例：Type-I vs Type-II vs Type-X vs Type-Y

技巧 5: 贝叶斯统计分析
------
# 使用 pymc 或 emcee 进行贝叶斯参数推断
# （更高级的分析）

""")

print("\n✓ 快速入门指南完成！\n")
print("【下一步】")
print("1. 检查 HiggsTools 安装: python -c \"import Higgs; print('OK')\"")
print("2. 运行快速测试: python run.py test")
print("3. 查看 highstools_2hdm_analysis.py 中的 CONFIG 配置")
print("4. 根据需要修改参数后运行完整扫描: python run.py full")
print("\n有问题? 查看 HiggsTools 官方文档: https://higgsbounds.gitlab.io/higgstools/")
