from MyAnalysis import MyAnalysis
from ROOT import TTree, TFile
from Plotter import plotVar, plotVarNorm, plotShapes


### Instantiation of an object of kind MyAnalysis for each single sample
TT = MyAnalysis("ttbar")
TT.processEvents()

DY = MyAnalysis("dy")
DY.processEvents()

QCD = MyAnalysis("qcd")
QCD.processEvents()

SingleTop = MyAnalysis("single_top")
SingleTop.processEvents()

WJets = MyAnalysis("wjets")
WJets.processEvents()

WW = MyAnalysis("ww")
WW.processEvents()

ZZ = MyAnalysis("zz")
ZZ.processEvents()

WZ = MyAnalysis("wz")
WZ.processEvents()

Data = MyAnalysis("data")
Data.processEvents()


samples = ["qcd", "zz", "wz", "ww", "single_top", "dy", "wjets", "ttbar"]


vars = ["NIsoMu", "Muon_Pt"]

for v in vars:
    print("Variable: ", v)
    ### plotShapes (variable, samples,logScale )
    plotShapes(v, samples, True)
    ### plotVar(variable, samples,isData, logScale )
    plotVar(v, samples, True, True)
