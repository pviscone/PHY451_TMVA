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
