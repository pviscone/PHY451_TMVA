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

    outfile = ROOT.TFile("TMVA_BDT_training.root", "RECREATE")

    factory = ROOT.TMVA.Factory(
        "BDTFactory",
        outfile,
        "!V:!Silent:Color:DrawProgressBar:Transformations=D,G:AnalysisType=Classification",
    )

    dataloader = ROOT.TMVA.DataLoader("dataset")
    for var in input_features:
        dataloader.AddVariable(var, "F")

    for s in s_trees:
        dataloader.AddSignalTree(s, 1.0)

    for b in b_trees:
        # fair reweighting (instead of xsec based)
        dataloader.AddBackgroundTree(b, 1.0 / len(backgrounds))

    nSigEvents = sum([signal_obj.count() for signal_obj in signals.values()])
    nBkgEvents = sum([bg_obj.count() for bg_obj in backgrounds.values()])

    dataloader.PrepareTrainingAndTestTree(
        ROOT.TCut(""),
        f"nTrain_Signal={int(nSigEvents * train_frac)}:nTrain_Background={int(nBkgEvents * train_frac)}:nTest_Signal={int(nSigEvents * (1 - train_frac))}:nTest_Background={int(nBkgEvents * (1 - train_frac))}:SplitMode=Random:!V",
    )

    factory.BookMethod(
        dataloader,
        ROOT.TMVA.Types.kBDT,
        "BDT",
        f"!H:!V:NTrees={nTrees}:MinNodeSize=2.5%:MaxDepth={max_depth}:BoostType=AdaBoost:SeparationType=GiniIndex",
    )

    factory.TrainAllMethods()
    factory.TestAllMethods()
    factory.EvaluateAllMethods()
    outfile.Close()

    print("BDT training completed! Results saved to TMVA_BDT_training.root")


def plot_score_distribution():
    outfile = ROOT.TFile("TMVA_BDT_training.root", "READ")

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
    c.SaveAs("BDT_score.pdf")
