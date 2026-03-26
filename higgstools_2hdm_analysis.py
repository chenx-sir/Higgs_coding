#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2HDM Type-I Parameter Space Constraint Analysis
================================================
Constrains the parameter space of Two-Higgs-Doublet Model (2HDM) Type-I
using HiggsSignals (χ² fit) and HiggsBounds (theoretical + experimental exclusions).

Author: [User]
Date: 2026
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplhep as hep
import Higgs.predictions as HP
import Higgs.bounds as HB
import Higgs.signals as HS
from tqdm import tqdm
import os
from pathlib import Path
import pickle
import json
from datetime import datetime

# ==================== Global Configuration ====================
CONFIG = {
    "HB_DATA": "/home/chenxsir/higgstools/data/HBDataSet",
    "HS_DATA": "/home/chenxsir/higgstools/data/HSDataSet",
    "OUTPUT_DIR": "higgstools_2hdm_results",
    "MH_REF": 125.09,           # Higgs reference mass (GeV)
    "MHp": 350.0,               # Charged Higgs mass (GeV)
    "SCAN_POINTS": (100, 100),  # (n_tanb, n_sinba) - high precision ~ 10000 points
    "TANB_RANGE": (0.5, 55.0),  # tan(β) range (hard limit=50, scan to 55 for exclusion display)
    "SINBA_RANGE": (0.1, 1.0),  # sin(β-α) range
    "CL_68": 2.3,               # χ² 68% CL threshold
    "CL_95": 5.99,              # χ² 95% CL threshold
    "ATLAS_STYLE": True,        # Use ATLAS style plotting
}

# Set plotting style
if CONFIG["ATLAS_STYLE"]:
    hep.style.use("ATLAS")
plt.rcParams.update({
    "font.sans-serif": ["DejaVu Sans"],  # English fonts only
    "font.size": 12,
    "axes.labelsize": 14,
    "axes.titlesize": 16,
    "legend.fontsize": 11,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "axes.unicode_minus": False,  # Display minus sign correctly
    "figure.dpi": 100,
})


