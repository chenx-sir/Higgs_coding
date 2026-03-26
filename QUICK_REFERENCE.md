# HiggsTools 2HDM 可视化 - 快速参考

## 📊 7 个完整生成的图表

| 图表 | 子图数 | 大小 | 标签 | 状态 |
|------|--------|------|------|------|
| contours_2d.png | 1 | 61K | — | ✓ |
| profiles_1d.png | 2 | 60K | (a,b) | ✓ |
| hb_exclusion.png | 1 | 37K | — | ✓ |
| chi2_analysis.png | 4 | 215K | (a,b,c,d) | ✓ |
| coupling_heatmap.png | 2 | 62K | (a,b) | ✓ |
| constraints_comparison.png | 4 | 154K | (a,b,c,d) | ✓ |
| best_fit_details.png | 4 | 195K | (a,b,c,d) | ✓ |

**总大小**: 784K (所有 PNG)

---

## 🎨 统一风格特性

✓ **白色背景** - 所有图表  
✓ **灰色网格线** - alpha=0.2, 实线, 0.5pt  
✓ **粗体字体** - 所有标签和标题  
✓ **专业图例** - 黑色边框, 方形  
✓ **子图标签** - (a,b,c,d) 左上角, 白色背景  

---

## 📌 物理参数

```
最佳拟合:
  tan(β) = 47.6982
  sin(β-α) = 0.9818
  χ² = 164.587

置信区域:
  68% CL: 213 点
  95% CL: 323 点
  
约束:
  HiggsBounds 排除: 12.4%
```

---

## 🚀 快速再生成

```bash
# 重新生成所有图表
cd /home/chenxsir/thesis1
bash run_higgstools.sh full

# 只验证代码
python -m py_compile higgstools_2hdm_analysis.py
```

---

## 📝 代码位置

- **主脚本**: `higgstools_2hdm_analysis.py`
- **执行脚本**: `run_higgstools.sh`
- **输出目录**: `higgstools_2hdm_results/`

---

## 🔧 修改点汇总

**7 个修改的绘图函数**:
1. `plot_2d_contours()` ← 早期修改 (出版质量)
2. `plot_1d_profiles()` ← (a,b) 标签
3. `plot_hb_exclusion()` ← 白色背景 + 粗体
4. `plot_chi2_distribution()` ← (a,b,c,d) 标签
5. `plot_coupling_heatmap()` ← (a,b) 标签
6. `plot_constraints_comparison()` ← (a,b,c,d) 标签
7. `plot_best_fit_region()` ← (a,b,c,d) 标签

---

## ✅ 质量检查清单

- [x] 所有 7 个图表生成
- [x] 代码通过句法检查
- [x] 脚本执行成功 (退出码=0)
- [x] 物理结果一致
- [x] 子图标签到位
- [x] 颜色/格式统一
- [x] 文件大小正常
- [x] 可用于发表

---

## 📖 发表建议

**主图**: contours_2d.pdf → 2D 置信区域  
**补充**: profiles_1d.pdf, chi2_analysis.pdf  
**附录**: 其他 4 个图表  

---

**项目完成**: 2026-03-24  
**发布就绪**: ✓ YES

