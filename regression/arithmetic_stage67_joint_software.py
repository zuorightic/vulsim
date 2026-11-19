"""Run the released node model through the real stage-7 composition interface.

This is the software half of steps 6--7.  It uses the real stage exporter and
the existing ConditionalBoundaryProvider, but does not run synthesis or global
routing.  The old preparation directory is read-only; all successor products
are written below a new release-specific artifact root.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def run(root, preparation, model, binding, binary):
    root = root.resolve()
    if root.exists():
        raise ValueError("preserve previous joint software attempt")
    root.mkdir(parents=True)
    sources = json.loads((preparation / "sources.json").read_text())["sources"]
    selected = [r for r in sources if r["role"] == "combination_validation"]
    if len(selected) != 6:
        raise ValueError("unexpected combination-validation source count")
    tasks = []
    for row in selected:
        source_request = preparation / "sources" / row["id"] / "request.json"
        output = root / row["id"]
        command = [str(binary), str(ROOT), str(source_request), str(model), str(binding), str(output)]
        result = subprocess.run(command, text=True, capture_output=True)
        (root / (row["id"] + ".stdout")).write_text(result.stdout)
        (root / (row["id"] + ".stderr")).write_text(result.stderr)
        if result.returncode:
            raise RuntimeError(f"stage exporter failed for {row['id']}: {result.stderr[-2000:]}")
        export = output / "export.json"
        document = json.loads(export.read_text())
        if document.get("full_D_ready") is not False or document.get("price_used_for_placement") is not False:
            raise ValueError("stage exporter changed placement/full-D gate")
        if document.get("operator_candidate_sha256") != sha(model):
            raise ValueError("released model identity missing from stage export")
        if document.get("S_binding_sha256") != sha(binding):
            raise ValueError("S binding identity missing from stage export")
        tasks.append(dict(id=row["id"], request_sha256=sha(source_request), export_sha256=sha(export),
                          arithmetic_nodes=document["arithmetic_nodes"], variants=len(document["variants"])))
    write(root / "manifest.json", dict(version="step67-joint-software-v1", status="passed_stage_export",
        preparation=str(preparation), preparation_sources_sha256=sha(preparation / "sources.json"),
        model=str(model), model_sha256=sha(model), S_binding=str(binding), S_binding_sha256=sha(binding),
        binary=str(binary), binary_sha256=sha(binary), tasks=tasks, physical_calls=0,
        zero_G_qualified=False, full_D_ready=False))
    print(json.dumps(dict(status="passed_stage_export", sources=len(tasks), placements=len(tasks) * 2,
                          physical_calls=0, full_D_ready=False), ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.preparation, args.model, args.binding, args.binary)
