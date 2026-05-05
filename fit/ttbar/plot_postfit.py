import ROOT

# --- Configuration ---
out_name = "result/postfit_plot.pdf"

def plot_postfit(root_in, out):
    # 1. Load the workspace and the fit result
    f_ws = ROOT.TFile.Open("result/workspace.root")
    w = f_ws.Get("w")
    
    # Load fit result to get post-fit parameter values
    # Note: MultiDimFit saveFitResult outputs a RooFitResult named 'fit_mdf'
    f_fit = ROOT.TFile.Open(root_in) 
    # If you used --saveFitResult, it's inside the file as 'fit_mdf'
    fit_res = f_fit.Get("fit_mdf") 

    if fit_res:
        print("Applying post-fit floating parameters...")
        w.allVars().assignValueOnly(fit_res.floatParsFinal())
    else:
        print("Warning: Fit result not found, plotting pre-fit/default values.")

    # 2. Setup Observables
    x = w.var("CMS_th1x")
    data = w.data("data_obs")
    
    # Define processes based on your workspace output
    bkg_processes = ["dy", "single_top", "wjets", "ww", "wz", "zz"]
    sig_processes = ["ttbar"]
    all_procs = sig_processes + bkg_processes
    colors = [ROOT.kRed, ROOT.kBlue, ROOT.kGreen, ROOT.kOrange, ROOT.kCyan, ROOT.kMagenta, ROOT.kGray]

    # 3. Create Canvas
    c = ROOT.TCanvas("c", "c", 800, 700)
    stack = ROOT.THStack("stack", "Post-fit Distributions; CMS_th1x; Events")
    legend = ROOT.TLegend(0.65, 0.6, 0.88, 0.88)

    hist_map = {}

    # 4. Loop through processes to build histograms
    for i, proc in enumerate(all_procs):
        # Get the PDF and the Norm function
        pdf = w.pdf(f"shape{'Sig' if proc=='ttbar' else 'Bkg'}_{proc}_SR_rebinPdf")
        norm_func = w.function(f"n_exp_binSR_proc_{proc}")
        
        # Create a histogram from the PDF
        # We bin it according to the observable's binning
        h = pdf.createHistogram(f"h_{proc}", x, ROOT.RooFit.Binning(x.getBinning()))
        
        # Scale the normalized PDF by the post-fit yield
        postfit_yield = norm_func.getVal()
        h.Scale(postfit_yield / h.Integral() if h.Integral() > 0 else 0)
        
        # Styling
        h.SetFillColor(colors[i % len(colors)])
        h.SetLineColor(ROOT.kBlack)
        
        hist_map[proc] = h
        stack.Add(h)
        legend.AddEntry(h, proc, "f")


    # Build total MC
    h_tot = hist_map[all_procs[0]].Clone("h_tot")
    for proc in all_procs[1:]:
        h_tot.Add(hist_map[proc])
    
    # Assign uncertainties (simple: sqrt(N))
    h_tot.Sumw2(False)
    for i in range(1, h_tot.GetNbinsX()+1):
        n = h_tot.GetBinContent(i)
        h_tot.SetBinError(i, ROOT.TMath.Sqrt(n) if n > 0 else 0)
    
    # Style as uncertainty band
    h_tot.SetFillColor(ROOT.kGray+2)
    h_tot.SetFillStyle(3004)
    h_tot.SetMarkerSize(0)
    h_tot.SetLineColor(0)
    
    legend.AddEntry(h_tot, "Uncertainty", "f")

    # 5. Handle Data
    h_data = data.createHistogram("h_data", x, ROOT.RooFit.Binning(x.getBinning()))
    # Force Poisson errors instead of SumW2
    h_data.Sumw2(False)  # disable stored sum of weights^2
    for i in range(1, h_data.GetNbinsX()+1):
        n = h_data.GetBinContent(i)
        h_data.SetBinError(i, ROOT.TMath.Sqrt(n) if n > 0 else 0)
    h_data.SetMarkerStyle(20)
    h_data.SetLineColor(ROOT.kBlack)
    legend.AddEntry(h_data, "Data", "pe")

    # 6. Draw
    stack.Draw("HIST")
    h_tot.Draw("SAME E2")
    h_data.Draw("SAME E1")
    legend.Draw()

    c.SaveAs(out)
    print(f"Plot saved to {out_name}")

if __name__ == "__main__":
    ROOT.gROOT.SetBatch(True)
    plot_postfit("result/likelihood_obs.root", "result/postfit_obs.pdf")
    plot_postfit("result/likelihood_exp.root", "result/postfit_exp.pdf")
    plot_postfit("result/likelihood_obs_stat_only.root", "result/postfit_obs_stat_only.pdf")
    plot_postfit("result/likelihood_exp_stat_only.root", "result/postfit_exp_stat_only.pdf")

