#ifndef RDFFUNCTIONS_H
#define RDFFUNCTIONS_H

#include "ROOT/RVec.hxx"
#include "Math/LorentzVector.h"
#include "Math/PxPyPzE4D.h"

using LV = ROOT::Math::LorentzVector<ROOT::Math::PxPyPzE4D<double>>;
using RVecLV = ROOT::RVec<LV>;
using RVecF = ROOT::RVec<float>;

RVecF getPt(const RVecLV& p4vec) {
    RVecF result;
    for (const auto& p4 : p4vec) {
        result.push_back(static_cast<float>(p4.Pt()));
    }
    return result;
}

RVecF getEta(const RVecLV& p4vec) {
    RVecF result;
    for (const auto& p4 : p4vec) {
        result.push_back(static_cast<float>(p4.Eta()));
    }
    return result;
}

RVecF getPhi(const RVecLV& p4vec) {
    RVecF result;
    for (const auto& p4 : p4vec) {
        result.push_back(static_cast<float>(p4.Phi()));
    }
    return result;
}

RVecF getMass(const RVecLV& p4vec) {
    RVecF result;
    for (const auto& p4 : p4vec) {
        result.push_back(static_cast<float>(p4.M()));
    }
    return result;
}

#endif
