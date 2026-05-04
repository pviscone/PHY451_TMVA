import ROOT
from utils.Samples import samp
from utils.rdfUtils import (
    FilterCollection,
    SortCollection,
    DefineFromIndex,
    definePtEtaPhiM,
)
import os

ROOT.EnableImplicitMT()

to_plot = set()


class MyAnalysis(object):
    _hist_files_created = set()  # Track which histogram files have been created

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

    def define_pt_eta_phi_m(self):
        # define MET pt
        self.rdf = self.rdf.Define("MET_pt", "sqrt(MET_px*MET_px + MET_py*MET_py)")

        # Define 4-momentum and related variables
        self.rdf = definePtEtaPhiM(self.rdf, "Muon")
        self.rdf = definePtEtaPhiM(self.rdf, "Jet")
        self.rdf = definePtEtaPhiM(self.rdf, "Electron")
        return self.rdf

    def preprocessEvents(self):
        self.rdf = self.define_pt_eta_phi_m()
        #! ============== Trigger selection ==============
        self.rdf = self.rdf.Filter("triggerIsoMu24")

        #! ================ Jet selection ================
        jetPtCut = 15
        njetCut = 2

        self.rdf = FilterCollection(
            self.rdf,
            "Jet",
            mask=f"Jet_ID == 1 && Jet_pt > {jetPtCut}",
        ).Filter(f"NJet >= {njetCut}")
        # reorder jets by pt
        self.rdf = SortCollection(self.rdf, "Jet", sort_by="Jet_pt")

        #! ================ Muon selection ================
        ###  - Select events with at least 1 isolated muon
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
        ).Filter("NMuon > 0")  # to select events with at least 1 isolated muon
        # reorder muons by pt
        self.rdf = SortCollection(self.rdf, "Muon", sort_by="Muon_pt")
        # select muon with highest pt (leading muon)
        self.rdf = DefineFromIndex(
            self.rdf,
            "Muon",
            new_col="LeadingMuon",
            index="ROOT::VecOps::ArgMax(Muon_pt)",
        )

        #! ============= Observables definition ============

    def processEvents(self):
        # Implement additional cuts
        self.runHistos()
        self.saveHistos()

    def defineHisto(self, branch, label, axis, weight="EventWeight"):
        to_plot.add(branch)
        # Store RResultPtr - computation is lazy
        self.histograms[branch] = {
            "ptr": self.rdf.Histo1D((branch, label, *axis), branch, weight),
            "label": label,
        }

    def runHistos(self):
        self.defineHisto("NJet", "# of jets", (6, -0.5, 6.5))
        self.defineHisto("Jet_pt", "Jet pT", (50, 0.0, 200.0))
        self.defineHisto("Jet_btag", "Jet b-tag", (10, 1.0, 6.0))
        self.defineHisto("MET_pt", "MET pT", (25, 0.0, 300.0))
        self.defineHisto("LeadingMuon_pt", "Leading Muon pT", (50, 0.0, 200.0))
        self.defineHisto(
            "LeadingMuon_relIso", "Leading Muon relative isolation", (25, 0.0, 0.3)
        )
        self.defineHisto("NMuon", "# of isolated muons", (5, 0.5, 5.5))
        self.defineHisto("BDTscore", "BDT score", (25, -1.0, 1.0))

    def saveHistos(self):
        # Trigger computation of all histograms in parallel using RunGraphs
        result_ptrs = [h["ptr"] for h in self.histograms.values()]
        ROOT.RDF.RunGraphs(result_ptrs)

        for name, h_dict in self.histograms.items():
            h = h_dict["ptr"].GetValue()
            outfilename = name + "_histos.root"
            outpath = os.path.join("results", outfilename)
            # Use RECREATE on first write to file, UPDATE on subsequent writes
            mode = (
                "RECREATE"
                if outpath not in MyAnalysis._hist_files_created
                else "UPDATE"
            )
            MyAnalysis._hist_files_created.add(outpath)
            outfile = ROOT.TFile(outpath, mode)
            outfile.cd()
            h.SetName(self.sample)
            h.SetXTitle(h_dict["label"])
            h.Write()
            outfile.Close()

    def evaluateBDT(self, input_features):
        cpp_inputs = "{" + ", ".join([f'"{feat}"' for feat in input_features]) + "}"

        cpp_code = f"""
            #ifndef BDT_DECLARED
            #define BDT_DECLARED
            TMVAEvaluator* bdt = new TMVAEvaluator("dataset/weights/BDTFactory_BDT.weights.xml", {cpp_inputs}, {{"BDT"}}, false);
            #endif
        """

        ROOT.gInterpreter.Declare(cpp_code)

        def convertExpression(expr):
            # Convert "Alt$(Jet_btag[1], -999)" to "Jet_btag.size()>1 ? Jet_btag[1] : -999"
            if expr.startswith("Alt$"):
                inner = expr[5:-1]  # Remove "Alt$(" and ")"
                var, default = inner.split(",")
                # remove whitespace
                var = var.strip()
                default = default.strip()
                base_var = var.split("[")[0]
                index = int(var.split("[")[1][:-1])
                # Cast to float to avoid narrowing conversion errors
                return (
                    f"static_cast<float>({base_var}.size()>{index} ? {var} : {default})"
                )
            else:
                return f"static_cast<float>({expr})"

        cols = [convertExpression(expr) for expr in input_features]
        cols = "{" + ", ".join(cols) + "}"

        self.rdf = self.rdf.Define("BDTscore", f"bdt->run({cols})")
