import ROOT
import os.path
from utils.Samples import samp

# ROOT.gROOT.Reset()
ROOT.gROOT.SetStyle("Plain")
ROOT.gStyle.SetPalette(1)
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch()  # don't pop up canvases
ROOT.TH1.SetDefaultSumw2()
ROOT.TH1.AddDirectory(False)


def setStyle(histo, color, style=0, fill=0):
    histo.GetXaxis().SetLabelFont(42)
    histo.GetYaxis().SetLabelFont(42)
    histo.GetXaxis().SetTitleFont(42)
    histo.GetYaxis().SetTitleFont(42)
    histo.GetXaxis().SetTitleOffset(0.9)
    histo.GetYaxis().SetTitleOffset(1.2)
    histo.SetTitleFont(42)
    histo.SetTitle("")
    if color != ROOT.kRed:
        histo.SetLineColor(1)
    else:
        histo.SetLineColor(color)
    histo.SetLineWidth(1)
    histo.SetLineStyle(style)
    histo.SetFillColor(color)
    histo.SetFillStyle(fill)
    if fill == 0:
        histo.SetMarkerStyle(23)
        histo.SetMarkerSize(1.1)
    nEvts = (
        histo.GetXaxis().GetXmax() - histo.GetXaxis().GetXmin()
    ) / histo.GetNbinsX()
    histo.GetYaxis().SetTitle("Events/" + str.format("{0:.2f}", nEvts))


def setStyleStack(hs, options=""):
    hs.Draw(options)
    hs.GetHistogram().GetXaxis().SetLabelFont(42)
    hs.GetHistogram().GetYaxis().SetLabelFont(42)
    hs.GetHistogram().GetXaxis().SetTitleFont(42)
    hs.GetHistogram().GetYaxis().SetTitleFont(42)
    hs.GetHistogram().GetXaxis().SetTitleOffset(0.9)
    hs.GetHistogram().GetYaxis().SetTitleOffset(1.0)
    hs.GetHistogram().SetTitleFont(42)
    hs.GetHistogram().SetTitle("")
    hs.GetHistogram().GetXaxis().SetLabelSize(0.05)
    hs.GetHistogram().GetYaxis().SetLabelSize(0.05)
    hs.GetHistogram().GetXaxis().SetTitleSize(0.06)
    hs.GetHistogram().GetYaxis().SetTitleSize(0.06)
    nEvts = (
        hs.GetHistogram().GetXaxis().GetXmax() - hs.GetHistogram().GetXaxis().GetXmin()
    ) / hs.GetHistogram().GetNbinsX()
    hs.GetHistogram().GetYaxis().SetTitle(
        "Number of events / " + str.format("{0:.2f}", nEvts)
    )


def setStyleLegend(leg):
    leg.SetNColumns(3)
    leg.SetFillColor(0)
    leg.SetTextSize(0.045)
    leg.SetTextFont(42)


def getStack(var, samples, excludeSig=False):
    hs = ROOT.THStack(var, "")
    leg = ROOT.TLegend(0.47, 0.65, 0.89, 0.89)
    setStyleLegend(leg)

    for s in samples:
        if not os.path.exists(os.path.join("results", s + "_histos.root")):
            print(
                "File "
                + s
                + "_histos.root does not exist. Please, check to have processed the corresponding sample"
            )
            continue
        else:
            if excludeSig and s == "ttbar":
                continue
            f = ROOT.TFile(os.path.join("results", s + "_histos.root"))
            h = f.Get(var)
            setStyle(h, samp[s], 1, 1001)
            hs.Add(h, "HIST")
            leg.AddEntry(h, s, "f")

    return (hs, leg)


