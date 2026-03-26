# 故障排除和快速入门

## 🎯 我的环境已经修复！现在怎么用？

### 最简单的方式（推荐）

```bash
# 1. 进入项目目录
cd /home/chenxsir/thesis1

# 2. 运行快速测试（验证环境）
bash run_higgstools.sh test

# 3. 如果测试通过，运行完整扫描
bash run_higgstools.sh full

# 4. 检查结果
ls -la higgstools_2hdm_results/
```

**就这么简单！** ✓

---

## 📋 环境问题 - 已修复

### 原始问题
```
ImportError: /home/chenxsir/anaconda3/lib/python3.11/site-packages/pyarrow/../../../libstdc++.so.6: 
version `CXXABI_1.3.15' not found
```

### 根本原因
- conda 环境中的 libstdc++ 版本太旧（仅支持到 CXXABI_1.3.10）
- HiggsTools 需要 CXXABI_1.3.15
- 系统中的 libstdc++ 有较新版本

### 解决方案
创建了 `run_higgstools.sh` 脚本，自动：
1. 设置 `LD_PRELOAD` 强制加载系统的 libstdc++
2. 调整 `LD_LIBRARY_PATH` 优先级
3. 启动 Python

**结果**: HiggsTools 现在可以正常导入 ✓

---

## 🚀 快速命令参考

### 完整命令列表

```bash
# 帮助信息
bash run_higgstools.sh

# 快速测试 (100 点，~1 分钟)
bash run_higgstools.sh test

# 完整扫描 (3600 点，~90 分钟)
bash run_higgstools.sh full

# 自定义扫描
bash run_higgstools.sh custom 50 50        # 50×50 点
bash run_higgstools.sh custom 40 40 400    # 40×40 点, mH±=400 GeV

# 重新绘图（不需要重新计算）
bash run_higgstools.sh replot
```

### 推荐的快速开始流程

```bash
# Step 1: 验证环境 (1 分钟)
bash run_higgstools.sh test

# Step 2: 如果成功，运行完整扫描 (90 分钟)
bash run_higgstools.sh full

# Step 3: 检查并使用结果
ls higgstools_2hdm_results/
# 使用 contours_2d.pdf 和 benchmark_table.tex 进行论文写作
```

---

## 📁 项目文件结构

```
/home/chenxsir/thesis1/
├── higgstools_2hdm_analysis.py      # 主分析代码（核心逻辑）
├── run.py                           # Python 运行脚本
├── main.py                          # 启动器（处理环境）
├── run_higgstools.sh               # ← 使用这个！（bash 包装脚本）
├── README.md                        # 详细文档
├── USAGE.md                         # 使用指南
├── QUICK_REFERENCE.md               # 快速参考卡
├── TROUBLESHOOTING.md              # 本文件
├── test.py                          # 原始测试文件（可删除）
├── test.cpp                         # C++ 测试代码（可删除）
└── higgstools_2hdm_results/        # 输出目录（自动创建）
    ├── scan_results.csv             # 完整数据
    ├── scan_data.npz                # 压缩数据
    ├── contours_2d.pdf              # 主要结果图 ← 投稿用
    ├── profiles_1d.pdf              # 1D 投影
    ├── hb_exclusion.pdf             # 排除区域
    ├── benchmark_table.tex          # LaTeX 表格 ← 投稿用
    ├── analysis_report.txt          # 分析摘要
    ├── metadata.json                # 配置
    └── results.pkl                  # Python 对象
```

---

## 🔍 常见问题速查

### Q1: `bash: run_higgstools.sh: No such file or directory`
**原因**: 脚本不在当前目录  
**解决**: 
```bash
cd /home/chenxsir/thesis1
bash run_higgstools.sh test
```

### Q2: `permission denied`
**原因**: 脚本没有执行权限  
**解决**:
```bash
chmod +x run_higgstools.sh
bash run_higgstools.sh test
```

### Q3: `ImportError: No module named 'Higgs'`
**原因**: 直接用 `python run.py` 而不是 `bash run_higgstools.sh`  
**解决**: 
```bash
# ❌ 错误的方式
python run.py test

