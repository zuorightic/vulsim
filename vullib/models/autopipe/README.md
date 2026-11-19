# Frozen v10 model resources

`asap7/response.json` is the original complete diagnostic response, including the frozen v10 arithmetic/G functions and S/shared/control parameters. Its bytes retain SHA-256 `de067c6983fe92eb7b5771b014f7881483bc2be06a5f70eddd3bc521208bc575`. `asap7/characterization.json` supplies the original body-budget to characterization-period contract.

`nangate45/` contains the frozen N5/N6 arithmetic, state/shared, characterization and cell-cover parameters. Only deployment paths and their enclosing file hashes changed during relocation; fitted numerical payloads did not change. The arithmetic package explicitly references the same retained ASAP7 response.

`profiles/` and `fixed_op_width_v1.json` preserve the original profile and static-cost bytes. `workloads.json` contains the registered finite structural grammars. `manifest.json` binds the shipped resource files.

These resources preserve the original diagnostic qualification and extrapolation limits. They provide offline prediction; they do not include a PDK or replace physical timing analysis. R1–R5 solver changes are excluded.

Build, generate and test commands: [model usage](../../../doc/autopipe.md).
