#!/usr/bin/python3.11

import ROOT
import ctypes
import numpy as np
import os

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptFit(0)

SIGNAL_FILE = "signal_histograms.root"
BKG_FILE = "background_histograms.root"
DATA_FILE = "data_histograms.root"
OUTPUT_DIR = "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

ETA_BINS = [0.0, 0.4, 0.8, 1.5, 1.8, 2.1]
N_ETA = len(ETA_BINS) - 1

SIG_FORMULA = "[0]*( [1]*TMath::Gaus(x,[2],[3],1) + (1-[1])*TMath::Gaus(x,[4],[5],1) )"


BKG_FORMULA = "[6]*(1 - TMath::Erf((x-[7])/[8]))"


FULL_FORMULA = SIG_FORMULA + " + " + BKG_FORMULA


def open_hist(root_file, name):
    """Retrieve a histogram from an open TFile, detach from file ownership."""
    h = root_file.Get(name)
    if not h:
        raise RuntimeError(f"Histogram '{name}' not found in {root_file.GetName()}")
    h.SetDirectory(0)
    return h


# fit signal shape with 2 gaussians
def fit_signal_shape(h_sig, tag):
    xmin = h_sig.GetXaxis().GetXmin()
    xmax = h_sig.GetXaxis().GetXmax()

    f = ROOT.TF1(f"f_sig_{tag}", SIG_FORMULA, xmin, xmax)
    # p0 = norm (free, just for the shape fit)
    f.SetParameter(0, h_sig.Integral())
    f.SetParameter(1, 0.7)  # fraction
    f.SetParameter(2, 78.0)  # mean1
    f.SetParameter(3, 5.0)  # sigma1
    f.SetParameter(4, 60.0)  # mean2
    f.SetParameter(5, 20.0)  # sigma2
    f.SetParLimits(1, 0.0, 1.0)
    f.SetParLimits(3, 0.5, 40.0)
    f.SetParLimits(5, 0.5, 60.0)
    f.SetLineColor(ROOT.kRed)
    f.SetLineWidth(2)

    h_sig.Fit(f, "WRQS")

    shape = {p: (f.GetParameter(p), f.GetParError(p)) for p in range(1, 6)}
    return f, shape


#fit background shape with erf function
def fit_bkg_shape(h_bkg, tag):
    xmin = h_bkg.GetXaxis().GetXmin()
    xmax = h_bkg.GetXaxis().GetXmax()

    f = ROOT.TF1(f"f_bkg_{tag}", BKG_FORMULA, xmin, xmax)
    f.SetParameter(6, 150)  # norm (free for shape fit)
    f.SetParameter(7, 50.0)  # turn-on
    f.SetParameter(8, 20.0)  # width
    f.SetParLimits(6, 0.0, 1e9)
    f.SetParLimits(8, 0.5, 80.0)
    f.SetLineColor(ROOT.kOrange + 1)
    f.SetLineWidth(2)

    h_bkg.Fit(f, "LRQS", "", 30, xmax)

    shape = {p: (f.GetParameter(p), f.GetParError(p)) for p in range(7, 9)}
    return f, shape


#fit data normalisations
def fit_data_norms(h_data, sig_shape, bkg_shape, tag):
    xmin = h_data.GetXaxis().GetXmin()
    xmax = h_data.GetXaxis().GetXmax()

    f = ROOT.TF1(f"f_data_{tag}", FULL_FORMULA, xmin, xmax)


    f.SetParameter(0, h_data.Integral() * 0.8)
    f.SetParameter(6, h_data.Integral() * 0.2)

    #Freeze signal shape params
    for p in range(1, 6):
        val, _ = sig_shape[p]
        f.SetParameter(p, val)
        f.FixParameter(p, val)

    #Freeze bkg shape params
    for p in range(7, 9):
        val, _ = bkg_shape[p]
        f.SetParameter(p, val)
        f.FixParameter(p, val)

    f.SetParLimits(0, 0.0, 1e9)
    f.SetParLimits(6, 0.0, 1e9)
    f.SetLineColor(ROOT.kBlack)
    f.SetLineWidth(2)

    h_data.Fit(f, "WRQS", "", 30, xmax)

    N_sig = f.GetParameter(0)
    eN_sig = f.GetParError(0)
    N_bkg = f.GetParameter(6)
    eN_bkg = f.GetParError(6)
    return f, N_sig, eN_sig, N_bkg, eN_bkg


