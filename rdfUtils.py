import ROOT

cpp_code = """
#ifndef __RDF_UTILS_CXX__
#define __RDF_UTILS_CXX__
ROOT::RVecF getPt(const ROOT::VecOps::RVec<ROOT::Math::PxPyPzEVector>& p4) {
    ROOT::RVecF res(p4.size());
    for (size_t i = 0; i < p4.size(); ++i)
        res[i] = p4[i].Pt();
    return res;
}
ROOT::RVecF getEta(const ROOT::VecOps::RVec<ROOT::Math::PxPyPzEVector>& p4) {
    ROOT::RVecF res(p4.size());
    for (size_t i = 0; i < p4.size(); ++i)
        res[i] = p4[i].Eta();
    return res;
}
ROOT::RVecF getPhi(const ROOT::VecOps::RVec<ROOT::Math::PxPyPzEVector>& p4) {
    ROOT::RVecF res(p4.size());
    for (size_t i = 0; i < p4.size(); ++i)
        res[i] = p4[i].Phi();
    return res;
}
ROOT::RVecF getMass(const ROOT::VecOps::RVec<ROOT::Math::PxPyPzEVector>& p4) {
    ROOT::RVecF res(p4.size());
    for (size_t i = 0; i < p4.size(); ++i)
        res[i] = p4[i].M();
    return res;
}
#endif

#ifndef CMGRDF_TMVADNNEVALUATOR_H
#define CMGRDF_TMVADNNEVALUATOR_H

#include <vector>
#include <string>
#include <exception>
#include <cassert>
#include <iostream>

#include "TMVA/Reader.h"
#include "TMVA/Tools.h"
#include "ROOT/RVec.hxx"

class TMVAEvaluator {
public:
  TMVAEvaluator(const char* weightFile,
                const std::vector<std::string>& varNames,
                const std::vector<std::string>& methodNames,
                bool verbose = false);
  // convenience constructor for single method
  TMVAEvaluator(const char* weightFile,
                const std::vector<std::string>& varNames,
                const char* methodName,
                bool verbose = false)
      : TMVAEvaluator(weightFile, varNames, std::vector<std::string>{std::string(methodName)}, verbose) {}

  // non-copyable
  TMVAEvaluator(const TMVAEvaluator&) = delete;
  TMVAEvaluator& operator=(const TMVAEvaluator&) = delete;

  // movable is disabled for simplicity (owns TMVA::Reader pointer)
  TMVAEvaluator(TMVAEvaluator&&) = delete;
  TMVAEvaluator& operator=(TMVAEvaluator&&) = delete;

  ~TMVAEvaluator() {
    if (reader_) {
      delete reader_;
      reader_ = nullptr;
    }
  }

  // Run: takes a ROOT::RVec<float> of inputs (size must match nInputs()) and returns a ROOT::RVec<float> of outputs
  // (one entry per booked method in the same order as methodNames() provided to constructor)

  unsigned int nInputs() const { return nInputs_; }
  unsigned int nOutputs() const { return nOutputs_; }
  const std::vector<std::string>& methodNames() const { return methodNames_; }
  const std::vector<std::string>& varNames() const { return varNames_; }
  ROOT::RVec<float> run(ROOT::RVec<float> in);

protected:
  std::string weightFile_;
  std::vector<std::string> varNames_;
  std::vector<std::string> methodNames_;
  std::vector<Float_t> vars_;  // storage for TMVA variables (double)
  unsigned int nInputs_;
  unsigned int nOutputs_;
  TMVA::Reader* reader_;
};


TMVAEvaluator::TMVAEvaluator(const char* weightFile,
                             const std::vector<std::string>& varNames,
                             const std::vector<std::string>& methodNames,
                             bool verbose)
    : weightFile_(weightFile),
      varNames_(varNames),
      methodNames_(methodNames),
      nInputs_(static_cast<unsigned int>(varNames.size())),
      nOutputs_(static_cast<unsigned int>(methodNames.size())),
      reader_(nullptr) {
  if (verbose)
    std::cout << "Initializing TMVAEvaluator with weights: " << weightFile_ << std::endl;
  if (nInputs_ == 0)
    throw std::logic_error("No input variable names provided to TMVAEvaluator");

  if (nOutputs_ == 0)
    throw std::logic_error("No method names provided to TMVAEvaluator");

  // Ensure TMVA tools are initialized
  TMVA::Tools::Instance();

  // create reader
  reader_ = new TMVA::Reader("!Color:!Silent");

  // create storage for variables (double as TMVA expects)
  vars_.resize(nInputs_);
  for (unsigned int i = 0; i < nInputs_; ++i)
    vars_[i] = 0.0;

  // add variables to the reader in the same order as varNames_
  for (unsigned int i = 0; i < nInputs_; ++i) {
    // TMVA::Reader::AddVariable accepts std::string and double*
    reader_->AddVariable(varNames_[i], &vars_[i]);
    if (verbose)
      std::cout << "Added variable [" << i << "] = " << varNames_[i] << std::endl;
  }

  // If you trained with spectators and want to add them, you can add AddSpectator similarly.
  // Book all requested MVA methods from the weights file.
  for (const auto& m : methodNames_) {
    // BookMVA accepts method label and path-to-weights: BookMVA(const std::string& methodLabel, const std::string& weightFile)
    reader_->BookMVA(m, weightFile_);
    if (verbose)
      std::cout << "Booked method: " << m << " from " << weightFile_ << std::endl;
  }

  if (verbose)
    std::cout << "TMVAEvaluator ready: nInputs=" << nInputs_ << " nOutputs=" << nOutputs_ << std::endl;
}

ROOT::RVec<float> TMVAEvaluator::run(ROOT::RVec<float> in) {
  if (in.size() != nInputs_)
    throw std::invalid_argument("Input vector size does not match nInputs()");

  // copy and convert inputs to double storage TMVA expects
  for (unsigned int i = 0; i < nInputs_; ++i) {
    vars_[i] = static_cast<double>(in[i]);
  }

  ROOT::RVec<float> out(nOutputs_);
  for (unsigned int j = 0; j < nOutputs_; ++j) {
    const std::string& method = methodNames_[j];
    double val = reader_->EvaluateMVA(method);
    out[j] = static_cast<float>(val);
  }
  return out;
}

#endif  // CMGRDF_TMVADNNEVALUATOR_H
"""
ROOT.gInterpreter.Declare(cpp_code)


