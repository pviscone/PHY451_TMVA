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
        jetPtCut = 45
        njetCut = 2

        self.rdf = FilterCollection(
            self.rdf,
            "Jet",
            mask=f"Jet_ID == 1 && Jet_pt > {jetPtCut}",
        ).Filter(f"NJet >= {njetCut}")
        # reorder jets by pt
        self.rdf = SortCollection(self.rdf, "Jet", sort_by="Jet_pt")
        # select up to 4 jets (with highest pt)
        self.rdf = FilterCollection(
            self.rdf,
            "Jet",
            indices="ROOT::VecOps::Range(NJet > 4 ? 4 : NJet)",
        )

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
            mask=f"Muon_pt > {muonPtCut} && Muon_relIso < {muonRelIsoCut}",  # removed transition region
        ).Filter("NMuon > 0")  # to select events with at least 1 isolated muon
        # reorder muons by pt
        self.rdf = SortCollection(self.rdf, "Muon", sort_by="Muon_pt")
        # select muon with highest pt (leading muon)
        self.rdf = DefineFromIndex(
            self.rdf,
            "Muon",
            new_col="LeadingMuon",
            index="ROOT::VecOps::ArgMax(Muon_pt)",
        ).Filter("abs(LeadingMuon_eta) < 1.479 || abs(LeadingMuon_eta) > 1.566")
        # remove events with leading muon in the transition region between barrel and endcap

        #! ============= Observables definition ============
        self.rdf = self.rdf.Define(
            "MedianJet_dR",
            """
            ROOT::RVecF dRs;
            auto comb = ROOT::VecOps::Combinations(Jet_eta, 2);
            for (size_t &i1 : comb[0]) {
                for (size_t &i2 : comb[1]) {
                    float dR = ROOT::VecOps::DeltaR(Jet_eta[i1], Jet_eta[i2], Jet_phi[i1], Jet_phi[i2]);
                    dRs.push_back(dR);
                }
            }
            // Return median dR or -1 if no combinations
            if (dRs.size() == 0) {
                return (float) -1.0;
            }
            std::sort(dRs.begin(), dRs.end());
            if (dRs.size() % 2 == 1) {
                return (float) dRs[dRs.size() / 2];
            } else {
                return (float) 0.5 * (dRs[dRs.size() / 2 - 1] + dRs[dRs.size() / 2]);
            }
            """,
        )

        self.rdf = self.rdf.Define(
            "InvariantMass_LeastBtaggedJets",
            """
            if (NJet < 2) {return (float) -1.0;}
            ROOT::RVecI sorted_indices = ROOT::VecOps::Argsort(Jet_btag);
            return ROOT::VecOps::InvariantMasses(
                ROOT::RVecF{Jet_pt[sorted_indices[0]]},
                ROOT::RVecF{Jet_eta[sorted_indices[0]]},
                ROOT::RVecF{Jet_phi[sorted_indices[0]]},
                ROOT::RVecF{Jet_mass[sorted_indices[0]]},
                ROOT::RVecF{Jet_pt[sorted_indices[1]]},
                ROOT::RVecF{Jet_eta[sorted_indices[1]]},
                ROOT::RVecF{Jet_phi[sorted_indices[1]]},
                ROOT::RVecF{Jet_mass[sorted_indices[1]]})[0]
            """,
        )

        self.rdf = self.rdf.Define(
            "MinInvariantMass_Jets",
            """
            if (NJet < 2) {return (float) -1.0;}
            auto comb = ROOT::VecOps::Combinations(Jet_eta, 2);
            ROOT::RVecF invMasses;
            for (size_t &i1 : comb[0]) {
                for (size_t &i2 : comb[1]) {
                    float invM = ROOT::VecOps::InvariantMasses(
                        ROOT::RVecF{Jet_pt[i1]},
                        ROOT::RVecF{Jet_eta[i1]},
                        ROOT::RVecF{Jet_phi[i1]},
                        ROOT::RVecF{Jet_mass[i1]},
                        ROOT::RVecF{Jet_pt[i2]},
                        ROOT::RVecF{Jet_eta[i2]},
                        ROOT::RVecF{Jet_phi[i2]},
                        ROOT::RVecF{Jet_mass[i2]})[0];
                    invMasses.push_back(invM);
                }
            }
            if (invMasses.size() == 0) {
                return (float) -1.0;
            }
            return ROOT::VecOps::Min(invMasses);
            """,
        )

        self.rdf = self.rdf.Define(
            "InvariantMass_LeadingMuon_MostbTaggedJet",
            """
            if (NJet < 1) {return (float) -1.0;}
            ROOT::RVecI sorted_indices = ROOT::VecOps::Reverse(ROOT::VecOps::Argsort(Jet_btag));
            return ROOT::VecOps::InvariantMasses(
                ROOT::RVecF{LeadingMuon_pt},
                ROOT::RVecF{LeadingMuon_eta},
                ROOT::RVecF{LeadingMuon_phi},
                ROOT::RVecF{0.105}, // muon mass
                ROOT::RVecF{Jet_pt[sorted_indices[0]]},
                ROOT::RVecF{Jet_eta[sorted_indices[0]]},
                ROOT::RVecF{Jet_phi[sorted_indices[0]]},
                ROOT::RVecF{Jet_mass[sorted_indices[0]]})[0]
            """,
        )

        self.rdf = self.rdf.Define(
            "dR_LeadingMuon_MostbTaggedJet",
            """
            if (NJet < 1) {return (float) -1.0;}
            ROOT::RVecI sorted_indices = ROOT::VecOps::Reverse(ROOT::VecOps::Argsort(Jet_btag));
            return ROOT::VecOps::DeltaR(
                LeadingMuon_eta, Jet_eta[sorted_indices[0]],
                LeadingMuon_phi, Jet_phi[sorted_indices[0]]
            );
            """,
        )

        self.rdf = self.rdf.Define(
            "dR_LeastBtaggedJets",
            """
            if (NJet < 2) {return (float) -1.0;}
            ROOT::RVecI sorted_indices = ROOT::VecOps::Argsort(Jet_btag);
            return ROOT::VecOps::DeltaR(
                Jet_eta[sorted_indices[0]], Jet_eta[sorted_indices[1]],
                Jet_phi[sorted_indices[0]], Jet_phi[sorted_indices[1]]
            );
            """,
        )

        self.rdf = self.rdf.Define("HT", "ROOT::VecOps::Sum(Jet_pt)")

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
        self.defineHisto("MedianJet_dR", "Median dR between jets", (25, 0.0, 5.0))
        self.defineHisto(
            "InvariantMass_LeastBtaggedJets",
            "Invariant mass of least b-tagged jets [GeV]",
            (25, 0.0, 200.0),
        )
        self.defineHisto(
            "InvariantMass_LeadingMuon_MostbTaggedJet",
            "Invariant mass of leading muon and most b-tagged jet [GeV]",
            (25, 0.0, 200.0),
        )

        self.defineHisto(
            "dR_LeadingMuon_MostbTaggedJet",
            "dR between leading muon and most b-tagged jet",
            (25, 0.0, 5.0),
        )

        self.defineHisto(
            "dR_LeastBtaggedJets",
            "dR between least b-tagged jets",
            (25, 0.0, 5.0),
        )
        self.defineHisto(
            "MinInvariantMass_Jets",
            "Minimum invariant mass of jet pairs [GeV]",
            (25, 0.0, 200.0),
        )
        self.defineHisto("HT", "HT [GeV]", (25, 0.0, 500.0))

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
