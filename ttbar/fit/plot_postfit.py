import ROOT

ROOT.gROOT.SetBatch(True)

# --------------------------------------------------
# Input
# --------------------------------------------------
f = ROOT.TFile.Open("result/fitDiagnostics_ttbar.root")

# --------------------------------------------------
# Get postfit shapes
# --------------------------------------------------
shapes = f.Get("shapes_fit_s")
if not shapes:
    raise RuntimeError("Missing shapes_fit_s")

channel = "SR"  # IMPORTANT: match your ROOT file
dir_sr = shapes.Get(channel)

if not dir_sr:
    raise RuntimeError(f"Channel {channel} not found")

# --------------------------------------------------
# Data
# --------------------------------------------------
data = dir_sr.Get("data")

# --------------------------------------------------
# Collect processes
# --------------------------------------------------
hists = {}

for key in dir_sr.GetListOfKeys():
    name = key.GetName()
    if name == "data":
        continue
    hists[name] = key.ReadObj()

print("Processes:", list(hists.keys()))

# --------------------------------------------------
# Stack order (adapt if needed)
# --------------------------------------------------
order = ["ttbar", "wjets", "dy", "single_top", "ww", "wz", "zz"]

colors = {
    "ttbar": ROOT.kRed - 7,
    "wjets": ROOT.kGreen + 2,
    "dy": ROOT.kAzure + 2,
    "single_top": ROOT.kYellow + 2,
    "ww": ROOT.kOrange + 1,
    "wz": ROOT.kOrange - 3,
    "zz": ROOT.kMagenta + 2
}

# --------------------------------------------------
# Build stack
# --------------------------------------------------
stack = ROOT.THStack("stack", "Postfit")

total = None

for p in order:
    if p not in hists:
        continue

    h = hists[p]
    h.SetFillColor(colors.get(p, ROOT.kGray))
    h.SetLineColor(ROOT.kBlack)

    stack.Add(h)

    if total is None:
        total = h.Clone("total")
    else:
        total.Add(h)

# --------------------------------------------------
# Uncertainty band (postfit)
# --------------------------------------------------
unc = total.Clone("unc")
unc.SetFillStyle(3354)
unc.SetFillColor(ROOT.kGray + 2)
unc.SetLineColor(ROOT.kGray + 2)

# --------------------------------------------------
# Canvas
# --------------------------------------------------
c = ROOT.TCanvas("c", "", 800, 700)

stack.Draw("HIST")
unc.Draw("E2 SAME")
stack.Draw("HIST SAME")
unc.Draw("E2 SAME")

# --------------------------------------------------
# Data
# --------------------------------------------------

#data.SetLineColor(ROOT.kBlack)
data.Draw("E SAME")

# --------------------------------------------------
# CMS label
# --------------------------------------------------
latex = ROOT.TLatex()
latex.SetNDC()
latex.SetTextSize(0.04)
latex.DrawLatex(0.15, 0.92, "CMS Preliminary")

# --------------------------------------------------
# Legend
# --------------------------------------------------
leg = ROOT.TLegend(0.65, 0.55, 0.88, 0.88)
leg.AddEntry(data, "Data", "lep")

for p in order:
    if p in hists:
        leg.AddEntry(hists[p], p, "f")

leg.AddEntry(unc, "Uncertainty", "f")
leg.Draw()

# --------------------------------------------------
# Save
# --------------------------------------------------
c.SaveAs("result/postfit_ttbar.png")
c.SaveAs("result/postfit_ttbar.pdf")

print("Saved postfit plots")
