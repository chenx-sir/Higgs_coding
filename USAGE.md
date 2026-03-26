# HiggsTools 2HDM 顶刊级分析 - 使用指南

## 🚀 快速开始

### 环境问题已修复

原始问题：libstdc++ 版本不兼容 (CXXABI_1.3.15 缺失)  
解决方案：已自动处理，通过 `run_higgstools.sh` 脚本加载系统库

### 基本使用

```bash
# 快速测试（推荐先试这个）
bash run_higgstools.sh test

# 完整扫描（顶刊级质量）
bash run_higgstools.sh full

# 自定义扫描
bash run_higgstools.sh custom 40 40 350

# 无参数显示帮助
bash run_higgstools.sh
```

## 📋 详细命令说明

### 1. 快速测试 (10×10 点)
```bash
bash run_higgstools.sh test
```
- 用于快速验证环境是否正确设置
- 产生 100 个扫描点
- 运行时间: ~1 分钟
- 输出: 完整的功能测试结果

### 2. 完整扫描 (60×60 点)
```bash
bash run_higgstools.sh full
```
- **顶刊级质量**（适合投稿到 JHEP / Phys. Rev. D）
- 3600 个扫描点
- 运行时间: ~90 分钟（取决于硬件）
- 输出: 所有分析结果

### 3. 自定义扫描
```bash
bash run_higgstools.sh custom 40 40 350
```
参数说明:
- 第一个数字: tan(β) 扫描点数
- 第二个数字: sin(β-α) 扫描点数
- 第三个数字 (可选): 带电 Higgs 质量 (GeV)，默认 350

### 4. 重新绘图
```bash
bash run_higgstools.sh replot
```
- 从已保存的结果重新生成所有图表
- **不需要重新计算**，速度很快
- 用于修改绘图参数后快速看效果

## 📊 输出文件

所有结果保存在 `higgstools_2hdm_results/` 目录下：

| 文件 | 说明 | 用途 |
|-----|------|------|
| `scan_results.csv` | 完整扫描数据 | 数据分析，作为附录 |
| `scan_data.npz` | 压缩格式 | Python 重新加载 |
| `contours_2d.pdf` | **主要结果图** | ✓ 投稿论文中的 Figure |
| `profiles_1d.pdf` | 1D 投影 | 补充图表 |
| `hb_exclusion.pdf` | 排除区域 | 理论约束说明 |
| `benchmark_table.tex` | LaTeX 表格 | ✓ 直接粘贴到论文 Table |
| `analysis_report.txt` | 分析摘要 | 方法部分参考 |
| `metadata.json` | 扫描配置 | 重现性记录 |

## 📝 为论文做准备

### 第 1 步：运行完整扫描
```bash
bash run_higgstools.sh full
```

### 第 2 步：检查结果
- 用 PDF 查看器打开 `contours_2d.pdf`
- 检查 χ² 轮廓是否合理
- 验证 HiggsBounds 约束区域

### 第 3 步：准备论文文件

**Figure （使用 contours_2d.pdf）**
```latex
\begin{figure}
  \centering
  \includegraphics[width=0.8\textwidth]{contours_2d.pdf}
  \caption{Allowed parameter space at 68\% and 95\% CL from HiggsSignals 
    (green and yellow regions), with theoretical constraints from 
    HiggsBounds (red shading). The best-fit point is marked by a red star.}
  \label{fig:constraints}
\end{figure}
```

**Table （使用 benchmark_table.tex）**
```bash
cat higgstools_2hdm_results/benchmark_table.tex
```
直接复制输出到你的 LaTeX 文件

**Method 部分模板**（见 README.md 中的建议）

### 第 4 步：提供补充材料
- 将 `scan_results.csv` 作为附录或 GitHub 仓库
- 在论文中添加数据可用性声明：
  ```
  "Complete scan results are available in the supplementary material 
   (scan_results.csv) and at [GitHub URL]."
  ```

## 🔧 常见修改

### 改变扫描点数（精细化）
编辑 `higgstools_2hdm_analysis.py` 中的 `CONFIG`：

```python
CONFIG = {
    ...
    "SCAN_POINTS": (100, 100),  # 改为 1 万个点（精细扫描）
    ...
}
```

然后运行：
```bash
bash run_higgstools.sh full
```

