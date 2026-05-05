import ROOT
import os


def train_BDT(
    signals, backgrounds, input_features, max_depth=8, nTrees=50, train_frac=0.2
):
    os.makedirs("files/BDT/train/signals", exist_ok=True)
    os.makedirs("files/BDT/train/backgrounds", exist_ok=True)

    # Snapshot RDataFrames to TTrees for TMVA
    for name, signal in signals.items():
        cols = signal.rdf.GetColumnNames()
        cols = [c for c in cols if "p4" not in c and not c.startswith("Photon")]
        signal.rdf.Snapshot("events", f"files/BDT/train/signals/{name}.root", cols)

    for name, background in backgrounds.items():
        cols = background.rdf.GetColumnNames()
        cols = [c for c in cols if "p4" not in c and not c.startswith("Photon")]
        background.rdf.Snapshot(
            "events", f"files/BDT/train/backgrounds/{name}.root", cols
        )

    s_files = [
        ROOT.TFile(f"files/BDT/train/signals/{name}.root") for name in signals.keys()
    ]
    b_files = [
        ROOT.TFile(f"files/BDT/train/backgrounds/{name}.root")
        for name in backgrounds.keys()
    ]

    s_trees = [f.Get("events") for f in s_files]
    b_trees = [f.Get("events") for f in b_files]

    outfile = ROOT.TFile(os.path.join("results", "TMVA_BDT_training.root"), "RECREATE")

    factory = ROOT.TMVA.Factory(
        "BDTFactory",
        outfile,
        "!V:!Silent:Color:DrawProgressBar:Transformations=D,G:AnalysisType=Classification",
    )

    dataloader = ROOT.TMVA.DataLoader("dataset")
    for var in input_features:
        dataloader.AddVariable(var, "F")

    nSigEvents = sum([signal_obj.count() for signal_obj in signals.values()])
    nBkgEvents = sum([bg_obj.count() for bg_obj in backgrounds.values()])

    for s in s_trees:
        dataloader.AddSignalTree(s, nBkgEvents / nSigEvents)

    for b in b_trees:
        # fair reweighting (instead of xsec based)
        if b.GetEntries() > 0:
            dataloader.AddBackgroundTree(b, 1.0)
        else:
            print(
                f"Warning: Background tree {b.GetName()} has no entries and will be skipped."
            )
    dataloader.SetSignalWeightExpression("EventWeight")
    dataloader.SetBackgroundWeightExpression("EventWeight")

    dataloader.PrepareTrainingAndTestTree(
        ROOT.TCut(""),
        ROOT.TCut(""),
        f"NormMode=EqualNumEvents:nTrain_Signal={int(nSigEvents * train_frac)}:nTrain_Background={int(nBkgEvents * train_frac)}:nTest_Signal={int(nSigEvents * (1 - train_frac))}:nTest_Background={int(nBkgEvents * (1 - train_frac))}:SplitMode=Random:!V",
    )

    factory.BookMethod(
        dataloader,
        ROOT.TMVA.Types.kBDT,
        "BDT",
        f"!H:!V:NTrees={nTrees}:MinNodeSize=2.5%:MaxDepth={max_depth}:BoostType=Grad:Shrinkage=0.10:UseBaggedBoost:BaggedSampleFraction=0.5",
    )

    factory.TrainAllMethods()
    factory.TestAllMethods()
    factory.EvaluateAllMethods()
    outfile.Close()

    print("BDT training completed! Results saved to TMVA_BDT_training.root")