def plotVar(var, samples, isData=False, logScale=False):
    c = ROOT.TCanvas()
    if logScale:
        c.SetLogy()
    hs = getStack(var, samples)[0]
    leg = getStack(var, samples)[1]
    hs.Draw()
    ### Superimposing signal events (ttbar) to visualise its shape
    if not os.path.exists(os.path.join("results", "ttbar_histos.root")):
        print(
            "File ttbar_histos.root does not exist. Please, check to have processed the corresponding sample"
        )
    else:
        f = ROOT.TFile(os.path.join("results", "ttbar_histos.root"))
        h = f.Get(var)
        setStyle(h, samp["ttbar"], 0, 0)
        h.SetLineColor(samp["ttbar"])
        h.SetLineWidth(2)
        h.Draw("histsame")
        leg.AddEntry(h, "ttbar", "L")

    if isData:
        if not os.path.exists(os.path.join("results", "data_histos.root")):
            print(
                "File data_histos.root does not exist. Please, check to have processed the corresponding sample"
            )
        else:
            f = ROOT.TFile(os.path.join("results", "data_histos.root"))
            h = f.Get(var)
            setStyle(h, ROOT.kBlack, 0, 0)
            h.Draw("same")
            leg.AddEntry(h, "data", "*")

    ymax = max(hs.GetStack().Last().GetMaximum(), h.GetMaximum())
    leg.Draw("SAME")
    if isData:
        hs.SetMaximum(ymax * 1.3)
        c.SaveAs(os.path.join("results", var + ".pdf"))
    else:
        c.SaveAs(os.path.join("results", var + "_MC.pdf"))


def plotVarNorm(var, samples, logScale=False):
    c = ROOT.TCanvas()
    c.cd()
    if logScale:
        c.SetLogy()

    leg = ROOT.TLegend(0.47, 0.65, 0.89, 0.89)
    setStyleLegend(leg)

    for s in samples:
        if not os.path.exists(os.path.join("results", s + "_histos.root")):
            print(
                "File "
                + s
                + "_histos.root does not exist. Please, check to have processed the corresponding sample"
            )
            continue
        else:
            f = ROOT.TFile(os.path.join("results", s + "_histos.root"))
            h = f.Get(var)
            setStyle(h, samp[s], 0, 0)
            h.SetLineColor(samp[s])
            h.SetLineWidth(2)
            if h.Integral() != 0.0:
                h.Scale(1.0 / h.Integral())
            h.Draw("histsame")
            leg.AddEntry(h, s, "l")

    leg.Draw("SAME")
    c.SaveAs(os.path.join("results", var + "_Norm_MC.pdf"))


def plotShapes(var, samples, logScale=False):
    c = ROOT.TCanvas()
    c.cd()
    if logScale:
        c.SetLogy()
    hs = getStack(var, samples, True)[0]
    leg = ROOT.TLegend(0.47, 0.65, 0.89, 0.89)
    setStyleLegend(leg)

    h_bkg = hs.GetStack().Last()
    if h_bkg.Integral() != 0.0:
        h_bkg.Scale(1.0 / h_bkg.Integral())
    setStyle(h_bkg, ROOT.kBlue, 0, 0)
    h_bkg.SetLineWidth(2)
    h_bkg.Draw("hist")
    leg.AddEntry(h_bkg, "Background", "l")

    if not os.path.exists(os.path.join("results", "ttbar_histos.root")):
        print(
            "File ttbar_histos.root does not exist. Please, check to have processed the corresponding sample"
        )

    else:
        f = ROOT.TFile(os.path.join("results", "ttbar_histos.root"))
        h = f.Get(var)
        setStyle(h, samp["ttbar"], 0, 0)
        h.SetLineColor(ROOT.kPink - 8)
        h.SetLineWidth(2)
        if h.Integral() != 0.0:
            h.Scale(1.0 / h.Integral())
        h.Draw("histsame")
        leg.AddEntry(h, "Signal (ttbar)", "L")

    leg.Draw("SAME")
    c.SaveAs(os.path.join("results", var + "_Shape_MC.pdf"))


def getBkgHisto(var, samples):
    hs = getStack(var, samples, True)[0]
    h_bkg = hs.GetStack().Last()
    setStyle(h_bkg, ROOT.kBlue, 0, 0)
    h_bkg.SetLineColor(ROOT.kBlue)
    h_bkg.SetLineWidth(2)
    ROOT.SetOwnership(h_bkg, False)
    h_bkg.SetDirectory(0)

    return h_bkg.Clone()


def getHisto(var, sample):
    h = ROOT.TH1F()
    filename = sample + "_histos.root"
    if not os.path.exists(os.path.join("results", filename)):
        print(
            "File "
            + filename
            + " does not exist. Please, check to have processed the corresponding sample"
        )

    else:
        f = ROOT.TFile(os.path.join("results", filename))
        h = f.Get(var)
        if sample == "data":
            setStyle(h, ROOT.kBlack, 0, 0)
        else:
            setStyle(h, samp[sample], 0, 0)
            h.SetLineColor(samp[sample])
            h.SetLineWidth(2)

    return h


def getSigHisto(var):
    h = getHisto(var, "ttbar")

    return h
