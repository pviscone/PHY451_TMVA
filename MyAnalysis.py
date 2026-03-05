import ROOT
from array import array
from Samples import samp
import re


class MyAnalysis(object):
    def __init__(self, sample):
        """The Init() function is called when an object MyAnalysis is initialised
        The tree corresponding to the specific sample is picked up
        and histograms are booked.
        """

        self._tree = ROOT.TTree()
        if sample not in samp.keys() and sample != "data":
            print(
                "Error"
            )  # RuntimeError("Sample %s not valid. please, choose among these: %s" % (sample, str(samp.keys())) )
            exit
        self.histograms = {}
        self.sample = sample
        self._file = ROOT.TFile("files/" + sample + ".root")
        self._file.cd()
        tree = self._file.Get("events")
        self._tree = tree
        self.nEvents = self._tree.GetEntries()
        print("Number of entries for " + self.sample + ": " + str(self.nEvents))

        ### Book histograms
        self.bookHistos()

    def getTree(self):
        return self._tree

    def getHistos(self):
        return self.histograms

    def bookHistos(self):
        h_nJet = ROOT.TH1F("NJet", "#of jets", 6, -0.5, 6.5)
        h_nJet.SetXTitle("%# of jets")
        self.histograms["NJet"] = h_nJet

        h_nJetFinal = ROOT.TH1F("NJetFinal", "#of jets", 6, -0.5, 6.5)
        h_nJetFinal.SetXTitle("%# of jets")
        self.histograms["NJetFinal"] = h_nJetFinal

        h_MuonIso = ROOT.TH1F("Muon_Iso", "Muon Isolation", 25, 0.0, 3.0)
        h_MuonIso.SetXTitle("Muon Isolation")
        self.histograms["Muon_Iso"] = h_MuonIso

        h_NIsoMu = ROOT.TH1F("NIsoMu", "Number of isolated muons", 5, 0.5, 5.5)
        h_NIsoMu.SetXTitle("Number of isolated muons")
        self.histograms["NIsoMu"] = h_NIsoMu

        h_MuonPt = ROOT.TH1F("Muon_Pt", "Muon P_T", 50, 0.0, 200.0)
        h_MuonPt.SetXTitle("Muon P_T")
        self.histograms["Muon_Pt"] = h_MuonPt

        h_METpt = ROOT.TH1F("MET_Pt", "MET P_T", 25, 0.0, 300.0)
        h_METpt.SetXTitle("MET P_T")
        self.histograms["MET_Pt"] = h_METpt

        h_JetPt = ROOT.TH1F("Jet_Pt", "Jet P_T", 50, 0.0, 200.0)
        h_JetPt.SetXTitle("Jet P_T")
        self.histograms["Jet_Pt"] = h_JetPt

        h_JetBtag = ROOT.TH1F("Jet_Btag", "Jet B tag", 10, 1.0, 6.0)
        h_JetBtag.SetXTitle("Jet B tag")
        self.histograms["Jet_btag"] = h_JetBtag

        h_NBtag = ROOT.TH1F("NBtag", "Jet B tag", 4, 0.5, 4.5)
        h_NBtag.SetXTitle("Number of B tagged jets")
        self.histograms["NBtag"] = h_NBtag

        h_BDT = ROOT.TH1F("BDTscore", "BDT score", 25, -1.0, 1.0)
        h_BDT.SetXTitle("BDT score")
        self.histograms["BDTscore"] = h_BDT

    def saveHistos(self):
        outfilename = self.sample + "_histos.root"
        outfile = ROOT.TFile(outfilename, "RECREATE")
        outfile.cd()
        for h in self.histograms.values():
            h.Write()
        outfile.Close()

    ### processEvent function implements the actions to perform on each event
    ### This is the place where to implement the analysis strategy: study of most sensitive variables
    ### and signal-like event selection

    def preprocessEvent(self, entry):
        tree = self.getTree()
        tree.GetEntry(entry)
        w = tree.EventWeight

        ### Muon selection - Select events with at least 1 isolated muon
        ### with pt>25 GeV to match trigger requirements
        muonPtCut = 25.0
        muonRelIsoCut = 0.05
        nIsoMu = 0

        for m in range(tree.NMuon):
            muon = ROOT.TLorentzVector(
                tree.Muon_Px[m], tree.Muon_Py[m], tree.Muon_Pz[m], tree.Muon_E[m]
            )
            self.histograms["Muon_Iso"].Fill(tree.Muon_Iso[m], w)
            if muon.Pt() > muonPtCut and (tree.Muon_Iso[m] / muon.Pt()) < muonRelIsoCut:
                nIsoMu += 1
                self.histograms["Muon_Pt"].Fill(muon.Pt(), w)
        self.histograms["NIsoMu"].Fill(nIsoMu, w)

    ### processEvents run the function processEvent on each event stored in the tree
    def preprocessEvents(self):
        nevts = self.nEvents
        for i in range(nevts):
            self.preprocessEvent(i)

    def processEvent(self, entry):
        tree = self.getTree()
        tree.GetEntry(entry)
        w = tree.EventWeight

        # Implement additional cuts

    def processEvents(self):
        nevts = self.nEvents
        for i in range(nevts):
            self.processEvent(i)
        self.saveHistos()

    def evaluateBDT(self, input_features):
        var_names = ROOT.std.vector("TString")()
        for feature in input_features:
            var_names.push_back(ROOT.TString(feature))
        reader = ROOT.TMVA.Reader("!Color:!Silent")
        buffers = {}

        for feat in input_features:
            buffers[feat] = array("f", [0.0])  # Reader needs 32-bit floats
            reader.AddVariable(feat, buffers[feat])

        reader.BookMVA("BDT", "dataset/weights/BDTFactory_BDT.weights.xml")

        tree = self.getTree()
        self.friend_tree = ROOT.TTree("additional", "Friend tree with BDT scores")

        bdt_output = array("f", [0.0])
        bdt_branch = self.friend_tree.Branch("BDT_output", bdt_output, "BDT_output/F")

        w = tree.EventWeight
        formulas = {}
        for feat in input_features:
            formulas[feat] = ROOT.TTreeFormula(feat, feat, tree)
        for entry in range(self.nEvents):
            tree.GetEntry(entry)

            for feat in input_features:
                val = formulas[feat].EvalInstance()
                buffers[feat][0] = val

            out = reader.EvaluateMVA("BDT")
            bdt_output[0] = out
            self.histograms["BDTscore"].Fill(out, w)
            bdt_branch.Fill()

        tree.AddFriend(self.friend_tree)
