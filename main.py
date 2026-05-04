from MyAnalysis import MyAnalysis, to_plot
from utils.Plotter import plotVar, plotShapes
from utils.train_BDT import train_BDT, plot_score_distribution
import os

os.makedirs("results", exist_ok=True)

signals = {}
backgrounds = {}

input_features = [
    "Alt$(Jet_pt[0], -999)",
    "MedianJet_dR",
    "InvariantMass_LeastBtaggedJets",
    "InvariantMass_LeadingMuon_MostbTaggedJet",
    "dR_LeadingMuon_MostbTaggedJet",
    "dR_LeastBtaggedJets",
    "MinInvariantMass_Jets",
    "HT",
    # "Alt$(Jet_pt[1], -999)",
    # "Alt$(Jet_pt[2], -999)",
    # "Alt$(Jet_pt[3], -999)",
    # "Alt$(Jet_eta[0], -999)",
    # "Alt$(Jet_eta[1], -999)",
    # "Alt$(Jet_eta[2], -999)",
    # "Alt$(Jet_eta[3], -999)",
    # "Alt$(Jet_phi[0], -999)",
    # "Alt$(Jet_phi[1], -999)",
    # "Alt$(Jet_phi[2], -999)",
    # "Alt$(Jet_phi[3], -999)",
    # "Alt$(Jet_btag[0], -999)",
    # "Alt$(Jet_btag[1], -999)",
    # "Alt$(Jet_btag[2], -999)",
    # "Alt$(Jet_btag[3], -999)",
    # "Alt$(Jet_ID[0], -999)",
    # "Alt$(Jet_ID[1], -999)",
    # "Alt$(Jet_ID[2], -999)",
    # "Alt$(Jet_ID[3], -999)",
    # "Alt$(Muon_pt[0], -999)",
    # "Alt$(Muon_eta[0], -999)",
    # "Alt$(Muon_phi[0], -999)",
    # "Alt$(Muon_Iso[0], -999)",
    # "NJet",
    # "NMuon",
    # "Alt$(Muon_Charge[0], -999)",
    # "Alt$(Muon_phi[1], -999)",
    # "Alt$(Muon_pt[1], -999)",
    # "Alt$(Muon_eta[1], -999)"
    # "Alt$(Muon_Charge[1], -999)",
    # "Alt$(Muon_Iso[1], -999)",
    # "NElectron",
    # "Alt$(Electron_pt[0], -999)",
    # "Alt$(Electron_pt[1], -999)",
    # "Alt$(Electron_eta[0], -999)",
    # "Alt$(Electron_eta[1], -999)",
    # "Alt$(Electron_phi[0], -999)",
    # "Alt$(Electron_phi[1], -999)",
    # "Alt$(Electron_Charge[0], -999)",
    # "Alt$(Electron_Charge[1], -999)",
    # "Alt$(Electron_Iso[0], -999)",
    # "Alt$(Electron_Iso[1], -999)",
    # "MET_pt",
]

for signal in ["ttbar"]:
    signals[signal] = MyAnalysis(signal)
    signals[signal].preprocessEvents()

for background in ["qcd", "zz", "wz", "ww", "single_top", "dy", "wjets"]:
    backgrounds[background] = MyAnalysis(background)
    backgrounds[background].preprocessEvents()

train_BDT(signals, backgrounds, input_features, max_depth=4, nTrees=35, train_frac=0.5)
plot_score_distribution()

samples = {**signals, **backgrounds}

Data = MyAnalysis("data")
Data.preprocessEvents()
Data.evaluateBDT(input_features)
Data.processEvents()

for sample in samples.values():
    sample.evaluateBDT(input_features)
    sample.processEvents()

for v in to_plot:
    print("Variable: ", v)
    plotShapes(v, list(samples.keys()), True)
    plotVar(v, list(samples.keys()), True, True)