### 改变带电 Higgs 质量
```bash
bash run_higgstools.sh custom 60 60 500
```
这会扫描带 mH± = 500 GeV 的参数空间

### 改变扫描范围
编辑 `CONFIG` 中的：
```python
"TANB_RANGE": (1.0, 50.0),      # 改变 tan β 范围
"SINBA_RANGE": (0.95, 1.0),     # 改变 sin(β-α) 范围
```

## 📊 预期输出示例

快速测试完成后会看到：

```
【扫描配置】
  - 参数空间: tan(β) ∈ [0.50, 30.00]
  - 参数空间: sin(β-α) ∈ [0.10, 1.00]
  - 总扫描点数: 100

【最佳拟合点】
  - tan(β) = 0.5000
  - sin(β-α) = 1.0000
  - χ² = 165.475
  - HiggsBounds 允许: ✓

【约束结果】
  - 68% CL 置信区域: 10 点
  - 95% CL 置信区域: 10 点
  - HiggsBounds 排除: 16 点 (16.0%)
```

## 🐛 故障排除

### Q: 运行时出现 "CXXABI_1.3.15 not found" 错误
**A:** 使用 `bash run_higgstools.sh` 而不是直接 `python run.py`

### Q: 初始化很慢
**A:** 这是正常的，HiggsTools 首次加载数据需要 30 秒。后续更快。

### Q: 某个点计算失败（看到 NaN）
**A:** 正常，代码已处理。通常是参数边界的数值问题。

### Q: 内存不足
**A:** 减少 `SCAN_POINTS` 或使用 `custom` 命令进行小规模扫描

### Q: 图表中文字乱码或缺失
**A:** 这是 matplotlib 字体问题，不影响功能。PDF 文件内容正确。

## 📚 参考资料

### 论文中引用
```bibtex
@article{Bechtle2010,
  title={HiggsBounds: Confronting arbitrary Higgs sectors with exclusion bounds from LEP and the Tevatron},
  author={Bechtle, Philip and others},
  journal={Computer Physics Communications},
  volume={181},
  pages={138--167},
  year={2010}
}

@article{Bechtle2015,
  title={HiggsTools: a program for evaluating Higgs-sector predictions of beyond the Standard Model theories},
  author={Bechtle, Philip and others},
  journal={Computer Physics Communications},
  volume={191},
  pages={52--70},
  year={2015}
}
```

### 官方文档
- HiggsTools: https://higgsbounds.gitlab.io/higgstools/
- 2HDM Type-I 的耦合定义参见论文中的方法部分

## 📈 进阶用法

### 保存为其他格式
```python
# 在 plot_2d_contours() 函数中修改
plt.savefig(..., format='eps')  # EPS 格式
plt.savefig(..., format='svg')  # SVG 格式
```

### 提取特定数据
```python
import pandas as pd
df = pd.read_csv('higgstools_2hdm_results/scan_results.csv')

# 获取最佳拟合点
best = df.loc[df['delta_chi2'].idxmin()]

# 获取 95% CL 区域
cl95_region = df[df['delta_chi2'] < 5.99]
```

### 对比多个 mHp 值
参考第 1 部分最后提供的"高级技巧"部分

## ✅ 投稿前检查清单

- [ ] 运行了 `bash run_higgstools.sh full`
- [ ] 检查了 `contours_2d.pdf` 的合理性
- [ ] 在 LaTeX 论文中插入了 Figure
- [ ] 复制了 `benchmark_table.tex` 中的表格
- [ ] 提供了 `scan_results.csv` 作为补充材料
- [ ] 在 Method 部分添加了 HiggsTools 说明
- [ ] 引用了 HiggsTools 文献
- [ ] 在 supplementary info 中包含了绘图代码（可选但推荐）

## 💡 建议

1. **第一次投稿**: 使用 `full` 模式（3600 点）- 这是标准的顶刊质量
2. **快速测试**: 总是先用 `test` 模式验证环境
3. **参数扫描**: 如需探索不同的 mHp 值，用 `custom` 命令
4. **图表复用**: 用 `replot` 快速调整绘图而不重新计算

---

**现在开始**：
```bash
bash run_higgstools.sh test
```

祝你顺利投稿！ 🎓
