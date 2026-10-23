import argparse
import copy
import itertools
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAFE = {"round": round, "int": int, "float": float, "max": max, "min": min, "abs": abs}


def get_path(cfg, dotted):
    node = cfg
    for part in dotted.split("."):
        node = node[part]
    return node


def set_path(cfg, dotted, value):
    parts = dotted.split(".")
    node = cfg
    for part in parts[:-1]:
        node = node[part]
    if parts[-1] not in node:
        raise KeyError(f"La clave '{dotted}' no existe en el template")
    node[parts[-1]] = value


def label(key, value):
    return f"{key.split('.')[-1]}_{value}"


def eval_derived(cfg, expr):
    substituted = re.sub(r"\{([^}]+)\}", lambda m: repr(get_path(cfg, m.group(1))), expr)
    return eval(substituted, {"__builtins__": {}}, SAFE)


def build_runs(campaign):
    template = json.loads((ROOT / campaign["template"]).read_text())
    grid = campaign.get("grid", {})
    keys = list(grid)
    runs = []
    for values in itertools.product(*(grid[k] for k in keys)):
        for seed in range(campaign["baseSeed"], campaign["baseSeed"] + campaign["realizations"]):
            cfg = copy.deepcopy(template)
            for k, v in zip(keys, values):
                set_path(cfg, k, v)
            for k, expr in campaign.get("derived", {}).items():
                set_path(cfg, k, eval_derived(cfg, expr))
            cfg["seed"] = seed
            point = " ".join(label(k, v) for k, v in zip(keys, values)) or "single"
            directory = Path(campaign["outputRoot"]) / point.replace(" ", "__") / f"seed_{seed}"
            cfg["output"]["directory"] = str(directory)
            runs.append((directory, cfg))
    return runs


def run_one(args, directory, cfg, force, jar):
    out = ROOT / directory
    if (out / "summary.txt").exists() and not force:
        return directory, "saltada (ya existe)"
    out.mkdir(parents=True, exist_ok=True)
    if force:
        cfg["output"]["overwrite"] = True
    config_path = out / "config.json"
    config_path.write_text(json.dumps(cfg, indent=2))
    with open(out / "run.log", "w") as log:
        proc = subprocess.run(["java", "-jar", str(jar), str(config_path)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    return directory, "ok" if proc.returncode == 0 else f"ERROR (ver {directory}/run.log)"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("campaign")
    p.add_argument("--jobs", type=int)
    p.add_argument("--jar", default="simulation/target/sds_tp4_g8.jar")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    campaign = json.loads(Path(args.campaign).read_text())
    runs = build_runs(campaign)
    jobs = args.jobs or campaign.get("jobs", 1)
    print(f"Campana '{campaign['name']}': {len(runs)} corridas, {jobs} en paralelo")
    if args.dry_run:
        for directory, cfg in runs:
            print(f"  {directory}  seed={cfg['seed']}")
        return
    root_out = ROOT / campaign["outputRoot"]
    root_out.mkdir(parents=True, exist_ok=True)
    (root_out / "campaign.json").write_text(Path(args.campaign).read_text())
    (root_out / "template.json").write_text((ROOT / campaign["template"]).read_text())
    jar = ROOT / args.jar
    if not jar.exists():
        sys.exit(f"No existe {jar}. Ejecutar 'mvn -q package' primero.")
    failures = 0
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(run_one, args, d, c, args.force, jar) for d, c in runs]
        for i, f in enumerate(futures, 1):
            directory, status = f.result()
            failures += status.startswith("ERROR")
            print(f"[{i}/{len(runs)}] {directory}: {status}", flush=True)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
