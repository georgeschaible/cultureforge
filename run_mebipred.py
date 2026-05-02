"""Run MeBiPred on a protein FASTA and emit a TSV of per-protein predictions.

The `mymetal` package ships `mymetal.mbp.predict()` as a pipeline that loads
ANN models and does two inference passes (the 'Multi'/'Mono' generic
metal-binding classifiers and the 10 per-ion models). It prints results to
stdout in a bespoke format and has no function that just returns arrays, so
we replicate the internals here to emit a clean TSV.

Output columns (one row per protein):
    protein_id  mono_prob  multi_prob  mbp_prob  Ca Co Cu Fe K Mg Mn Na Ni Zn

  mbp_prob = max(mono, multi)   (overall "is metal-binding" score)
  per-metal columns are probabilities 0.0-1.0 from the T2<metal> models.
"""

import os
import sys
import numpy as np

# Silence TensorFlow chatter + force the legacy (Keras 2) code path, since the
# MeBiPred models are serialised in the Keras 2.2.4 JSON format that Keras 3
# cannot load.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ["TF_USE_LEGACY_KERAS"] = "1"

from tf_keras.models import model_from_json   # noqa: E402
from mymetal.load_dicts import precoded_kmer_list, precoded_dict_list  # noqa: E402
from mymetal.iof import load_encode  # noqa: E402
import mymetal.mbp as _mbp  # noqa: F401 — just to populate sys.modules

METALS = ["Ca", "Co", "Cu", "Fe", "K", "Mg", "Mn", "Na", "Ni", "Zn"]


def _load_ann(attribute):
    cwd = os.path.dirname(os.path.abspath(
        sys.modules["mymetal.mbp"].__file__))
    json_path = os.path.join(cwd, "ModelPersistency",
                             f"ANNmodel{attribute}.json")
    h5_path = os.path.join(cwd, "ModelPersistency",
                           f"ANNmodel{attribute}.h5")
    with open(json_path) as f:
        model = model_from_json(f.read())
    model.load_weights(h5_path)
    model.compile(loss="binary_crossentropy",
                  optimizer="rmsprop", metrics=["accuracy"])
    return model


def predict_metals(fasta_path):
    """Return list of dicts {id, mbp, mono, multi, Ca, Co, ..., Zn}."""
    kmer_list = precoded_kmer_list()
    dict_list = precoded_dict_list()

    # load_encode returns a list of lists: [[protein_id, float, float, ...], ...]
    rows = load_encode(fasta_path, dict_list, kmer_list, "2")
    ids = [r[0] for r in rows]
    b = np.array([r[1:] for r in rows], dtype=float)

    print(f"  encoded {len(ids)} proteins → feature matrix {b.shape}",
          file=sys.stderr)

    # Generic "binds any metal" classifiers
    multi_model = _load_ann("Multi")
    mono_model = _load_ann("Mono")
    multi = multi_model.predict(b, verbose=0).flatten()
    mono = mono_model.predict(b, verbose=0).flatten()

    # Per-metal classifiers take augmented features (original + mono + multi)
    stacked = np.hstack((b, multi.reshape(-1, 1), mono.reshape(-1, 1)))
    preds = {}
    for ion in METALS:
        m = _load_ann("T2" + ion.upper())
        preds[ion] = m.predict(stacked, verbose=0).flatten()
        print(f"  predicted {ion:2s}: mean={preds[ion].mean():.3f}  "
              f"≥0.5={int((preds[ion] >= 0.5).sum())}", file=sys.stderr)

    rows = []
    for i, pid in enumerate(ids):
        row = {
            "protein_id": str(pid),
            "mono_prob": float(mono[i]),
            "multi_prob": float(multi[i]),
            "mbp_prob": float(max(mono[i], multi[i])),
        }
        for ion in METALS:
            row[ion] = float(preds[ion][i])
        rows.append(row)
    return rows


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: run_mebipred.py <proteins.faa> <out.tsv>")
    fasta_path, out_path = sys.argv[1], sys.argv[2]
    rows = predict_metals(fasta_path)
    cols = ["protein_id", "mbp_prob", "mono_prob", "multi_prob"] + METALS
    with open(out_path, "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(
                str(r["protein_id"]) if k == "protein_id"
                else f"{r[k]:.4f}" for k in cols
            ) + "\n")
    print(f"  wrote {len(rows)} predictions → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
