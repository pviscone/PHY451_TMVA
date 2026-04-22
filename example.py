from MyAnalysis import MyAnalysis
from Plotter import plotVar, plotShapes
from train_BDT import train_BDT, plot_score_distribution

signals = {}
backgrounds = {}

input_features = [
    "NJet",
    "Alt$(Jet_Px[0], -999)",
    "Alt$(Jet_Px[1], -999)",
    "Alt$(Jet_Px[2], -999)",
    "Alt$(Jet_Px[3], -999)",
    "Alt$(Jet_Py[0], -999)",
    "Alt$(Jet_Py[1], -999)",
    "Alt$(Jet_Py[2], -999)",
    "Alt$(Jet_Py[3], -999)",
    "Alt$(Jet_Pz[0], -999)",
    "Alt$(Jet_Pz[1], -999)",
    "Alt$(Jet_Pz[2], -999)",
    "Alt$(Jet_Pz[3], -999)",
    "Alt$(Jet_E[0], -999)",
    "Alt$(Jet_E[1], -999)",
    "Alt$(Jet_E[2], -999)",
    "Alt$(Jet_E[3], -999)",
    "Alt$(Jet_btag[0], -999)",
    "Alt$(Jet_btag[1], -999)",
    "Alt$(Jet_btag[2], -999)",
    "Alt$(Jet_btag[3], -999)",
    "Alt$(Jet_ID[0], -999)",
    "Alt$(Jet_ID[1], -999)",
    "Alt$(Jet_ID[2], -999)",
    "Alt$(Jet_ID[3], -999)",
    "NMuon",
    "Alt$(Muon_Px[0], -999)",
    "Alt$(Muon_Px[1], -999)",
    "Alt$(Muon_Py[0], -999)",
    "Alt$(Muon_Py[1], -999)",
    "Alt$(Muon_Pz[0], -999)",
    "Alt$(Muon_Pz[1], -999)",
    "Alt$(Muon_E[0], -999)",
    "Alt$(Muon_E[1], -999)",
    "Alt$(Muon_Charge[0], -999)",
    "Alt$(Muon_Charge[1], -999)",
    "Alt$(Muon_Iso[0], -999)",
    "Alt$(Muon_Iso[1], -999)",
    "NElectron",
    "Alt$(Electron_Px[0], -999)",
    "Alt$(Electron_Px[1], -999)",
    "Alt$(Electron_Py[0], -999)",
    "Alt$(Electron_Py[1], -999)",
    "Alt$(Electron_Pz[0], -999)",
    "Alt$(Electron_Pz[1], -999)",
    "Alt$(Electron_E[0], -999)",
    "Alt$(Electron_E[1], -999)",
    "Alt$(Electron_Charge[0], -999)",
    "Alt$(Electron_Charge[1], -999)",
    "Alt$(Electron_Iso[0], -999)",
    "Alt$(Electron_Iso[1], -999)",
    "MET_px",
    "MET_py",
]

for signal in ["ttbar"]:
    signals[signal] = MyAnalysis(signal)
    signals[signal].preprocessEvents()

for background in ["qcd", "zz", "wz", "ww", "single_top", "dy", "wjets"]:
    backgrounds[background] = MyAnalysis(background)
    backgrounds[background].preprocessEvents()

train_BDT(signals, backgrounds, input_features, max_depth=8, nTrees=50, train_frac=0.2)
plot_score_distribution()

samples = {**signals, **backgrounds}

Data = MyAnalysis("data")
Data.preprocessEvents()
Data.evaluateBDT(input_features)
Data.processEvents()

for sample in samples.values():
    sample.evaluateBDT(input_features)
    sample.processEvents()

vars = ["NIsoMu", "Muon_Pt", "BDTscore"]
for v in vars:
    print("Variable: ", v)
    plotShapes(v, list(samples.keys()), True)
    plotVar(v, list(samples.keys()), True, True)
