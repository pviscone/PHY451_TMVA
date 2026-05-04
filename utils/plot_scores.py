#!/usr/bin/env python3

import ROOT


def plot_score_distributions():
    # Open TMVA results file
    tmva_file = ROOT.TFile("TMVA_BDT_training.root", "READ")

    # Access the dataset directory and trees
    dataset_dir = tmva_file.Get("dataset")

    # Get test trees
    test_signal_tree = dataset_dir.Get("TestTree_Signal")
    test_background_tree = dataset_dir.Get("TestTree_Background")

    # Get train trees
    train_signal_tree = dataset_dir.Get("TrainTree_Signal")
    train_background_tree = dataset_dir.Get("TrainTree_Background")

    # Create histograms for BDT scores
    nbins = 50
    xmin = -1.0
    xmax = 1.0

    # Test histograms
    h_test_sig = ROOT.TH1F("h_test_sig", "Test Signal", nbins, xmin, xmax)
    h_test_bkg = ROOT.TH1F("h_test_bkg", "Test Background", nbins, xmin, xmax)

    # Train histograms
    h_train_sig = ROOT.TH1F("h_train_sig", "Train Signal", nbins, xmin, xmax)
    h_train_bkg = ROOT.TH1F("h_train_bkg", "Train Background", nbins, xmin, xmax)

    # Fill histograms with BDT scores
    test_signal_tree.Draw("BDT>>h_test_sig", "", "goff")
    test_background_tree.Draw("BDT>>h_test_bkg", "", "goff")
    train_signal_tree.Draw("BDT>>h_train_sig", "", "goff")
    train_background_tree.Draw("BDT>>h_train_bkg", "", "goff")

    # Normalize all histograms to area = 1
    if h_test_sig.Integral() > 0:
        h_test_sig.Scale(1.0 / h_test_sig.Integral())
    if h_test_bkg.Integral() > 0:
        h_test_bkg.Scale(1.0 / h_test_bkg.Integral())
    if h_train_sig.Integral() > 0:
        h_train_sig.Scale(1.0 / h_train_sig.Integral())
    if h_train_bkg.Integral() > 0:
        h_train_bkg.Scale(1.0 / h_train_bkg.Integral())

    # Set histogram styles
    # Test signal: red filled hatched
    h_test_sig.SetFillColor(ROOT.kRed)
    h_test_sig.SetFillStyle(3004)  # hatched pattern
    h_test_sig.SetLineColor(ROOT.kRed)
    h_test_sig.SetLineWidth(2)

    # Train signal: red marker only
    h_train_sig.SetMarkerColor(ROOT.kRed)
    h_train_sig.SetMarkerStyle(20)
    h_train_sig.SetMarkerSize(0.8)
    h_train_sig.SetLineColor(ROOT.kRed)
    h_train_sig.SetFillStyle(0)  # no fill

    # Test background: blue filled hatched
    h_test_bkg.SetFillColor(ROOT.kBlue)
    h_test_bkg.SetFillStyle(3004)  # hatched pattern
    h_test_bkg.SetLineColor(ROOT.kBlue)
    h_test_bkg.SetLineWidth(2)

    # Train background: blue marker only
    h_train_bkg.SetMarkerColor(ROOT.kBlue)
    h_train_bkg.SetMarkerStyle(20)
    h_train_bkg.SetMarkerSize(0.8)
    h_train_bkg.SetLineColor(ROOT.kBlue)
    h_train_bkg.SetFillStyle(0)  # no fill

    # Set ROOT batch mode to prevent GUI windows
    ROOT.gROOT.SetBatch(True)

    # Create first plot - Signal distributions
    c1 = ROOT.TCanvas("c1", "BDT Score Distribution - Signal", 800, 600)
    c1.cd()

    # Find maximum for proper scaling
    max_val = max(h_test_sig.GetMaximum(), h_train_sig.GetMaximum())

    h_test_sig.SetMaximum(max_val * 1.2)
    h_test_sig.GetXaxis().SetTitle("BDT Score")
    h_test_sig.GetYaxis().SetTitle("Normalized Events")
    h_test_sig.SetTitle("BDT Score Distribution - Signal")

    # Draw signal histograms
    h_test_sig.Draw("HIST")
    h_train_sig.Draw("P SAME")

    # Add legend
    leg1 = ROOT.TLegend(0.2, 0.7, 0.5, 0.9)
    leg1.SetFillStyle(0)  # transparent
    leg1.SetBorderSize(0)
    leg1.AddEntry(h_test_sig, "Test Signal", "f")
    leg1.AddEntry(h_train_sig, "Train Signal", "p")
    leg1.Draw()

    c1.SaveAs("BDT_Signal_Distribution.pdf")
    c1.SaveAs("BDT_Signal_Distribution.png")

    # Create second plot - Background distributions
    c2 = ROOT.TCanvas("c2", "BDT Score Distribution - Background", 800, 600)
    c2.cd()

    # Find maximum for proper scaling
    max_val = max(h_test_bkg.GetMaximum(), h_train_bkg.GetMaximum())

    h_test_bkg.SetMaximum(max_val * 1.2)
    h_test_bkg.GetXaxis().SetTitle("BDT Score")
    h_test_bkg.GetYaxis().SetTitle("Normalized Events")
    h_test_bkg.SetTitle("BDT Score Distribution - Background")

    # Draw background histograms
    h_test_bkg.Draw("HIST")
    h_train_bkg.Draw("P SAME")

    # Add legend
    leg2 = ROOT.TLegend(0.5, 0.7, 0.8, 0.9)
    leg2.SetFillStyle(0)  # transparent
    leg2.SetBorderSize(0)
    leg2.AddEntry(h_test_bkg, "Test Background", "f")
    leg2.AddEntry(h_train_bkg, "Train Background", "p")
    leg2.Draw()

    c2.SaveAs("BDT_Background_Distribution.pdf")
    c2.SaveAs("BDT_Background_Distribution.png")

    # Optional: Create combined plot with all 4 distributions
    c3 = ROOT.TCanvas("c3", "BDT Score Distribution - Combined", 800, 600)
    c3.cd()

    # Find overall maximum for scaling
    max_val = max(
        h_test_sig.GetMaximum(),
        h_train_sig.GetMaximum(),
        h_test_bkg.GetMaximum(),
        h_train_bkg.GetMaximum(),
    )

    h_test_sig.SetMaximum(max_val * 1.2)
    h_test_sig.SetTitle("BDT Score Distribution - All Samples")

    # Draw all histograms
    h_test_sig.Draw("HIST")
    h_test_bkg.Draw("HIST SAME")
    h_train_sig.Draw("P SAME")
    h_train_bkg.Draw("P SAME")

    # Add combined legend
    leg3 = ROOT.TLegend(0.15, 0.6, 0.45, 0.9)
    leg3.SetFillStyle(0)
    leg3.SetBorderSize(0)
    leg3.AddEntry(h_test_sig, "Test Signal", "f")
    leg3.AddEntry(h_train_sig, "Train Signal", "p")
    leg3.AddEntry(h_test_bkg, "Test Background", "f")
    leg3.AddEntry(h_train_bkg, "Train Background", "p")
    leg3.Draw()

    c3.SaveAs("BDT_Combined_Distribution.pdf")
    c3.SaveAs("BDT_Combined_Distribution.png")

    print("Score distribution plots saved:")
    print("- BDT_Signal_Distribution.pdf/png")
    print("- BDT_Background_Distribution.pdf/png")
    print("- BDT_Combined_Distribution.pdf/png")

    tmva_file.Close()


if __name__ == "__main__":
    print("Generating BDT score distribution plots...")
    plot_score_distributions()
