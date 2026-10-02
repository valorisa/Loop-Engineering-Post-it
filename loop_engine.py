#!/usr/bin/env python3
"""loop_engine.py - closed-loop producer / critic, pure stdlib (Python 3.9+).

Differences with the prompt-only version:
  * the iteration cap is enforced by the code (a for-loop), not by the model;
  * the registry is a JSON file re-read at every iteration (real persistence);
  * the critic is a separate API call (optionally another model);
  * the exit decision is computed here from per-criterion pass/fail and an
    optional shell check (tests, linter...), never from the model's own
    "status" or "% done";
  * human checkpoints are real input() prompts.

Usage:
  export ANTHROPIC_API_KEY=...            # PowerShell: $env:ANTHROPIC_API_KEY="..."
  python loop_engine.py config.json
  python loop_engine.py config.json --resume
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"

PRODUCER_SYSTEM = (
    "You are the PRODUCER in a closed loop. Output ONLY the full deliverable, "
    "no commentary. If a previous deliverable and defects are given, fix those "
    "defects and keep what already satisfies the criteria. Respect the lessons."
)
CRITIC_SYSTEM = (
    "You are an independent QUALITY CONTROLLER. Judge the deliverable strictly "
    "against each listed criterion, with a short factual evidence quote or "
    "observation. No generic praise. Reply with ONLY a JSON object:\n"
    '{"criteria":[{"id":"<id>","pass":true|false,"evidence":"..."}],'
    '"defects":["..."],"lessons":["short reusable rule", "..."]}'
)


def call_llm(model, system, user, max_tokens=4000, timeout=180):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY manquante dans l'environnement.")
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {e.code}: {detail}") from e
    return "".join(b.get("text", "") for b in data.get("content", [])
                   if b.get("type") == "text")


def extract_json(raw):
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(raw[start:end + 1])


def save_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)  # atomic: no half-written registry


def run_check(cmd, deliverable_path):
    env = dict(os.environ, LOOP_DELIVERABLE=str(deliverable_path))
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=120, env=env)
    except subprocess.TimeoutExpired:
        return False, "check_command: timeout (120 s)"
    return p.returncode == 0, (p.stdout + p.stderr)[-800:]


def producer_prompt(cfg, reg):
    parts = [f"OBJECTIVE:\n{cfg['objective']}",
             "CRITERIA:\n" + "\n".join(f"- [{c['id']}] {c['text']}" for c in cfg["criteria"])]
    if reg["lessons"]:
        parts.append("LESSONS (rules learned so far):\n" +
                     "\n".join(f"- {x}" for x in reg["lessons"][-20:]))
    if reg["deliverable"]:
        last = reg["history"][-1]
        parts.append("PREVIOUS DELIVERABLE:\n" + reg["deliverable"])
        parts.append("DEFECTS TO FIX:\n" + "\n".join(f"- {d}" for d in last["defects"]))
        if last.get("check_output"):
            parts.append("CHECK COMMAND OUTPUT (failed):\n" + last["check_output"])
    if reg["feedback"]:
        parts.append("HUMAN FEEDBACK (priority):\n" + "\n".join(f"- {f}" for f in reg["feedback"]))
    return "\n\n".join(parts)


def review(cfg, deliverable):
    prompt = ("CRITERIA:\n" + "\n".join(f"- [{c['id']}] {c['text']}" for c in cfg["criteria"])
              + f"\n\nDELIVERABLE:\n{deliverable}")
    for _ in range(2):  # one retry if the JSON is malformed
        raw = call_llm(cfg["critic_model"], CRITIC_SYSTEM, prompt, 2000)
        try:
            return extract_json(raw)
        except ValueError:
            continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    cfg.setdefault("producer_model", "claude-sonnet-5-5")
    cfg.setdefault("critic_model", "claude-opus-5-5")  # ideally another model/provider
    cfg.setdefault("max_iterations", 8)
    cfg.setdefault("checkpoint_every", 3)
    cfg.setdefault("registry_path", "registry.json")
    cfg.setdefault("output_path", "deliverable.txt")
    cfg.setdefault("check_command", "")

    reg_path, out_path = Path(cfg["registry_path"]), Path(cfg["output_path"])
    if reg_path.exists() and not args.resume:
        sys.exit(f"{reg_path} existe deja. Utilisez --resume ou supprimez-le.")
    if reg_path.exists():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
    else:
        reg = {"objective": cfg["objective"], "status": "EN COURS", "iteration": 0,
               "lessons": [], "history": [], "deliverable": "", "feedback": []}

    ids = [c["id"] for c in cfg["criteria"]]
    final = "PLAFOND ATTEINT"

    for n in range(reg["iteration"] + 1, cfg["max_iterations"] + 1):
        print(f"\n=== Iteration {n}/{cfg['max_iterations']} ===")
        try:
            deliverable = call_llm(cfg["producer_model"], PRODUCER_SYSTEM,
                                   producer_prompt(cfg, reg), 4000).strip()
        except RuntimeError as e:
            final = f"ERREUR API: {e}"
            break
        reg["feedback"] = []  # consumed
        out_path.write_text(deliverable, encoding="utf-8")

        verdict = review(cfg, deliverable)
        if verdict is None:
            final = "ERREUR: reponse du critique non exploitable"
            break
        passed = {c.get("id"): bool(c.get("pass")) for c in verdict.get("criteria", [])}
        failed = [i for i in ids if not passed.get(i, False)]  # missing id = fail

        check_ok, check_out = True, ""
        if cfg["check_command"]:
            check_ok, check_out = run_check(cfg["check_command"], out_path)

        defects = [f"[{i}] non satisfait" for i in failed] + list(verdict.get("defects", []))
        if not check_ok:
            defects.append("check_command a echoue")
        for lesson in verdict.get("lessons", []):
            if lesson not in reg["lessons"]:
                reg["lessons"].append(lesson)

        reg["deliverable"], reg["iteration"] = deliverable, n
        reg["history"].append({"n": n, "failed": failed, "defects": defects,
                               "check_ok": check_ok,
                               "check_output": "" if check_ok else check_out})
        save_json(reg_path, reg)
        print(f"Criteres en echec: {failed or 'aucun'} | check: {'OK' if check_ok else 'KO'}")

        if not failed and check_ok:
            final = "ATTEINT - FIN DE LA BOUCLE"
            break

        if n % cfg["checkpoint_every"] == 0 and n < cfg["max_iterations"]:
            if not sys.stdin.isatty():
                final = "EN ATTENTE DE VALIDATION"
                break
            ans = input("[Entree]=continuer | s=stop | ou saisir un retour: ").strip()
            if ans.lower() == "s":
                final = "ARRETE PAR L'HUMAIN"
                break
            if ans and ans.lower() != "c":
                reg["feedback"].append(ans)
    reg["status"] = final
    save_json(reg_path, reg)
    print(f"\nStatut final: {final}\nLivrable: {out_path}\nRegistre: {reg_path}")


if __name__ == "__main__":
    main()