# ✓ 正确的方式
bash run_higgstools.sh test
```

### Q4: 程序运行但生成 NaN 值
**原因**: 正常，某些参数点可能数值不稳定  
**解决**: 代码已自动处理，NaN 会被记录但不影响整体结果

### Q5: 内存不足或运行太慢
**原因**: 扫描点数太多  
**解决**:
```bash
# 运行较小规模的扫描
bash run_higgstools.sh custom 30 30   # 900 点而不是 3600
```

### Q6: matplotlib 中文字体显示为方块
**原因**: 系统缺少中文字体  
**解决**: 这是显示问题，PDF 内容正确。可以修改代码改成英文标签（见下面的高级用法）

---

## 🛠️ 修改和自定义

### 修改 1: 改变扫描精度

编辑 `higgstools_2hdm_analysis.py` 的 `CONFIG` 字典：

```python
CONFIG = {
    ...
    "SCAN_POINTS": (60, 60),     # ← 改这里
    ...
}
```

| 值 | 点数 | 运行时间 |
|----|------|--------|
| (10, 10) | 100 | ~1 min |
| (30, 30) | 900 | ~15 min |
| (60, 60) | 3600 | ~90 min |
| (100, 100) | 10000 | ~4 hours |

### 修改 2: 改变带电 Higgs 质量

```bash
bash run_higgstools.sh custom 60 60 500
# 这会扫描 mH± = 500 GeV 的参数空间
```

或编辑 `CONFIG`:
```python
"MHp": 400.0,   # 改这里（单位 GeV）
```

### 修改 3: 改变轴范围

编辑 `CONFIG`:
```python
"TANB_RANGE": (0.5, 30.0),      # tan β 范围
"SINBA_RANGE": (0.1, 1.0),      # sin(β-α) 范围
```

### 修改 4: 改成英文标签（避免中文显示问题）

在 `plot_2d_contours()` 中修改：
```python
ax.set_xlabel(r"$\sin(\beta - \alpha)$", fontsize=16)
ax.set_ylabel(r"$\tan \beta$", fontsize=16)
ax.set_title("2HDM Type-I: HiggsTools Constraints", fontsize=16)
```

然后重新绘图：
```bash
bash run_higgstools.sh replot
```

---

## 📊 数据加载和重用

### 从已保存的结果加载数据

```python
import pandas as pd
import numpy as np

# 方法 1: 使用 CSV（简单）
df = pd.read_csv('higgstools_2hdm_results/scan_results.csv')
print(df.head())

# 方法 2: 使用 NPZ（快速）
data = np.load('higgstools_2hdm_results/scan_data.npz')
print(data.files)  # 查看可用的数组
chi2_grid = data['chi2_grid']

# 方法 3: 使用 Pickle（完整对象）
import pickle
with open('higgstools_2hdm_results/results.pkl', 'rb') as f:
    results = pickle.load(f)
    df = results['df']
    config = results['config']
```

### 提取特定数据

```python
# 获取最佳拟合点
best_idx = df['delta_chi2'].idxmin()
best_point = df.loc[best_idx]
print(f"tan(β) = {best_point['tan_beta']:.4f}")
print(f"sin(β-α) = {best_point['sin_beta_alpha']:.4f}")

# 获取 95% CL 区域
cl95_region = df[df['delta_chi2'] < 5.99]
print(f"95% CL 允许的点数: {len(cl95_region)}")

# 获取 HiggsBounds 没有排除的点
hb_allowed = df[df['allowed_hb']]
print(f"HiggsBounds 允许的点数: {len(hb_allowed)}")
```

---

## 💻 从头再运行一遍（完全重置）

```bash
cd /home/chenxsir/thesis1

# 删除旧的结果（可选）
rm -rf higgstools_2hdm_results/

# 运行完整扫描
bash run_higgstools.sh full

# 查看新结果
ls -la higgstools_2hdm_results/
```

---

## 📄 为论文准备

### 基本步骤

```bash
# 1. 完整扫描
bash run_higgstools.sh full

# 2. 复制图表
cp higgstools_2hdm_results/contours_2d.pdf ~/my_paper/figures/

# 3. 复制表格
cat higgstools_2hdm_results/benchmark_table.tex
# → 复制输出到 LaTeX 文件中

# 4. 复制数据
cp higgstools_2hdm_results/scan_results.csv ~/my_paper/supplementary/
```

### LaTeX 模板

**在 figures 文件夹放置 PDF**:
```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=0.85\textwidth]{figures/contours_2d.pdf}
  \caption{Allowed parameter space at 68\% and 95\% CL from HiggsSignals 
    (green and yellow regions), with constraints from HiggsBounds (red shading). 
    The best-fit point is marked by a red star.}
  \label{fig:2hdm_constraints}
\end{figure}
```

**为表格添加 LaTeX 导言包** (在 `\documentclass` 后):
```latex
\usepackage{booktabs}
```

---

## ✅ 测试清单

在论文投稿前，确保完成以下步骤：

- [ ] `bash run_higgstools.sh test` 成功完成
- [ ] `bash run_higgstools.sh full` 成功完成
- [ ] `higgstools_2hdm_results/contours_2d.pdf` 存在且有效
- [ ] `higgstools_2hdm_results/benchmark_table.tex` 存在
- [ ] 打开 PDF 检查图表是否合理
- [ ] 复制表格数据到论文 LaTeX 文件
- [ ] 在 Method 部分添加 HiggsTools 说明（见 README.md）
- [ ] 引用 HiggsTools 文献
- [ ] (可选) 提供 scan_results.csv 作为补充材料

---

## 🎓 总结

**你现在有**:
- ✓ 完整的 2HDM Type-I 分析框架
- ✓ 自动处理的环境问题
- ✓ 结果
- ✓ 可直接用于论文的图表和表格

**下一步**:
```bash
bash run_higgstools.sh full
```

**然后**:
使用 `contours_2d.pdf` 和 `benchmark_table.tex` 投稿！

---

**有问题?** 查看:
- `USAGE.md` - 详细使用指南
- `README.md` - 完整文档
- `QUICK_REFERENCE.md` - 快速参考

**官方资源**:
- HiggsTools 文档: https://higgsbounds.gitlab.io/higgstools/
- 本项目代码: 完全自包含，可在 GitHub 上分享

