"""Advanced Intelligence layer: deterministic analysis built on top of the
already-extracted, already-validated data from both pipelines
(``services.parsers`` for RSE, ``services.documents`` for generic
documents). Nothing in this package calls an LLM or invents a number —
every module here reads values that already exist in ``extracted_data`` (or
computes a plain pandas/NumPy aggregate over them) and reports where the
value came from, so every finding stays traceable back to the source
document. See ``bundle.build_analysis`` for the single entry point the API
view uses.
"""
