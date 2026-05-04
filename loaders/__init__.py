"""Generic loaders for the Phase 4.1 process wrapper.

These modules wrap the existing gid-parameterized loader functions in
load_gapseq.py / load_genomespot.py / load_mebipred.py / run_marker_blast.py
with conventions about where each tool's output files live, so the wrapper
can call a single function per stage.

The Phase 4.1 design contract: do NOT modify the existing load_*.py scripts.
They produced the test-set data correctly and remain the reproducibility
anchor. These generic loaders are NEW code that calls into them.

Usage:

    from loaders.gapseq_generic import load_gapseq_outputs
    from loaders.genomespot_generic import load_genomespot_outputs
    from loaders.marker_blast_generic import load_marker_blast_results
    from loaders.mebipred_generic import load_mebipred_outputs

    # After running the tools and producing outputs in standard locations:
    load_gapseq_outputs(gid=1000, gapseq_dir="data/user_genomes/X/gapseq")
    load_genomespot_outputs(gid=1000, predictions_tsv="data/user_genomes/X/genomespot.predictions.tsv")
    load_marker_blast_results(gid=1000, proteome_path="data/user_genomes/X/proteome.faa")
    load_mebipred_outputs(gid=1000, predictions_tsv="data/user_genomes/X/mebipred_predictions.tsv")
"""
