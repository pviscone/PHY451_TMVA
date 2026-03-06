import ROOT
from array import array
from Samples import samp
from rdfUtils import FilterCollection, definePtEtaPhiM
import os


class MyAnalysis(object):
    def __init__(self, sample):
        """The Init() function is called when an object MyAnalysis is initialised
        The tree corresponding to the specific sample is picked up
        and histograms are booked.
        """

        if sample not in samp.keys() and sample != "data":
            print(
                "Error"
            )  # RuntimeError("Sample %s not valid. please, choose among these: %s" % (sample, str(samp.keys())) )
            exit
        self.histograms = {}
        self.sample = sample
        self._file = ROOT.TFile("files/" + sample + ".root")
        self._tree = self._file.Get("events")
        self.rdf = ROOT.RDataFrame(self._tree)
        self.nEvents = self._tree.GetEntries()
        print("Number of entries for " + self.sample + ": " + str(self.nEvents))

    ### preprocessEvents/processEvents function implements the actions to perform on each event
    ### preprocessEvents run before the training of the BDT, processEvents after the training.
    ### This is the place where to implement the analysis strategy: study of most sensitive variables
    ### and signal-like event selection
    def count(self):
        return self.rdf.Count().GetValue()

    def defineBasicVariables(self):
        # define MET pt
        self.rdf = self.rdf.Define("MET_pt", "sqrt(MET_px*MET_px + MET_py*MET_py)")

        # Define 4-momentum and related variables
        self.rdf = definePtEtaPhiM(self.rdf, "Muon")
        self.rdf = definePtEtaPhiM(self.rdf, "Jet")
        self.rdf = definePtEtaPhiM(self.rdf, "Electron")
        return self.rdf

    def preprocessEvents(self):
        self.rdf = self.defineBasicVariables()

        ### Muon selection - Select events with at least 1 isolated muon
        ### with pt>25 GeV to match trigger requirements
        muonPtCut = 25.0
        muonRelIsoCut = 0.05

        # skim the muon collection
        self.rdf = self.rdf.Define("Muon_relIso", "Muon_Iso / Muon_pt")

        self.rdf = FilterCollection(
            self.rdf,
            "Muon",
            # new_col="IsoMu", # this rename the skimmed collection
            mask=f"Muon_pt > {muonPtCut} && Muon_relIso < {muonRelIsoCut}",
        )  # .Filter("NMuon > 0") #to select events with at least 1 isolated muon

    def processEvents(self):
        # Implement additional cuts
        self.runHistos()
        self.saveHistos()

    def defineHisto(self, name, label, axis, branch, weight="EventWeight"):
        # Store RResultPtr - computation is lazy
        self.histograms[name] = {
            "ptr": self.rdf.Histo1D((name, label, *axis), branch, weight),
            "label": label,
        }

    def runHistos(self):
        self.defineHisto("NJet", "# of jets", (6, -0.5, 6.5), "NJet")
        self.defineHisto("Jet_Pt", "Jet pT", (50, 0.0, 200.0), "Jet_pt")
        self.defineHisto("Jet_Btag", "Jet b-tag", (10, 1.0, 6.0), "Jet_btag")
        self.defineHisto("MET_pt", "MET pT", (25, 0.0, 300.0), "MET_pt")
        self.defineHisto("Muon_Pt", "Muon pT", (50, 0.0, 200.0), "Muon_pt")
        self.defineHisto(
            "Muon_Iso", "Muon relative isolation", (25, 0.0, 3.0), "Muon_Iso"
        )
        self.defineHisto("NMuon", "# of isolated muons", (5, 0.5, 5.5), "NMuon")
        # self.defineHisto("BDTscore", "BDT score", (25, -1.0, 1.0), "BDTscore")

    def saveHistos(self):
        # Trigger computation of all histograms in parallel using RunGraphs
        result_ptrs = [h["ptr"] for h in self.histograms.values()]
        ROOT.RDF.RunGraphs(result_ptrs)

        outfilename = self.sample + "_histos.root"
        outfile = ROOT.TFile(outfilename, "RECREATE")
        outfile.cd()
        for name, h_dict in self.histograms.items():
            h = h_dict["ptr"].GetValue()
            h.SetXTitle(h_dict["label"])
            h.Write()
        outfile.Close()

    def evaluateBDT(self, input_features):
        os.makedirs("files/BDT/evaluate", exist_ok=True)
        cols = self.rdf.GetColumnNames()
        cols = [c for c in cols if "p4" not in c and not c.startswith("Photon")]
        self.rdf.Snapshot("events", f"files/BDT/evaluate/{self.sample}.root", cols)

        file = ROOT.TFile(f"files/BDT/evaluate/{self.sample}.root")
        tree = file.Get("events")

        var_names = ROOT.std.vector("TString")()
        for feature in input_features:
            var_names.push_back(ROOT.TString(feature))
        reader = ROOT.TMVA.Reader("!Color:!Silent")
        buffers = {}

        for feat in input_features:
            buffers[feat] = array("f", [0.0])  # Reader needs 32-bit floats
            reader.AddVariable(feat, buffers[feat])

        reader.BookMVA("BDT", "dataset/weights/BDTFactory_BDT.weights.xml")

        formulas = {}
        for feat in input_features:
            formulas[feat] = ROOT.TTreeFormula(feat, feat, tree)
        scores = ROOT.RVecF()
        for entry in range(self.nEvents):
            tree.GetEntry(entry)

            for feat in input_features:
                val = formulas[feat].EvalInstance()
                buffers[feat][0] = val

            out = reader.EvaluateMVA("BDT")
            scores.push_back(out)

        self.rdf = self.rdf.Define("BDTscore", "scores[rdfentry_]")
        self.defineHisto("BDTscore", "BDT score", (25, -1.0, 1.0), "BDTscore")