def plot_score_distribution():
    outfile = ROOT.TFile(os.path.join("results", "TMVA_BDT_training.root"), "READ")

    def _get_hist(path):
        h = outfile.Get(path)
        if not h:
            raise RuntimeError(f"Histogram not found: {path}")
        hc = h.Clone(path.split("/")[-1] + "_clone")
        hc.SetDirectory(0)
        return hc

    def _normalize(h):
        integral = h.Integral()
        if integral > 0:
            h.Scale(1.0 / integral)

    def _make_roc_graph(h_sig, h_bkg, name):
        n_bins = h_sig.GetNbinsX()
        sig_total = h_sig.Integral(0, n_bins + 1)
        bkg_total = h_bkg.Integral(0, n_bins + 1)

        graph = ROOT.TGraph()
        points = []

        graph.SetPoint(0, 0.0, 0.0)
        points.append((0.0, 0.0))

        for bin_idx in range(n_bins, 0, -1):
            sig_eff = (
                0.0
                if sig_total == 0.0
                else h_sig.Integral(bin_idx, n_bins + 1) / sig_total
            )
            bkg_eff = (
                0.0
                if bkg_total == 0.0
                else h_bkg.Integral(bin_idx, n_bins + 1) / bkg_total
            )
            x = bkg_eff
            y = sig_eff
            graph.SetPoint(len(points), x, y)
            points.append((x, y))

        graph.SetPoint(len(points), 1.0, 1.0)
        points.append((1.0, 1.0))
        graph.SetName(name)

        auc = 0.0
        for idx in range(1, len(points)):
            x0, y0 = points[idx - 1]
            x1, y1 = points[idx]
            auc += 0.5 * (y0 + y1) * (x1 - x0)
        auc = max(0.0, min(1.0, auc))
        return graph, auc

    h_test_sig = _get_hist("dataset/Method_BDT/BDT/MVA_BDT_S")
    h_train_sig = _get_hist("dataset/Method_BDT/BDT/MVA_BDT_Train_S")
    h_test_bkg = _get_hist("dataset/Method_BDT/BDT/MVA_BDT_B")
    h_train_bkg = _get_hist("dataset/Method_BDT/BDT/MVA_BDT_Train_B")

    for h in (h_test_sig, h_train_sig, h_test_bkg, h_train_bkg):
        _normalize(h)
        h.SetStats(0)

    # Styles
    h_test_sig.SetFillColor(ROOT.kRed - 9)
    h_test_sig.SetFillStyle(3354)
    h_test_sig.SetLineColor(ROOT.kRed + 1)
    h_train_sig.SetLineColor(ROOT.kRed + 1)
    h_train_sig.SetMarkerColor(ROOT.kRed + 1)
    h_train_sig.SetMarkerStyle(20)
    h_train_sig.SetMarkerSize(0.9)

    h_test_bkg.SetFillColor(ROOT.kBlue - 9)
    h_test_bkg.SetFillStyle(3345)
    h_test_bkg.SetLineColor(ROOT.kBlue + 1)
    h_train_bkg.SetLineColor(ROOT.kBlue + 1)
    h_train_bkg.SetMarkerColor(ROOT.kBlue + 1)
    h_train_bkg.SetMarkerStyle(24)
    h_train_bkg.SetMarkerSize(0.9)

    c = ROOT.TCanvas("c_sig", "BDT score - signal", 800, 600)
    h_test_sig.GetXaxis().SetTitle("BDT score")
    h_test_sig.GetYaxis().SetTitle("Normalized entries")
    h_test_sig.SetTitle("Signal score distribution")
    h_test_sig.Draw("HIST")
    h_train_sig.Draw("E1 SAME")

    h_test_bkg.GetXaxis().SetTitle("BDT score")
    h_test_bkg.GetYaxis().SetTitle("Normalized entries")
    h_test_bkg.SetTitle("Background score distribution")

    h_test_sig.Draw("HIST")
    h_train_sig.Draw("E1 SAME")
    h_test_bkg.Draw("HIST SAME")
    h_train_bkg.Draw("E1 SAME")

    leg = ROOT.TLegend(0.58, 0.72, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.AddEntry(h_test_sig, "Test signal", "f")
    leg.AddEntry(h_train_sig, "Train signal", "lep")
    leg.AddEntry(h_test_bkg, "Test bkg", "f")
    leg.AddEntry(h_train_bkg, "Train bkg", "lep")
    leg.Draw()
    c.SaveAs(os.path.join("results", "BDT_score.pdf"))

    g_test_roc, auc_test = _make_roc_graph(h_test_sig, h_test_bkg, "g_test_roc")
    g_train_roc, auc_train = _make_roc_graph(h_train_sig, h_train_bkg, "g_train_roc")

    g_test_roc.SetLineColor(ROOT.kRed + 1)
    g_test_roc.SetLineWidth(2)
    g_train_roc.SetLineColor(ROOT.kBlue + 1)
    g_train_roc.SetLineWidth(2)

    c_roc = ROOT.TCanvas("c_roc", "ROC curves", 800, 600)
    frame = ROOT.TH1F(
        "frame_roc", ";Background efficiency;Signal efficiency", 100, 0.0, 1.0
    )
    frame.SetMinimum(0.0)
    frame.SetMaximum(1.05)
    frame.Draw()

    diagonal = ROOT.TLine(0.0, 0.0, 1.0, 1.0)
    diagonal.SetLineStyle(2)
    diagonal.SetLineColor(ROOT.kGray + 1)
    diagonal.Draw("same")

    g_test_roc.Draw("L SAME")
    g_train_roc.Draw("L SAME")

    leg_roc = ROOT.TLegend(0.18, 0.18, 0.46, 0.32)
    leg_roc.SetBorderSize(0)
    leg_roc.AddEntry(g_test_roc, f"Test sample (AUC={auc_test:.3f})", "l")
    leg_roc.AddEntry(g_train_roc, f"Train sample (AUC={auc_train:.3f})", "l")
    leg_roc.Draw()

    c_roc.SaveAs(os.path.join("results", "BDT_ROC.pdf"))
