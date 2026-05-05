import ROOT
import sys
import ctypes

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)

f_obs = ROOT.TFile.Open("higgsCombine_ttbar_obs.MultiDimFit.mH120.root")
f_exp = ROOT.TFile.Open("higgsCombine_ttbar_exp.MultiDimFit.mH120.root")

if not f_obs or f_obs.IsZombie(): sys.exit("ERROR: cannot open observed file")
if not f_exp or f_exp.IsZombie(): sys.exit("ERROR: cannot open expected file")

t_obs = f_obs.Get("limit")
t_exp = f_exp.Get("limit")

print(f"Observed entries: {t_obs.GetEntries()}")
print(f"Expected entries: {t_exp.GetEntries()}")

def make_graph(tree, label=""):
    n = tree.Draw("r:2*deltaNLL", "deltaNLL>0", "goff")
    if n <= 0:
        sys.exit(f"ERROR: no scan points with deltaNLL>0 in {label}. "
                 f"Did you run --algo grid? Tree has {tree.GetEntries()} entries total.")

    v1 = tree.GetV1()
    v2 = tree.GetV2()

    pairs = sorted([(v1[i], v2[i]) for i in range(n)])

    print(f"{label}: {len(pairs)} points, "
          f"r in [{pairs[0][0]:.3f}, {pairs[-1][0]:.3f}], "
          f"2dNLL in [{min(p[1] for p in pairs):.3f}, {max(p[1] for p in pairs):.3f}]")

    g = ROOT.TGraph(len(pairs))
    for i, (r, nll) in enumerate(pairs):
        g.SetPoint(i, r, nll)
    return g

g_obs = make_graph(t_obs, "observed")
g_exp = make_graph(t_exp, "expected")

g_obs.SetLineColor(ROOT.kBlack)
g_obs.SetLineWidth(2)

g_exp.SetLineColor(ROOT.kBlue)
g_exp.SetLineWidth(2)
g_exp.SetLineStyle(2)

# ── Axis range from graph using ctypes ────────────────────────────────────────
def graph_range(g):
    x, y = ctypes.c_double(), ctypes.c_double()
    xs, ys = [], []
    for i in range(g.GetN()):
        g.GetPoint(i, x, y)
        xs.append(float(x.value))
        ys.append(float(y.value))
    return xs, ys

xs_obs, ys_obs = graph_range(g_obs)
xs_exp, ys_exp = graph_range(g_exp)

all_r   = xs_obs + xs_exp
all_nll = ys_obs + ys_exp

x_min = min(all_r)   - 0.02
x_max = max(all_r)   + 0.02
y_max = min(max(all_nll), 8.0)

# ── Canvas ────────────────────────────────────────────────────────────────────
c = ROOT.TCanvas("c", "NLL scan", 800, 600)
c.SetLeftMargin(0.12)
c.SetBottomMargin(0.12)
c.SetRightMargin(0.05)
c.SetTopMargin(0.10)

frame = c.DrawFrame(x_min, 0.0, x_max, y_max)
frame.GetXaxis().SetTitle("#mu = #sigma / #sigma_{ref}")
frame.GetYaxis().SetTitle("-2 #Delta ln #it{L}")
frame.GetXaxis().SetTitleSize(0.05)
frame.GetYaxis().SetTitleSize(0.05)
frame.GetXaxis().SetTitleOffset(1.0)
frame.GetYaxis().SetTitleOffset(1.1)
frame.GetXaxis().SetLabelSize(0.04)
frame.GetYaxis().SetLabelSize(0.04)

line_68 = ROOT.TLine(x_min, 1.0, x_max, 1.0)
line_68.SetLineColor(ROOT.kGray + 1)
line_68.SetLineStyle(3)
line_68.SetLineWidth(1)
line_68.Draw()

line_95 = ROOT.TLine(x_min, 4.0, x_max, 4.0)
line_95.SetLineColor(ROOT.kGray + 1)
line_95.SetLineStyle(3)
line_95.SetLineWidth(1)
line_95.Draw()

line_sm = ROOT.TLine(1.0, 0.0, 1.0, y_max)
line_sm.SetLineColor(ROOT.kRed)
line_sm.SetLineStyle(2)
line_sm.SetLineWidth(1)
line_sm.Draw()

g_obs.Draw("LP SAME")
g_exp.Draw("LP SAME")

lat = ROOT.TLatex()
lat.SetTextSize(0.035)
lat.SetTextColor(ROOT.kGray + 2)
if y_max > 1.2: lat.DrawLatex(x_max - 0.08, 1.08, "68% CL")
if y_max > 4.2: lat.DrawLatex(x_max - 0.08, 4.08, "95% CL")

leg = ROOT.TLegend(0.65, 0.65, 0.92, 0.82)
leg.SetBorderSize(0)
leg.SetFillStyle(0)
leg.SetTextSize(0.04)
leg.AddEntry(g_obs, "Observed", "L")
leg.AddEntry(g_exp, "Expected (#mu=1)", "L")
leg.Draw()

cms = ROOT.TLatex()
cms.SetNDC(); cms.SetTextFont(61); cms.SetTextSize(0.05)
cms.DrawLatex(0.12, 0.92, "CMS")

cms_sup = ROOT.TLatex()
cms_sup.SetNDC(); cms_sup.SetTextFont(52); cms_sup.SetTextSize(0.04)
cms_sup.DrawLatex(0.21, 0.92, "Preliminary")

lumi_label = ROOT.TLatex()
lumi_label.SetNDC(); lumi_label.SetTextFont(42)
lumi_label.SetTextSize(0.04); lumi_label.SetTextAlign(31)

c.RedrawAxis()
c.SaveAs("nll_scan.pdf")
c.SaveAs("nll_scan.png")
print("Saved nll_scan.pdf and nll_scan.png")