def FilterCollection(rdf, collection, new_col=None, mask=None, indices=None):
    if mask is None:
        assert indices is not None
    else:
        assert indices is None

    columns = rdf.GetColumnNames()

    redefine = True
    if new_col is not None:
        redefine = False
        assert not any([name.startswith(new_col + "_") for name in columns])
    else:
        new_col = collection

    def define_or_redefine(name, expr, redefine):
        if redefine:
            return rdf.Redefine(name, expr)
        else:
            return rdf.Define(name, expr)

    if mask is not None:
        mask_name = f"__mask__{collection}__{new_col}"
        rdf = define_or_redefine(mask_name, mask, mask_name in columns)
        mask = mask_name

    if indices is not None:
        indices_name = f"__indices__{collection}__{new_col}"
        rdf = define_or_redefine(indices_name, indices, indices_name in columns)
        indices = indices_name

    vars = [name for name in columns if name.startswith(collection + "_")]

    for var in vars:
        target = var if redefine else var.replace(collection, new_col)
        if mask:
            rdf = define_or_redefine(target, f"{var}[{mask}]", redefine)
        if indices:
            rdf = define_or_redefine(target, f"Take({var}, {indices})", redefine)

    if mask:
        size = f"Sum({mask})"
    if indices:
        size = f"{indices}.size()"

    size_name = f"N{collection}" if redefine else f"N{new_col}"
    rdf = define_or_redefine(size_name, size, redefine)

    return rdf


def definePtEtaPhiM(rdf, collection):
    rdf = (
        rdf.Define(
            f"{collection}_p4",
            f"ROOT::VecOps::Construct<ROOT::Math::PxPyPzEVector>({collection}_Px, {collection}_Py, {collection}_Pz, {collection}_E)",
        )
        .Define(
            f"{collection}_pt",
            f"getPt({collection}_p4)",
        )
        .Define(
            f"{collection}_eta",
            f"getEta({collection}_p4)",
        )
        .Define(
            f"{collection}_phi",
            f"getPhi({collection}_p4)",
        )
        .Define(
            f"{collection}_mass",
            f"getMass({collection}_p4)",
        )
    )
    return rdf
