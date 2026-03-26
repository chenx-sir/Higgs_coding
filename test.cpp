// test.cpp
// HiggsTools C++ 2HDM Type-I 扫描（最终版，匹配你的 API）

#include <iostream>
#include <fstream>
#include <cmath>
#include <string>
#include <map>  // 需要这个来处理 selectedLimits() 返回的 map

#include "Higgs/Predictions.hpp"
#include "Higgs/Bounds.hpp"
#include "Higgs/Signals.hpp"

namespace HP = Higgs::predictions;

int main() {
    const std::string HB_DATA_PATH = "/home/chenxsir/higgstools/data/HBDataSet";
    const std::string HS_DATA_PATH = "/home/chenxsir/higgstools/data/HSDataSet";

    const double m_h = 125.09;
    const int n_tanb  = 30;   // 测试用小网格，成功后改大
    const int n_sinba = 30;

    const double tanb_min = 0.5, tanb_max = 30.0;
    const double sinba_min = 0.1, sinba_max = 1.0;

    std::ofstream outfile("2hdm_typeI_scan.csv");
    if (!outfile.is_open()) {
        std::cerr << "无法打开输出文件！\n";
        return 1;
    }
    outfile << "tan_beta,sin_beta_alpha,chi2,excluded,mHpm,max_obs_ratio\n";

    std::cout << "初始化 HiggsBounds...\n";
    Higgs::Bounds bounds(HB_DATA_PATH);

    std::cout << "初始化 HiggsSignals...\n";
    Higgs::Signals signals(HS_DATA_PATH);

    std::cout << "扫描开始 (" << n_tanb * n_sinba << " 点)...\n";

    for (int i = 0; i < n_tanb; ++i) {
        double tanb = tanb_min + (tanb_max - tanb_min) * static_cast<double>(i) / (n_tanb - 1.0);
        double beta = std::atan(tanb);

        for (int j = 0; j < n_sinba; ++j) {
            double sinba = sinba_min + (sinba_max - sinba_min) * static_cast<double>(j) / (n_sinba - 1.0);
            if (sinba > 1.0) continue;

            double alpha = beta - std::asin(sinba);

            HP::Predictions pred;

            // 轻 Higgs
            auto& h = pred.addParticle(HP::BsmParticle{"h", HP::ECharge::neutral, HP::CP::even});
            h.setMass(m_h);

            // Type-I 有效耦合
            double kappa_f = std::cos(alpha) / std::sin(beta);
            double kappa_V = sinba;

            HP::NeutralEffectiveCouplings cpls;
            cpls.tt     = kappa_f;
            cpls.bb     = kappa_f;
            cpls.tautau = kappa_f;
            cpls.WW     = kappa_V;
            cpls.ZZ     = kappa_V;
            cpls.gg     = 1.0;
            cpls.gamgam = 1.0;

            HP::effectiveCouplingInput(h, cpls, HP::ReferenceModel::SMHiggsEW);

            // 带电 Higgs
            double mHpm = 350.0;
            auto& Hpm = pred.addParticle(HP::BsmParticle{"Hpm", HP::ECharge::single, HP::CP::undefined});
            Hpm.setMass(mHpm);
            Hpm.setTotalWidth(0.1);

            // χ²
            double chi2 = signals(pred);

            // HiggsBounds 排除判断
            auto hb_res = bounds(pred);
            bool excluded = false;
            double max_obs_ratio = 0.0;

            // selectedLimits() 返回 map<string, AppliedLimit>
            const auto& limits = hb_res.selectedLimits();
            if (!limits.empty()) {
                // 遍历所有选中的限制，找最大 obsratio
                for (const auto& [id, limit] : limits) {
                    double ratio = limit.obsratio;  // 注意：这里是成员变量 obsratio（小写 o）
                    if (ratio > max_obs_ratio) {
                        max_obs_ratio = ratio;
                    }
                    if (ratio > 1.0) {
                        excluded = true;
                        // 可以 break; 如果只关心是否排除
                    }
                }
            }

            outfile << tanb << "," << sinba << "," << chi2 << ","
                    << (excluded ? "yes" : "no") << "," << mHpm << "," << max_obs_ratio << "\n";

            int progress = (i * n_sinba + j + 1) * 100 / (n_tanb * n_sinba);
            if (progress % 10 == 0 && progress > 0) {
                std::cout << progress << "% ...\n";
            }
        }
    }

    outfile.close();
    std::cout << "\n完成！结果：2hdm_typeI_scan.csv\n"
              << "excluded = yes 表示至少一个限制被违反 (obsratio >1)\n"
              << "max_obs_ratio >1 表示被排除\n"
              << "下一步：Python 绘图 tan_beta vs sin_beta_alpha 的 Δχ² contour\n";

    return 0;
}