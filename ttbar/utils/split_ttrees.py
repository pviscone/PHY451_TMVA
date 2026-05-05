#!/usr/bin/env python3
"""Split one or more ROOT files (TTree) into train/test TTrees.

Creates two ROOT files with TTrees named the same as the input tree and
copies entries randomly (fixed seed for reproducibility).

Usage:
  python3 split_ttrees.py --inputs files/my.root files/other.root \
      --tree events --train_out train.root --test_out test.root --train_frac 0.8
"""

import argparse
import ROOT


def build_chain(files, tree_name="events"):
    chain = ROOT.TChain(tree_name)
    for f in files:
        chain.Add(f)
    return chain


def split_chain(chain, train_frac=0.8, train_out=None, test_out=None, seed=123):
    ROOT.gRandom.SetSeed(seed)

    n = int(chain.GetEntries())
    print(f"Total entries in chain: {n}")

    # Prepare output files (if provided)
    train_f = ROOT.TFile(train_out, "RECREATE") if train_out else None
    test_f = ROOT.TFile(test_out, "RECREATE") if test_out else None

    # Create empty cloned trees (preserve branch structure)
    if train_f:
        train_f.cd()
    train_tree = chain.CloneTree(0)

    if test_f:
        test_f.cd()
    test_tree = chain.CloneTree(0)

    ntrain = 0
    ntest = 0

    for i in range(n):
        chain.GetEntry(i)
        if ROOT.gRandom.Uniform() < train_frac:
            train_tree.Fill()
            ntrain += 1
        else:
            test_tree.Fill()
            ntest += 1

    print(f"Split: train={ntrain}, test={ntest}")

    # Write and close files if requested
    if train_f:
        train_f.cd()
        train_tree.Write()
        train_f.Close()
        print(f"Wrote training tree to {train_out}")
    if test_f:
        test_f.cd()
        test_tree.Write()
        test_f.Close()
        print(f"Wrote testing tree to {test_out}")

    return train_tree, test_tree


def main():
    parser = argparse.ArgumentParser(description="Split TTree into train/test TTrees")
    parser.add_argument(
        "--inputs", nargs="+", required=True, help="input ROOT files (can be multiple)"
    )
    parser.add_argument(
        "--tree",
        default="events",
        help="name of the tree inside the files (default: events)",
    )
    parser.add_argument(
        "--train_out", default="train.root", help="output file for training tree"
    )
    parser.add_argument(
        "--test_out", default="test.root", help="output file for testing tree"
    )
    parser.add_argument(
        "--train_frac",
        type=float,
        default=0.8,
        help="fraction of entries to keep for training",
    )
    parser.add_argument(
        "--seed", type=int, default=123, help="random seed for reproducibility"
    )

    args = parser.parse_args()

    chain = build_chain(args.inputs, tree_name=args.tree)
    split_chain(
        chain,
        train_frac=args.train_frac,
        train_out=args.train_out,
        test_out=args.test_out,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