class HiggsToolsAnalyzer:
    """2HDM Type-I parameter space analyzer using HiggsTools.
    
    Performs parameter space scan with HiggsSignals fit (χ²) and 
    HiggsBounds exclusion checks.
    """
    
    def __init__(self, config=CONFIG):
        """Initialize analyzer with configuration.
        
        Parameters
        ----------
        config : dict
            Configuration dictionary with HiggsTools paths and parameters.
        """
        self.config = config
        self.output_dir = Path(config["OUTPUT_DIR"])
        self.output_dir.mkdir(exist_ok=True)
        
        # Load HiggsTools database and analysis tools
        self.bounds = HB.Bounds(config["HB_DATA"])
        self.signals = HS.Signals(config["HS_DATA"])
        self.mh = config["MH_REF"]
        
        # Storage for scan results
        self.results = []
        self.scan_params = {}
        self.df = None
        
    def set_typeI_predictions(self, sinba, tanb, mHp=None):
        """Set up 2HDM Type-I predictions for HiggsTools analysis.
        
        Simplified model containing:
        - h (125 GeV): light CP-even neutral Higgs
        - H±: charged Higgs (constrained via theoretical bounds)
        
        Parameters
        ----------
        sinba : float
            sin(β - α) value (0 to 1)
        tanb : float
            tan(β) value
        mHp : float, optional
            Charged Higgs mass in GeV. If None, uses CONFIG["MHp"]
        
        Returns
        -------
        pred : Higgs.predictions.Predictions
            HiggsTools prediction object
        """
        if mHp is None:
            mHp = self.config["MHp"]
            
        pred = HP.Predictions()
        
        # Calculate angles (beta and alpha)
        beta = np.arctan(tanb)
        alpha = beta - np.arcsin(sinba)
        
        # Type-I effective coupling parameters
        kappa_f = np.cos(alpha) / np.sin(beta)
        kappa_V = sinba  # Vector coupling = sin(β-α)
        
        # ===== Physical Constraint Checks =====
        # 1. Vacuum stability hard upper bound for 2HDM Type-I
        # Reference: arXiv:1405.0181, 1512.04199
        # 即使在完美对齐（sin(β-α)=1），tan(β) > ~50-60 也面临问题
        hard_limit_ok = tanb < 50.0  # 绝对上界（即使对齐）
        
        # 2. 真空稳定性对对齐的要求（tan(β) 依存）
        alignment_requirement_ok = True
        if tanb >= 40:
            # tan(β) >= 40: requires near alignment (sin(β-α) > 0.98)
            if sinba < 0.98:
                alignment_requirement_ok = False
        elif tanb >= 25:
            # tan(β) >= 25: requires relatively close alignment (sin(β-α) > 0.95)
            if sinba < 0.95:
                alignment_requirement_ok = False
        elif tanb >= 10:
            # tan(β) >= 10: requires some degree of alignment (sin(β-α) > 0.90)
            if sinba < 0.90:
                alignment_requirement_ok = False
        
        # 3. Perturbativity（扰动性）检查
        combined_coupling = np.sqrt(kappa_f**2 + kappa_V**2)
        perturbative_ok = combined_coupling < 3.0  # Standard unitarity limit
        
        # If physical constraints violated, return invalid prediction
        if not hard_limit_ok or not alignment_requirement_ok or not perturbative_ok:
            # 返回虚拟预测对象（会导致 χ² 巨大，HiggsTools 排除）
            pred_invalid = HP.Predictions()
            h_invalid = pred_invalid.addParticle(HP.NeutralScalar("h", HP.CP.even))
            h_invalid.setMass(self.mh)
            # 设置无效的耦合（会导致 χ² → ∞）
            cpl_invalid = HP.NeutralEffectiveCouplings()
            cpl_invalid.tt = cpl_invalid.bb = cpl_invalid.tautau = 0.0
            cpl_invalid.WW = cpl_invalid.ZZ = 0.0
            cpl_invalid.gg = 0.0
            cpl_invalid.gamgam = 0.0
            HP.effectiveCouplingInput(h_invalid, cpl_invalid, reference=HP.ReferenceModel.SMHiggsEW)
            return pred_invalid
        
        # ===== Light CP-even Higgs (h, ~125 GeV) =====
        h = pred.addParticle(HP.NeutralScalar("h", HP.CP.even))
        h.setMass(self.mh)
        
        # Type-I tree-level couplings
        cpl_h = HP.NeutralEffectiveCouplings()
        cpl_h.tt = cpl_h.bb = cpl_h.tautau = kappa_f
        cpl_h.WW = cpl_h.ZZ = kappa_V
        
        # Loop-induced couplings (improved tan(β) dependent weights)
        # High tan(β) requires weight adjustment due to additional Higgs contributions
        if tanb < 5:
            # 低 tan(β)：原始权重（顶夸克 + W loop）
            w_top_gg = 0.875
            w_V_gg = 0.125
            w_top_gam = 0.77
            w_V_gam = 0.23
        elif tanb < 20:
            # Intermediate tan(β): gradual adjustment
            w_top_gg = 0.85
            w_V_gg = 0.15
            w_top_gam = 0.75
            w_V_gam = 0.25
        else:
            # High tan(β): increased extra Higgs contributions, weakened W loop
            w_top_gg = 0.80
            w_V_gg = 0.20
            w_top_gam = 0.70
            w_V_gam = 0.30
        
        cpl_h.gg = w_top_gg * kappa_f + w_V_gg * kappa_V
        cpl_h.gamgam = w_top_gam * kappa_f + w_V_gam * kappa_V
        
        HP.effectiveCouplingInput(h, cpl_h, reference=HP.ReferenceModel.SMHiggsEW)
        
        # ===== Charged Higgs (H±) =====
        Hpm = pred.addParticle(HP.ChargedScalar("Hpm"))
        Hpm.setMass(mHp)
        Hpm.setTotalWidth(0.1)  # 小宽度（不关键）
        
        return pred
    
    def run_parameter_scan(self, tanb_vals=None, sinba_vals=None):
        """
        运行参数空间扫描
        
        参数：
        ------
        tanb_vals : np.ndarray, optional
            tan(β) 的值
        sinba_vals : np.ndarray, optional
            sin(β-α) 的值
        """
        if tanb_vals is None:
            n_tanb = self.config["SCAN_POINTS"][0]
            tanb_min, tanb_max = self.config["TANB_RANGE"]
            tanb_vals = np.logspace(np.log10(tanb_min), np.log10(tanb_max), n_tanb)
        
        if sinba_vals is None:
            n_sinba = self.config["SCAN_POINTS"][1]
            sinba_min, sinba_max = self.config["SINBA_RANGE"]
            sinba_vals = np.linspace(sinba_min, sinba_max, n_sinba)
        
        self.scan_params = {
            "tanb_vals": tanb_vals.copy(),
            "sinba_vals": sinba_vals.copy(),
        }
        
        # Log scan configuration
        print("Scan configuration:")
        print(f"  tan(β): {tanb_vals.min():.2f} - {tanb_vals.max():.2f} ({len(tanb_vals)} points)")
        print(f"  sin(β-α): {sinba_vals.min():.2f} - {sinba_vals.max():.2f} ({len(sinba_vals)} points)")
        print(f"  Total points: {len(tanb_vals) * len(sinba_vals)}")
        print(f"  mH±: {self.config['MHp']} GeV")
        
        self.results = []
        
        # Execute parameter space scan
        for tanb in tqdm(tanb_vals, desc="tan(β)", position=0, leave=True):
            for sinba in tqdm(sinba_vals, desc="sin(β-α)", position=1, leave=False):
                # Generate 2HDM Type-I predictions
                pred = self.set_typeI_predictions(sinba, tanb)
                
                # Compute HiggsSignals χ² fit
                try:
                    chi2 = self.signals(pred)
                except Exception as e:
                    chi2 = np.nan
                
                # HiggsBounds 排除检查
                hb_ok = self.bounds(pred)
                allowed = bool(hb_ok)  # True = 允许, False = 被排除
                
                # 获取详细的 HiggsBounds 信息
                hb_details = self._get_hb_details(hb_ok)
                
                # 保存结果
                self.results.append({
                    "tan_beta": tanb,
                    "sin_beta_alpha": sinba,
                    "chi2": chi2,
                    "delta_chi2": chi2,  # 相对于最小值的 Δχ²（后续处理）
                    "allowed_hb": allowed,
                    "excluded_reason": hb_details.get("excluded_reason", ""),
                    "max_obsratio": hb_details.get("max_obsratio", 0.0),
                    "mHp": self.config["MHp"],
                })
        
        # 转换为 DataFrame
        self.df = pd.DataFrame(self.results)
        
        # 计算相对 χ² (相对最小值)
        chi2_min = self.df["chi2"].min()
        self.df["delta_chi2"] = self.df["chi2"] - chi2_min
        
        # Log scan completion statistics
        print(f"\nScan complete. Total points: {len(self.df)}")
        print(f"  χ² range: {chi2_min:.3f} to {self.df['chi2'].max():.3f}")
        print(f"  HiggsBounds allowed: {self.df['allowed_hb'].sum()} points")
        print(f"  HiggsBounds excluded: {(~self.df['allowed_hb']).sum()} points")
        
        return self.df
    
    def _get_hb_details(self, hb_result):
        """提取 HiggsBounds 详细信息"""
        details = {
            "excluded_reason": "",
            "max_obsratio": 0.0,
        }
        
        if hasattr(hb_result, "selectedLimits"):
            try:
                limits = hb_result.selectedLimits()
                if limits:
                    for limit_id, limit in limits.items():
                        if hasattr(limit, "obsratio"):
                            ratio = limit.obsratio
                            details["max_obsratio"] = max(details["max_obsratio"], ratio)
            except Exception as e:
                pass
        
        return details
    
    # ==================== 数据输出 ====================
    
    def save_results(self):
        """Save scan results to output directory.
        
        Outputs created:
        - scan_results.csv: Full results table
        - scan_data.npz: Binary format for efficient loading
        - results.pkl: Python pickle format
        - metadata.json: Scan configuration and statistics
        """
        # CSV table for spreadsheet analysis
        csv_path = self.output_dir / "scan_results.csv"
        self.df.to_csv(csv_path, index=False)
        print(f"Saved CSV: {csv_path}")
        
        # NumPy compressed format for efficient data loading
        npz_path = self.output_dir / "scan_data.npz"
        np.savez_compressed(
            npz_path,
            tanb=self.scan_params["tanb_vals"],
            sinba=self.scan_params["sinba_vals"],
            chi2_grid=self.df["chi2"].values.reshape(
                len(self.scan_params["tanb_vals"]),
                len(self.scan_params["sinba_vals"])
            ),
            delta_chi2_grid=self.df["delta_chi2"].values.reshape(
                len(self.scan_params["tanb_vals"]),
                len(self.scan_params["sinba_vals"])
            ),
            allowed_grid=self.df["allowed_hb"].values.reshape(
                len(self.scan_params["tanb_vals"]),
                len(self.scan_params["sinba_vals"])
            ),
        )
        print(f"Saved compressed data: {npz_path}")
        
        # Python pickle for object serialization
        pkl_path = self.output_dir / "results.pkl"
        with open(pkl_path, "wb") as f:
            pickle.dump({
                "df": self.df,
                "config": self.config,
                "scan_params": self.scan_params,
            }, f)
        print(f"Saved pickle: {pkl_path}")
        
        # JSON metadata for reproducibility
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "config": {k: str(v) for k, v in self.config.items()},
            "scan_info": {
                "n_points": len(self.df),
                "n_allowed": int(self.df["allowed_hb"].sum()),
                "n_excluded": int((~self.df["allowed_hb"]).sum()),
                "chi2_min": float(self.df["chi2"].min()),
                "chi2_max": float(self.df["chi2"].max()),
            }
        }
        json_path = self.output_dir / "metadata.json"
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Saved metadata: {json_path}")
    
    # ==================== 绘图 ====================
    
    def plot_2d_contours(self):
        """Generate 2D confidence region contour plot.
        
        Produces publication-quality figure showing 68% and 95% CL regions,
        HiggsBounds excluded regions, and best-fit point.
        """
        print("Generating 2D contours...")
        
        # 准备网格
        X, Y = np.meshgrid(
            self.scan_params["sinba_vals"],
            self.scan_params["tanb_vals"]
        )
        Z = self.df["delta_chi2"].values.reshape(
            len(self.scan_params["tanb_vals"]),
            len(self.scan_params["sinba_vals"])
        )
        allowed = self.df["allowed_hb"].values.reshape(
            len(self.scan_params["tanb_vals"]),
            len(self.scan_params["sinba_vals"])
        )
        
        # 找最佳拟合点
        best_idx = self.df["delta_chi2"].idxmin()
        best_sinba = self.df.loc[best_idx, "sin_beta_alpha"]
        best_tanb = self.df.loc[best_idx, "tan_beta"]
        best_chi2 = self.df.loc[best_idx, "delta_chi2"]
        
        # Plot with clean white background
        fig, ax = plt.subplots(figsize=(11, 8), facecolor='white')
        ax.set_facecolor('white')
        
        # Create masked arrays for CL regions (only on allowed points)
        Z_masked = np.ma.array(Z, mask=~allowed)
        
        # 68% CL region - Light blue fill
        contourf_68 = ax.contourf(
            X, Y, Z_masked,
            levels=[0, self.config["CL_68"]],
            colors=["#ADD8E6"],  # Light blue
            alpha=0.7
        )
        
        # 95% CL region - NO fill, only black contour line
        contour_95 = ax.contour(
            X, Y, Z_masked,
            levels=[self.config["CL_95"]],
            colors="black",
            linewidths=2.5,
            linestyles="-"
        )
        
        # 68% CL boundary - thin black contour
        contour_68 = ax.contour(
            X, Y, Z_masked,
            levels=[self.config["CL_68"]],
            colors="black",
            linewidths=1.5,
            linestyles="-",
            alpha=0.6
        )
        
        # HiggsBounds excluded region - hatched pattern
        ax.contourf(
            X, Y, ~allowed,
            levels=[0.5, 1.5],
            colors="none",
            hatches=["////"],  # Diagonal hatching pattern
            edgecolors="darkgray",
            linewidths=0.8
        )
        
        # Best fit point - solid black with white edge
        ax.plot(
            best_sinba, best_tanb,
            marker="o", color="black", markersize=12,
            markeredgecolor='white', markeredgewidth=2.5,
            zorder=15
        )
        
        # Add a small star on top for emphasis
        ax.plot(
            best_sinba, best_tanb,
            marker="*", color="white", markersize=8,
            zorder=16
        )
        
        # Labels and format
        ax.set_xlabel(r"$\sin(\beta - \alpha)$", fontsize=16, fontweight='bold')
        ax.set_ylabel(r"$\tan \beta$", fontsize=16, fontweight='bold')
        ax.set_title("2HDM Type-I: HiggsTools Constraints (Run 2)", fontsize=16, pad=15)
        
        ax.set_xlim(self.config["SINBA_RANGE"])
        ax.set_ylim(self.config["TANB_RANGE"])
        ax.set_yscale("log")
        
        # Clean grid
        ax.grid(True, alpha=0.2, linestyle="-", linewidth=0.5, color='gray')
        ax.set_axisbelow(True)
        
        # ATLAS label
        if self.config["ATLAS_STYLE"]:
            hep.cms.label(ax=ax, data=True, year="Run 2", lumi="139 fb⁻¹")
        
        # Minimal, clean legend
        from matplotlib.patches import Patch
        from matplotlib.lines import Line2D
        legend_elements = [
            # Regions
            Patch(facecolor='#ADD8E6', alpha=0.7, label=r'68% CL: $\Delta\chi^2 < 2.30$'),
            Line2D([0], [0], color='black', lw=2.5, label=r'95% CL: $\Delta\chi^2 < 5.99$'),
            Line2D([0], [0], color='black', lw=1.5, alpha=0.6, label='68% CL boundary'),
            Patch(facecolor='none', hatch='////', edgecolor='darkgray', label='HiggsBounds Excluded'),
            # Best fit marker
            Line2D([0], [0], marker='o', color='w', markerfacecolor='black', markersize=10,
                   markeredgecolor='white', markeredgewidth=2, linestyle='none', label='Best fit point'),
        ]
        
        ax.legend(handles=legend_elements, loc="upper left", fontsize=11, 
                 frameon=True, fancybox=False, edgecolor='black', framealpha=0.95)
        
        plt.tight_layout()
        
        # 保存
        for fmt in ["pdf", "png"]:
            path = self.output_dir / f"contours_2d.{fmt}"
            plt.savefig(path, dpi=300 if fmt == "pdf" else 100, bbox_inches="tight", 
                       facecolor='white', edgecolor='none')
            print(f"    ✓ {path}")
        
        plt.close()
    
    def plot_1d_profiles(self):
        """Generate 1D profile likelihood plots.
        
        Creates 1×2 subplot figure showing profile likelihoods vs tan(β)
        and sin(β-α), with CL thresholds and best-fit markers.
        """
        print("Generating 1D profiles...")
        
        best_tanb = self.df.loc[self.df["delta_chi2"].idxmin(), "tan_beta"]
        best_sinba = self.df.loc[self.df["delta_chi2"].idxmin(), "sin_beta_alpha"]
        
        # tan(β) 1D profile
        df_tanb = self.df.groupby("tan_beta")["delta_chi2"].min()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), facecolor='white')
        
        # tan(β) profile
        ax1.set_facecolor('white')
        ax1.plot(df_tanb.index, df_tanb.values, "b-", lw=2.5, label="1D Profile")
        ax1.axhline(self.config["CL_68"], color="green", ls="--", lw=2.0, alpha=0.8, label="68% CL")
        ax1.axhline(self.config["CL_95"], color="red", ls="--", lw=2.0, alpha=0.8, label="95% CL")
        ax1.axvline(best_tanb, color="orange", ls=":", lw=2, alpha=0.7, label="Best fit")
        
        ax1.set_xlabel(r"$\tan \beta$", fontsize=14, fontweight='bold')
        ax1.set_ylabel(r"$\Delta \chi^2$", fontsize=14, fontweight='bold')
        ax1.set_title(r"Profile Likelihood: $\tan \beta$", fontsize=14, fontweight='bold')
        ax1.set_xscale("log")
        ax1.set_ylim(bottom=0)
        ax1.legend(fontsize=11, loc="upper left", frameon=True, fancybox=False, edgecolor='black')
        ax1.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='gray')
        ax1.set_axisbelow(True)
        
        if self.config["ATLAS_STYLE"]:
            hep.cms.label(ax=ax1, data=True, year="Run 2")
        
        # 子图标签(放在后面，避免被hep.cms.label覆盖)
        ax1.text(0.02, 0.98, '(a)', transform=ax1.transAxes, fontsize=14, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                zorder=1000)
        
        # sin(β-α) 1D profile
        df_sinba = self.df.groupby("sin_beta_alpha")["delta_chi2"].min()
        
        ax2.set_facecolor('white')
        ax2.plot(df_sinba.index, df_sinba.values, "b-", lw=2.5, label="1D Profile")
        ax2.axhline(self.config["CL_68"], color="green", ls="--", lw=2.0, alpha=0.8, label="68% CL")
        ax2.axhline(self.config["CL_95"], color="red", ls="--", lw=2.0, alpha=0.8, label="95% CL")
        ax2.axvline(best_sinba, color="orange", ls=":", lw=2, alpha=0.7, label="Best fit")
        
        ax2.set_xlabel(r"$\sin(\beta - \alpha)$", fontsize=14, fontweight='bold')
        ax2.set_ylabel(r"$\Delta \chi^2$", fontsize=14, fontweight='bold')
        ax2.set_title(r"Profile Likelihood: $\sin(\beta - \alpha)$", fontsize=14, fontweight='bold')
        ax2.set_ylim(bottom=0)
        ax2.legend(fontsize=11, loc="upper left", frameon=True, fancybox=False, edgecolor='black')
        ax2.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='gray')
        ax2.set_axisbelow(True)
        
        if self.config["ATLAS_STYLE"]:
            hep.cms.label(ax=ax2, data=True, year="Run 2")
        
        # 子图标签(放在后面，避免被hep.cms.label覆盖)
        ax2.text(0.02, 0.98, '(b)', transform=ax2.transAxes, fontsize=14, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                zorder=1000)
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            path = self.output_dir / f"profiles_1d.{fmt}"
            plt.savefig(path, dpi=300 if fmt == "pdf" else 100, bbox_inches="tight")
            print(f"    ✓ {path}")
        
        plt.close()
    
    def plot_hb_exclusion(self):
        """Generate HiggsBounds exclusion region visualization.
        
        Shows allowed (green) and excluded (red) regions in parameter space.
        """
        print("Generating HiggsBounds exclusion plot...")
        
        X, Y = np.meshgrid(
            self.scan_params["sinba_vals"],
            self.scan_params["tanb_vals"]
        )
        allowed = self.df["allowed_hb"].values.reshape(
            len(self.scan_params["tanb_vals"]),
            len(self.scan_params["sinba_vals"])
        )
        
        fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
        ax.set_facecolor('white')
        
        # 允许区域（绿）
        ax.contourf(X, Y, allowed, levels=[0.5, 1.5], colors=["#99FF99"], alpha=0.8)
        # 排除区域（红）
        ax.contourf(X, Y, ~allowed, levels=[0.5, 1.5], colors=["#FF9999"], alpha=0.6)
        
        ax.set_xlabel(r"$\sin(\beta - \alpha)$", fontsize=16, fontweight='bold')
        ax.set_ylabel(r"$\tan \beta$", fontsize=16, fontweight='bold')
        ax.set_title("HiggsBounds Allowed & Excluded Regions", fontsize=16, fontweight='bold')
        ax.set_xlim(self.config["SINBA_RANGE"])
        ax.set_ylim(self.config["TANB_RANGE"])
        ax.set_yscale("log")
        
        if self.config["ATLAS_STYLE"]:
            hep.cms.label(ax=ax, data=True, year="Run 2")
        
        ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='gray')
        ax.set_axisbelow(True)
        
        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#99FF99", alpha=0.8, edgecolor='black', label="HiggsBounds Allowed"),
            Patch(facecolor="#FF9999", alpha=0.6, edgecolor='black', label="HiggsBounds Excluded"),
        ]
        ax.legend(handles=legend_elements, fontsize=12, loc="best", frameon=True, fancybox=False, edgecolor='black')
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            path = self.output_dir / f"hb_exclusion.{fmt}"
            plt.savefig(path, dpi=300 if fmt == "pdf" else 100, bbox_inches="tight")
            print(f"    ✓ {path}")
        
        plt.close()
    
    # ==================== 增强绘图函数 ====================
    
    def plot_chi2_distribution(self):
        """Generate χ² distribution and correlation plots.
        
        Creates 2×2 subplot figure showing:
        (a) χ² histogram
        (b) Δχ² vs tan(β) scatter plot
        (c) Δχ² vs sin(β-α) scatter plot
        (d) Statistical summary
        """
        print("Generating χ² analysis plots...")
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6), facecolor='white')
        
        # 1. χ² histogram
        ax = axes[0]
        ax.set_facecolor('white')
        chi2_data = self.df['chi2'].dropna()
        ax.hist(chi2_data, bins=50, color='steelblue', alpha=0.7, edgecolor='black', linewidth=0.8)
        ax.axvline(chi2_data.min(), color='red', linestyle='--', lw=2, label=f'Min = {chi2_data.min():.2f}')
        ax.axvline(chi2_data.median(), color='green', linestyle='--', lw=2, label=f'Median = {chi2_data.median():.2f}')
        ax.set_xlabel(r'$\chi^2$', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Points', fontsize=12, fontweight='bold')
        ax.set_title(r'$\chi^2$ Distribution', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10, frameon=True, fancybox=False, edgecolor='black')
        ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='gray')
        ax.set_axisbelow(True)
        ax.text(0.02, 0.98, '(a)', transform=ax.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 2. Δχ² vs tan(β)
        ax = axes[1]
        ax.set_facecolor('white')
        # 使用固定的colorbar范围避免artifacts
        scatter = ax.scatter(self.df['tan_beta'], self.df['delta_chi2'], 
                           c=self.df['sin_beta_alpha'], cmap='viridis', 
                           alpha=0.6, s=30, vmin=self.config["SINBA_RANGE"][0], 
                           vmax=self.config["SINBA_RANGE"][1], edgecolors='none')
        ax.set_xlabel(r'$\tan\beta$', fontsize=12, fontweight='bold')
        ax.set_ylabel(r'$\Delta\chi^2$', fontsize=12, fontweight='bold')
        ax.set_title(r'$\Delta\chi^2$ vs $\tan\beta$', fontsize=13, fontweight='bold')
        ax.set_xscale('log')
        ax.set_ylim(bottom=0, top=self.config["CL_95"]*3)
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(r'$\sin(\beta-\alpha)$', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='gray')
        ax.set_axisbelow(True)
        ax.text(0.02, 0.98, '(b)', transform=ax.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 3. Δχ² vs sin(β-α)
        ax = axes[2]
        ax.set_facecolor('white')
        scatter = ax.scatter(self.df['sin_beta_alpha'], self.df['delta_chi2'], 
                           c=self.df['tan_beta'], cmap='plasma', 
                           alpha=0.6, s=30, edgecolors='none')
        ax.set_xlabel(r'$\sin(\beta-\alpha)$', fontsize=12, fontweight='bold')
        ax.set_ylabel(r'$\Delta\chi^2$', fontsize=12, fontweight='bold')
        ax.set_title(r'$\Delta\chi^2$ vs $\sin(\beta-\alpha)$', fontsize=13, fontweight='bold')
        ax.set_ylim(bottom=0, top=self.config["CL_95"]*3)
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(r'$\tan\beta$', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='gray')
        ax.set_axisbelow(True)
        ax.text(0.02, 0.98, '(c)', transform=ax.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            path = self.output_dir / f"chi2_analysis.{fmt}"
            plt.savefig(path, dpi=300 if fmt == "pdf" else 100, bbox_inches="tight")
            print(f"    ✓ {path}")
        
        plt.close()
    
    def plot_coupling_heatmap(self):
        """Generate Higgs coupling coefficient heatmaps.
        
        Creates 1×2 subplot figure showing fermionic (κf) and vector (κV)
        coupling strength variations across parameter space.
        """
        print("Generating coupling heatmaps...")
        
        # 计算耦合系数
        kappa_f_grid = np.zeros((len(self.scan_params["tanb_vals"]), len(self.scan_params["sinba_vals"])))
        kappa_v_grid = np.zeros_like(kappa_f_grid)
        
        for idx, row in self.df.iterrows():
            tanb_idx = np.argmin(np.abs(self.scan_params["tanb_vals"] - row["tan_beta"]))
            sinba_idx = np.argmin(np.abs(self.scan_params["sinba_vals"] - row["sin_beta_alpha"]))
            
            tanb = row["tan_beta"]
            sinba = row["sin_beta_alpha"]
            beta = np.arctan(tanb)
            alpha = beta - np.arcsin(sinba)
            
            kappa_f_grid[tanb_idx, sinba_idx] = np.cos(alpha) / np.sin(beta)
            kappa_v_grid[tanb_idx, sinba_idx] = sinba
        
        X, Y = np.meshgrid(self.scan_params["sinba_vals"], self.scan_params["tanb_vals"])
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), facecolor='white')
        
        # κ_f 热图
        ax1.set_facecolor('white')
        cf1 = ax1.contourf(X, Y, kappa_f_grid, levels=20, cmap='RdYlBu_r')
        ax1.contour(X, Y, kappa_f_grid, levels=10, colors='black', alpha=0.2, linewidths=0.5)
        ax1.set_xlabel(r'$\sin(\beta-\alpha)$', fontsize=14, fontweight='bold')
        ax1.set_ylabel(r'$\tan\beta$', fontsize=14, fontweight='bold')
        ax1.set_title(r'Fermionic coupling $\kappa_f = \cos\alpha/\sin\beta$', fontsize=14, fontweight='bold')
        ax1.set_yscale('log')
        ax1.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='gray')
        ax1.set_axisbelow(True)
        cbar1 = plt.colorbar(cf1, ax=ax1)
        cbar1.set_label(r'$\kappa_f$', fontsize=12, fontweight='bold')
        ax1.text(0.02, 0.98, '(a)', transform=ax1.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # κ_V 热图
        ax2.set_facecolor('white')
        cf2 = ax2.contourf(X, Y, kappa_v_grid, levels=20, cmap='viridis')
        ax2.contour(X, Y, kappa_v_grid, levels=10, colors='black', alpha=0.2, linewidths=0.5)
        ax2.set_xlabel(r'$\sin(\beta-\alpha)$', fontsize=14, fontweight='bold')
        ax2.set_ylabel(r'$\tan\beta$', fontsize=14, fontweight='bold')
        ax2.set_title(r'Vector coupling $\kappa_V = \sin(\beta-\alpha)$', fontsize=14, fontweight='bold')
        ax2.set_yscale('log')
        ax2.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='gray')
        ax2.set_axisbelow(True)
        cbar2 = plt.colorbar(cf2, ax=ax2)
        cbar2.set_label(r'$\kappa_V$', fontsize=12, fontweight='bold')
        ax2.text(0.02, 0.98, '(b)', transform=ax2.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            path = self.output_dir / f"coupling_heatmap.{fmt}"
            plt.savefig(path, dpi=300 if fmt == "pdf" else 100, bbox_inches="tight")
            print(f"    ✓ {path}")
        
        plt.close()
    
    def plot_constraints_comparison(self):
        """Generate constraint comparison analysis plots.
        
        Creates 2×2 subplot figure showing:
        (a) Venn diagram of HiggsSignals vs HiggsBounds regions
        (b) Constraint strength vs tan(β)
        (c) Constraint strength vs sin(β-α)
        (d) Statistical summary
        """
        print("Generating constraint comparison...")
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.patch.set_facecolor('white')
        
        # 1. HiggsSignals vs HiggsBounds Venn diagram
        ax = axes[0]
        hs_only = len(self.df[(self.df["delta_chi2"] < self.config["CL_95"]) & (~self.df["allowed_hb"])])
        hb_only = len(self.df[(self.df["delta_chi2"] >= self.config["CL_95"]) & (self.df["allowed_hb"])])
        both = len(self.df[(self.df["delta_chi2"] < self.config["CL_95"]) & (self.df["allowed_hb"])])
        
        categories = ['HiggsSignals\n95% CL\nOnly', 'HiggsBounds\nOnly', 'Both']
        values = [hs_only, hb_only, both]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        bars = ax.bar(categories, values, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        ax.set_ylabel('Number of Scan Points', fontsize=12)
        ax.set_title('Constraint Venn Diagram', fontsize=13)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(val)}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        ax.text(0.02, 0.98, '(a)', transform=ax.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 2. 不同参数下的约束强度
        ax = axes[1]
        
        # 按 tan β 分组，计算 HiggsBounds 允许的比例
        tanb_bins = np.logspace(np.log10(self.config["TANB_RANGE"][0]), 
                               np.log10(self.config["TANB_RANGE"][1]), 8)
        hb_fraction = []
        tanb_centers = []
        
        for i in range(len(tanb_bins)-1):
            mask = (self.df["tan_beta"] >= tanb_bins[i]) & (self.df["tan_beta"] < tanb_bins[i+1])
            if mask.sum() > 0:
                tanb_centers.append(np.sqrt(tanb_bins[i] * tanb_bins[i+1]))
                hb_fraction.append(self.df[mask]["allowed_hb"].sum() / mask.sum() * 100)
        
        ax.plot(tanb_centers, hb_fraction, 'o-', color='darkblue', lw=2.5, markersize=8, label='HiggsBounds Allowed')
        ax.fill_between(tanb_centers, hb_fraction, alpha=0.3, color='skyblue')
        ax.axhline(100, color='green', linestyle='--', lw=2, label='Fully Allowed')
        ax.axhline(0, color='red', linestyle='--', lw=2, label='Fully Excluded')
        ax.set_xlabel(r'$\tan\beta$', fontsize=12)
        ax.set_ylabel('HiggsBounds Allowed Fraction (%)', fontsize=12)
        ax.set_xscale('log')
        ax.set_ylim(-5, 105)
        ax.set_title(r'Constraint Strength vs $\tan\beta$', fontsize=13)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.text(0.02, 0.98, '(b)', transform=ax.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 3. sin(β-α) 依赖性
        ax = axes[2]
        
        sinba_bins = np.linspace(self.config["SINBA_RANGE"][0], self.config["SINBA_RANGE"][1], 8)
        hb_fraction_sinba = []
        sinba_centers = []
        
        for i in range(len(sinba_bins)-1):
            mask = (self.df["sin_beta_alpha"] >= sinba_bins[i]) & (self.df["sin_beta_alpha"] < sinba_bins[i+1])
            if mask.sum() > 0:
                sinba_centers.append((sinba_bins[i] + sinba_bins[i+1]) / 2)
                hb_fraction_sinba.append(self.df[mask]["allowed_hb"].sum() / mask.sum() * 100)
        
        ax.plot(sinba_centers, hb_fraction_sinba, 's-', color='darkred', lw=2.5, markersize=8, label='HiggsBounds Allowed')
        ax.fill_between(sinba_centers, hb_fraction_sinba, alpha=0.3, color='salmon')
        ax.axhline(100, color='green', linestyle='--', lw=2)
        ax.axhline(0, color='red', linestyle='--', lw=2)
        ax.set_xlabel(r'$\sin(\beta-\alpha)$', fontsize=12)
        ax.set_ylabel('HiggsBounds Allowed Fraction (%)', fontsize=12)
        ax.set_ylim(-5, 105)
        ax.set_title(r'Constraint Strength vs $\sin(\beta-\alpha)$', fontsize=13)
        ax.grid(True, alpha=0.3)
        ax.text(0.02, 0.98, '(c)', transform=ax.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            path = self.output_dir / f"constraints_comparison.{fmt}"
            plt.savefig(path, dpi=300 if fmt == "pdf" else 100, bbox_inches="tight")
            print(f"    ✓ {path}")
        
        plt.close()
    
    def plot_best_fit_region(self):
        """Generate detailed best-fit point analysis plots.
        
        Creates 2×2 subplot figure showing:
        (a) Zoomed contours around best-fit point
        (b) Coupling coefficient variation near best fit
        (c) Confidence level contours (68%, 95%, 99%)
        (d) Best-fit point parameters and properties
        """
        print("Generating best-fit region details...")
        
        best_idx = self.df["delta_chi2"].idxmin()
        best_tanb = self.df.loc[best_idx, "tan_beta"]
        best_sinba = self.df.loc[best_idx, "sin_beta_alpha"]
        best_chi2 = self.df.loc[best_idx, "delta_chi2"]
        
        # 在最佳点周围提取数据
        region = self.df[
            ((np.abs(np.log(self.df["tan_beta"]/best_tanb))) < 0.5) &
            ((np.abs(self.df["sin_beta_alpha"] - best_sinba)) < 0.1)
        ]
        
        fig, axes = plt.subplots(1, 3, figsize=(21, 7), facecolor='white')
        
        # 1. 最佳点周围的轮廓（放大）
        ax = axes[0]
        ax.set_facecolor('white')
        ax.set_axisbelow(True)
        
        if len(region) > 0:
            X_region = region['sin_beta_alpha'].values.reshape(-1, 1)
            Y_region = region['tan_beta'].values.reshape(-1, 1)
            Z_region = region['delta_chi2'].values.reshape(-1, 1)
            
            # 使用三角剖分进行插值
            from matplotlib.tri import Triangulation, TriContourSet
            try:
                triang = Triangulation(region['sin_beta_alpha'], region['tan_beta'])
                contourf = ax.tricontourf(triang, region['delta_chi2'], levels=15, cmap='RdYlGn_r')
                ax.tricontour(triang, region['delta_chi2'], levels=10, colors='black', alpha=0.3, linewidths=0.5)
                
                # Add colorbar with label
                cbar = plt.colorbar(contourf, ax=ax)
                cbar.set_label(r'$\Delta\chi^2$', fontsize=11, fontweight='bold')
            except:
                pass
        
        ax.plot(best_sinba, best_tanb, '*', color='red', markersize=30, label=f'Best fit\n(χ²={best_chi2:.2f})')
        ax.set_xlabel(r'$\sin(\beta-\alpha)$', fontsize=12, fontweight='bold')
        ax.set_ylabel(r'$\tan\beta$', fontsize=12, fontweight='bold')
        ax.set_title('Zoomed Contours Near Best Fit\n(Staircase: Vacuum Stability Boundary at tan(β)≈50)', 
                    fontsize=12, fontweight='bold')
        
        ax.legend(fontsize=10, loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.text(0.02, 0.98, '(a)', transform=ax.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 2. 最佳点周围的物理参数变化
        ax = axes[1]
        ax.set_facecolor('white')
        ax.set_axisbelow(True)
        
        # 计算耦合系数
        kappas = []
        distances = []
        
        for idx, row in region.iterrows():
            tanb = row["tan_beta"]
            sinba = row["sin_beta_alpha"]
            beta = np.arctan(tanb)
            alpha = beta - np.arcsin(sinba)
            kappa_f = np.cos(alpha) / np.sin(beta)
            kappas.append(kappa_f)
            
            dist = np.sqrt((np.log(tanb/best_tanb))**2 + (sinba - best_sinba)**2)
            distances.append(dist)
        
        scatter = ax.scatter(distances, kappas, c=region['delta_chi2'].values, 
                           cmap='plasma', s=50, alpha=0.6)
        ax.plot(0, np.cos(np.arctan(best_tanb) - np.arcsin(best_sinba))/np.sin(np.arctan(best_tanb)), 
               '*', color='red', markersize=25, label='Best fit')
        ax.set_xlabel('Distance in parameter space', fontsize=13, fontweight='bold')
        ax.set_ylabel(r'Fermionic coupling $\kappa_f$', fontsize=13, fontweight='bold')
        ax.set_title('How Couplings Vary from Best Fit', fontsize=13, fontweight='bold')
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(r'$\Delta\chi^2$', fontsize=12, fontweight='bold')
        ax.legend(fontsize=11, loc='best')
        ax.grid(True, alpha=0.3)
        ax.text(0.02, 0.98, '(b)', transform=ax.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 3. Confidence level ellipses
        ax = axes[2]
        ax.set_facecolor('white')
        ax.set_axisbelow(True)
        
        X, Y = np.meshgrid(self.scan_params["sinba_vals"], self.scan_params["tanb_vals"])
        Z = self.df["delta_chi2"].values.reshape(
            len(self.scan_params["tanb_vals"]),
            len(self.scan_params["sinba_vals"])
        )
        
        # Only plot around best fit point
        levels_to_plot = [self.config["CL_68"], self.config["CL_95"], 10.0]
        # Use different colors for each CL level
        colors_cl = ['#2ecc71', '#f39c12', '#e74c3c']
        linestyles_cl = ['solid', 'dashed', 'dotted']
        for level, color, ls in zip(levels_to_plot, colors_cl, linestyles_cl):
            ax.contour(X, Y, Z, levels=[level], colors=color, 
                      linewidths=2.5, linestyles=ls)
        
        ax.plot(best_sinba, best_tanb, '*', color='red', markersize=30, zorder=5)
        
        ax.set_xlabel(r'$\sin(\beta-\alpha)$', fontsize=13)
        ax.set_ylabel(r'$\tan\beta$', fontsize=13)
        ax.set_title(r'Confidence Level Contours', fontsize=13, fontweight='bold')
        ax.set_yscale('log')
        # Add proper legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='#2ecc71', lw=2.5, label=f'68% CL (Δχ²<{self.config["CL_68"]:.2f})'),
            Line2D([0], [0], color='#f39c12', lw=2.5, linestyle='--', label=f'95% CL (Δχ²<{self.config["CL_95"]:.2f})'),
            Line2D([0], [0], color='#e74c3c', lw=2.5, linestyle=':', label='99% CL (Δχ²<10.0)'),
        ]
        ax.legend(handles=legend_elements, fontsize=10, loc='best')
        ax.grid(True, alpha=0.3)
        ax.text(0.02, 0.98, '(c)', transform=ax.transAxes, fontsize=12, fontweight='bold',
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        for fmt in ["pdf", "png"]:
            path = self.output_dir / f"best_fit_details.{fmt}"
            plt.savefig(path, dpi=300 if fmt == "pdf" else 100, bbox_inches="tight")
            print(f"    ✓ {path}")
        
        plt.close()
    
    # ==================== 分析统计 ====================
    
    def generate_benchmark_table(self):
        """Generate benchmark points table for publication.
        
        Selects and exports the 5 best-fit points satisfying both
        HiggsSignals (95% CL) and HiggsBounds constraints.
        """
        # Select 5 best points within 95% CL and HiggsBounds allowed
        candidates = self.df[
            (self.df["delta_chi2"] < self.config["CL_95"]) &
            (self.df["allowed_hb"])
        ].nsmallest(5, "delta_chi2")
        
        # LaTeX 表格
        latex_cols = ["tan_beta", "sin_beta_alpha", "delta_chi2", "mHp"]
        latex_table = candidates[latex_cols].to_latex(
            index=False,
            float_format="%.3f",
            caption="Selected benchmark points (95\\% CL, HiggsBounds allowed)",
            label="tab:benchmarks",
        )
        
        # 保存
        tex_path = self.output_dir / "benchmark_table.tex"
        with open(tex_path, "w") as f:
            f.write(latex_table)
        print(f"Saved LaTeX table: {tex_path}")
        
        # Print summary statistics
        print("\nScan Results Summary:")
        print("Best fit point:")
        best = self.df.loc[self.df["delta_chi2"].idxmin()]
        print(f"  tan(β) = {best['tan_beta']:.4f}")
        print(f"  sin(β-α) = {best['sin_beta_alpha']:.4f}")
        print(f"  Δχ² = {best['delta_chi2']:.4f}")
        print(f"  HiggsBounds: {'ALLOWED' if best['allowed_hb'] else 'EXCLUDED'}")
        
        # Confidence level statistics
        cl68_allowed = len(self.df[
            (self.df["delta_chi2"] < self.config["CL_68"]) &
            (self.df["allowed_hb"])
        ])
        cl95_allowed = len(self.df[
            (self.df["delta_chi2"] < self.config["CL_95"]) &
            (self.df["allowed_hb"])
        ])
        print(f"\nConfidence regions (HiggsBounds allowed):")
        print(f"  68% CL: {cl68_allowed} points")
        print(f"  95% CL: {cl95_allowed} points")
        
        return candidates
    
    def generate_summary_report(self):
        """Generate comprehensive analysis summary report.
        
        Creates a formatted text report with scan configuration,
        results summary, and file outputs.
        """
        report = f"""
========================================================================
  2HDM Type-I Analysis Summary Report
========================================================================

Scan Configuration:
  Parameter space: tan(β) ∈ [{self.config["TANB_RANGE"][0]:.2f}, {self.config["TANB_RANGE"][1]:.2f}]
  Parameter space: sin(β-α) ∈ [{self.config["SINBA_RANGE"][0]:.2f}, {self.config["SINBA_RANGE"][1]:.2f}]
  Reference Higgs mass: {self.config["MH_REF"]} GeV
  Charged Higgs mass: {self.config["MHp"]} GeV
  Total scan points: {len(self.df)}

Best Fit Point:
"""
        best_idx = self.df["delta_chi2"].idxmin()
        best = self.df.loc[best_idx]
        report += f"""  tan(β) = {best['tan_beta']:.4f}
  sin(β-α) = {best['sin_beta_alpha']:.4f}
  χ² = {best['chi2']:.3f}
  Δχ² = {best['delta_chi2']:.3f}
  HiggsBounds: {'ALLOWED' if best['allowed_hb'] else 'EXCLUDED'}

Constraint Results:
"""
        cl68 = len(self.df[(self.df["delta_chi2"] < self.config["CL_68"]) & self.df["allowed_hb"]])
        cl95 = len(self.df[(self.df["delta_chi2"] < self.config["CL_95"]) & self.df["allowed_hb"]])
        excluded_hb = len(self.df[~self.df["allowed_hb"]])
        
        report += f"""  68% CL region: {cl68} points
  95% CL region: {cl95} points
  HiggsBounds excluded: {excluded_hb} points ({excluded_hb/len(self.df)*100:.1f}%)

Output Files:
  Plots: contours_2d.pdf, profiles_1d.pdf, hb_exclusion.pdf
  Data: scan_results.csv, scan_data.npz
  Table: benchmark_table.tex
  Metadata: metadata.json

Publication Recommendations:
  1. Use contours_2d.pdf as main result figure
  2. Reference benchmark_table.tex for benchmark points
  3. Include scan_results.csv as supplementary material
  4. Cite HiggsTools in methods section

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
========================================================================
"""
        
        # 保存报告
        report_path = self.output_dir / "analysis_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(report)


def main():
    """Main analysis pipeline.
    
    Executes complete 2HDM Type-I parameter space analysis including
    scanning, result storage, and visualization generation.
    """
    print("\n" + "="*70)
    print("2HDM Type-I Parameter Space Analysis")
    print("="*70 + "\n")
    
    # Initialize analyzer
    analyzer = HiggsToolsAnalyzer(config=CONFIG)
    
    # Execute parameter space scan
    analyzer.run_parameter_scan()
    
    # Save results to disk
    analyzer.save_results()
    
    # Generate publication figures
    analyzer.plot_2d_contours()
    analyzer.plot_1d_profiles()
    analyzer.plot_hb_exclusion()
    analyzer.plot_chi2_distribution()
    analyzer.plot_coupling_heatmap()
    analyzer.plot_constraints_comparison()
    analyzer.plot_best_fit_region()
    
    # Generate analysis outputs
    analyzer.generate_benchmark_table()
    analyzer.generate_summary_report()
    
    print("="*70)
    print(f"Analysis complete. Results saved to: {CONFIG['OUTPUT_DIR']}/")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