def _component_tfs(fit_func, xmin, xmax):
    f_g1 = ROOT.TF1("_g1", "[0]*[1]*TMath::Gaus(x,[2],[3],1)", xmin, xmax)
    f_g2 = ROOT.TF1("_g2", "[0]*(1-[1])*TMath::Gaus(x,[4],[5],1)", xmin, xmax)
    f_erf = ROOT.TF1("_erf", "[6]*(1-TMath::Erf((x-[7])/[8]))", xmin, xmax)
    for fi in (f_g1, f_g2, f_erf):
        for p in range(9):
            fi.SetParameter(p, fit_func.GetParameter(p))
    f_g1.SetLineColor(ROOT.kGreen + 2)
    f_g1.SetLineStyle(2)
    f_g1.SetLineWidth(2)
    f_g2.SetLineColor(ROOT.kMagenta)
    f_g2.SetLineStyle(3)
    f_g2.SetLineWidth(2)
    f_erf.SetLineColor(ROOT.kOrange + 1)
    f_erf.SetLineStyle(4)
    f_erf.SetLineWidth(2)
    return f_g1, f_g2, f_erf


def save_shape_plot(hist, fit_func, title, fname_out, extra_tfs=None):
    c = ROOT.TCanvas(f"c_{fname_out}", "", 800, 600)
    c.SetLeftMargin(0.12)
    hist.SetMarkerStyle(20)
    hist.SetMarkerSize(0.8)
    hist.GetXaxis().SetTitle("M_{T} [GeV]")
    hist.GetYaxis().SetTitle("Events / bin")
    hist.SetTitle(title)
    hist.Draw("E")
    fit_func.Draw("same")
    leg = ROOT.TLegend(0.62, 0.70, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.030)
    leg.AddEntry(hist, "MC", "lep")
    leg.AddEntry(fit_func, "Fit", "l")
    if extra_tfs:
        labels = ["Gauss 1", "Gauss 2"]
        for tf, lbl in zip(extra_tfs, labels):
            tf.Draw("same")
            leg.AddEntry(tf, lbl, "l")
    leg.Draw()
    ROOT.gPad.Update()
    c.SaveAs(fname_out)
    print(f"  Saved {fname_out}")
    c.Close()


def save_data_plot(h_data, f_full, f_g1, f_g2, f_erf, title, fname_out):
    c = ROOT.TCanvas(f"c_{fname_out}", "", 800, 600)
    c.SetLeftMargin(0.12)
    h_data.SetMarkerStyle(20)
    h_data.SetMarkerSize(0.8)
    h_data.SetMarkerColor(ROOT.kBlack)
    h_data.SetLineColor(ROOT.kBlack)
    h_data.GetXaxis().SetTitle("M_{T} [GeV]")
    h_data.GetYaxis().SetTitle("Events / bin")
    h_data.SetTitle(title)
    h_data.Draw("E")
    f_full.Draw("same")
    f_g1.Draw("same")
    f_g2.Draw("same")
    f_erf.Draw("same")
    leg = ROOT.TLegend(0.62, 0.62, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.030)
    leg.AddEntry(h_data, "Data", "lep")
    leg.AddEntry(f_full, "Total fit", "l")
    leg.AddEntry(f_g1, "Gauss 1", "l")
    leg.AddEntry(f_g2, "Gauss 2", "l")
    leg.AddEntry(f_erf, "Erf bkg", "l")
    leg.Draw()
    ROOT.gPad.Update()
    c.SaveAs(fname_out)
    print(f"  Saved {fname_out}")
    c.Close()

