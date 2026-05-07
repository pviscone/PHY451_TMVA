# %%
import ROOT

from utils import definePtEtaPhiM, FilterCollection, DefineFromIndex

ROOT.EnableImplicitMT()


# %%
def run(sample, files):
    df = ROOT.RDataFrame("events", files)
    #!===================== Define pt eta phi =======================
    df = definePtEtaPhiM(df, "Muon")
    df = definePtEtaPhiM(df, "Jet")
    df = df.Define("MET_pt", "sqrt(MET_px*MET_px + MET_py*MET_py)").Define(
        "MET_phi", "atan2(MET_py, MET_px)"
    )
    #!========================== Trigger ============================
    df = df.Filter("triggerIsoMu24")

    #!===================== Select the muon =========================
    df = FilterCollection(
        df,
        "Muon",
        mask="Muon_pt > 30 && abs(Muon_eta) < 2.1 && Muon_Iso/Muon_pt < 0.05",
    ).Filter("NMuon == 1")
    df = DefineFromIndex(df, "Muon", "LeadingMuon", "ROOT::VecOps::ArgMax(Muon_pt)")

    #!================= Compute transverse mass =====================
    df = df.Define(
        "MT",
        "sqrt(2*LeadingMuon_pt*MET_pt*(1 - cos(LeadingMuon_phi - MET_phi)))",
    )

    #!====================== Get the histogram =======================

    eta_bins = [0.0, 0.4, 0.8, 1.5, 1.8, 2.1]
    charges = {"plus": 1, "minus": -1}

    output_file = ROOT.TFile(f"{sample}_histograms.root", "RECREATE")

    for i in range(len(eta_bins) - 1):
        low, high = eta_bins[i], eta_bins[i + 1]

        for name, sign in charges.items():
            bin_df = df.Filter(f"LeadingMuon_Charge == {sign}").Filter(
                f"abs(LeadingMuon_eta) >= {low} && abs(LeadingMuon_eta) < {high}"
            )

            hist_name = f"MT_eta_{i}_{name}"
            h = bin_df.Histo1D(
                (hist_name, f"MT bin {i} {name};MT [GeV];Events", 60, 0, 150),
                "MT",
                "EventWeight",
            ).GetValue()

            h.Write()

    output_file.Close()


run("data", ["../files/data.root"])
run("signal", ["../files/wjets.root"])
run(
    "background",
    [
        f"../files/{sample}.root"
        for sample in ["dy", "single_top", "ttbar", "ww", "wz", "zz"]
    ],
)