def main():
    tf_sig = ROOT.TFile.Open(SIGNAL_FILE)
    tf_bkg = ROOT.TFile.Open(BKG_FILE)
    tf_data = ROOT.TFile.Open(DATA_FILE)
    for tf, name in [(tf_sig, SIGNAL_FILE), (tf_bkg, BKG_FILE), (tf_data, DATA_FILE)]:
        if not tf or tf.IsZombie():
            raise RuntimeError(f"Cannot open {name}")

    asym_vals = []
    asym_errs = []
    eta_centers = []
    eta_errs = []

    for i in range(N_ETA):
        eta_lo = ETA_BINS[i]
        eta_hi = ETA_BINS[i + 1]
        eta_centers.append(0.5 * (eta_lo + eta_hi))
        eta_errs.append(0.5 * (eta_hi - eta_lo))

        print(f"\n{'=' * 60}")
        print(f"Eta bin {i}: [{eta_lo:.1f}, {eta_hi:.1f}]")

        N_sig_charges = []
        eN_sig_charges = []

        for charge in ("plus", "minus"):
            tag = f"eta{i}_{charge}"
            hname = f"MT_eta_{i}_{charge}"
            sym = "W^{+}" if charge == "plus" else "W^{-}"
            eta_str = f"{eta_lo:.1f} < |#eta| < {eta_hi:.1f}"

            h_sig = open_hist(tf_sig, hname)
            h_bkg = open_hist(tf_bkg, hname)
            h_data = open_hist(tf_data, hname)

            mc_color = ROOT.kRed + 1 if charge == "plus" else ROOT.kBlue + 1
            for h in (h_sig, h_bkg):
                h.SetLineColor(mc_color)
                h.SetMarkerColor(mc_color)

            #Signal shape fit on MC
            print(f"  [{charge}] Fitting signal shape ...")
            f_sig_fit, sig_shape = fit_signal_shape(h_sig, tag)
            save_shape_plot(
                h_sig,
                f_sig_fit,
                f"Signal MC  {sym},  {eta_str}",
                os.path.join(OUTPUT_DIR, f"sig_{tag}.png"),
                extra_tfs=[
                    ROOT.TF1(
                        f"_g1_{tag}",
                        "[0]*[1]*TMath::Gaus(x,[2],[3],1)",
                        h_sig.GetXaxis().GetXmin(),
                        h_sig.GetXaxis().GetXmax(),
                    ),
                    ROOT.TF1(
                        f"_g2_{tag}",
                        "[0]*(1-[1])*TMath::Gaus(x,[4],[5],1)",
                        h_sig.GetXaxis().GetXmin(),
                        h_sig.GetXaxis().GetXmax(),
                    ),
                ],
            )
            # (re-draw component TFs with correct parameters for the legend)
            _g1_tmp = ROOT.TF1(
                f"_g1t_{tag}",
                "[0]*[1]*TMath::Gaus(x,[2],[3],1)",
                h_sig.GetXaxis().GetXmin(),
                h_sig.GetXaxis().GetXmax(),
            )
            _g2_tmp = ROOT.TF1(
                f"_g2t_{tag}",
                "[0]*(1-[1])*TMath::Gaus(x,[4],[5],1)",
                h_sig.GetXaxis().GetXmin(),
                h_sig.GetXaxis().GetXmax(),
            )
            for fi in (_g1_tmp, _g2_tmp):
                for p in range(6):
                    fi.SetParameter(p, f_sig_fit.GetParameter(p))
            _g1_tmp.SetLineColor(ROOT.kGreen + 2)
            _g1_tmp.SetLineStyle(2)
            _g1_tmp.SetLineWidth(2)
            _g2_tmp.SetLineColor(ROOT.kMagenta)
            _g2_tmp.SetLineStyle(3)
            _g2_tmp.SetLineWidth(2)
            save_shape_plot(
                h_sig,
                f_sig_fit,
                f"Signal MC  {sym},  {eta_str}",
                os.path.join(OUTPUT_DIR, f"sig_{tag}.png"),
                extra_tfs=[_g1_tmp, _g2_tmp],
            )

            #Background shape fit on MC
            print(f"  [{charge}] Fitting background shape ...")
            f_bkg_fit, bkg_shape = fit_bkg_shape(h_bkg, tag)
            save_shape_plot(
                h_bkg,
                f_bkg_fit,
                f"Background MC  {sym},  {eta_str}",
                os.path.join(OUTPUT_DIR, f"bkg_{tag}.png"),
            )

            #Normalization fit on data
            print(f"  [{charge}] Fitting data normalisations ...")
            f_data_fit, N_sig, eN_sig, N_bkg, eN_bkg = fit_data_norms(
                h_data, sig_shape, bkg_shape, tag
            )
            xmin = h_data.GetXaxis().GetXmin()
            xmax = h_data.GetXaxis().GetXmax()
            f_g1, f_g2, f_erf = _component_tfs(f_data_fit, xmin, xmax)
            save_data_plot(
                h_data,
                f_data_fit,
                f_g1,
                f_g2,
                f_erf,
                f"Data  {sym},  {eta_str}",
                os.path.join(OUTPUT_DIR, f"data_{tag}.png"),
            )

            print(f"    N_sig = {N_sig:.1f} +/- {eN_sig:.1f}")
            print(f"    N_bkg = {N_bkg:.1f} +/- {eN_bkg:.1f}")
            N_sig_charges.append(N_sig)
            eN_sig_charges.append(eN_sig)

        # Asymmetry from signal yields
        N_plus, eN_plus = N_sig_charges[0], eN_sig_charges[0]
        N_minus, eN_minus = N_sig_charges[1], eN_sig_charges[1]
        denom = N_plus + N_minus
        if abs(denom) < 1e-9:
            print("  WARNING: zero signal yield, skipping asymmetry")
            asym_vals.append(0.0)
            asym_errs.append(0.0)
            continue

        A = (N_plus - N_minus) / denom
        dA_dNp = 2.0 * N_minus / denom**2
        dA_dNm = -2.0 * N_plus / denom**2
        eA = np.sqrt((dA_dNp * eN_plus) ** 2 + (dA_dNm * eN_minus) ** 2)
        print(f"  --> Asymmetry A = {A:.4f} +/- {eA:.4f}")
        asym_vals.append(A)
        asym_errs.append(eA)

    for tf in (tf_sig, tf_bkg, tf_data):
        tf.Close()

    # ── Asymmetry summary plot ─────────────────────────────────────────────────
    x = np.array(eta_centers, dtype=float)
    ex = np.array(eta_errs, dtype=float)
    y = np.array(asym_vals, dtype=float)
    ey = np.array(asym_errs, dtype=float)

    gr = ROOT.TGraphErrors(
        N_ETA,
        x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        y.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ex.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ey.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
    )
    gr.SetTitle("W charge asymmetry vs |#eta|")
    gr.GetXaxis().SetTitle("|#eta| bin centre")
    gr.GetYaxis().SetTitle("A = (N_{+} #minus N_{#minus}) / (N_{+} + N_{#minus})")
    gr.SetMarkerStyle(21)
    gr.SetMarkerSize(1.2)
    gr.SetMarkerColor(ROOT.kBlack)
    gr.SetLineColor(ROOT.kBlack)
    gr.SetLineWidth(2)

    c_asym = ROOT.TCanvas("c_asym", "Charge asymmetry", 800, 600)
    c_asym.SetLeftMargin(0.13)
    margin = 3 * float(np.max(ey)) + 0.02
    gr.GetYaxis().SetRangeUser(float(np.min(y)) - margin, float(np.max(y)) + margin)
    gr.Draw("AP")

    line = ROOT.TLine(ETA_BINS[0], 0.0, ETA_BINS[-1], 0.0)
    line.SetLineStyle(2)
    line.SetLineColor(ROOT.kGray + 1)
    line.Draw()

    asym_out = os.path.join(OUTPUT_DIR, "charge_asymmetry_vs_eta.png")
    c_asym.SaveAs(asym_out)
    print(f"\nSaved asymmetry plot: {asym_out}")
    c_asym.Close()

    # Summary table
    print("\n" + "=" * 60)
    print(f"{'Eta bin':^20}  {'A':^10}  {'delta A':^10}")
    print("=" * 60)
    for i in range(N_ETA):
        lo, hi = ETA_BINS[i], ETA_BINS[i + 1]
        print(
            f"[{lo:.1f}, {hi:.1f}]{'':>10}  {asym_vals[i]:+.4f}    {asym_errs[i]:.4f}"
        )
    print("=" * 60)


if __name__ == "__main__":
    main()
