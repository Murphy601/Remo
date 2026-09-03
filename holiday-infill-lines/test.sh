set +e
export CARGO_TERM_COLOR=never

if [ -f /app/Cargo.toml ]; then
  cd /app
elif [ -f Cargo.toml ]; then
  :
fi

python3 - << 'PY'
import json, os, re, subprocess, time
from pathlib import Path

root = Path("/app") if Path("/app/Cargo.toml").exists() else Path.cwd()
os.chdir(root)

pattern = re.compile(r"^test (.+) \.\.\. (ok|FAILED|ignored|failed)")
results = {}


def run_cargo(args):
    proc = subprocess.run(
        args,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    text = proc.stdout or ""
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        name, raw = match.group(1), match.group(2).lower()
        if raw == "ok":
            status = "passed"
        elif raw == "ignored":
            status = "skipped"
        else:
            status = "failed"
        results[name] = status
    return text, proc.returncode


log_a, _ = run_cargo(["cargo", "test", "--all-targets", "--", "--test-threads=1"])
log_b, _ = run_cargo(["cargo", "test", "--doc", "--", "--test-threads=1"])

tests = []
passed = failed = skipped = 0
for name, status in sorted(results.items()):
    tests.append(
        {
            "name": name,
            "status": status,
            "duration": 0,
            "rawStatus": status,
        }
    )
    if status == "passed":
        passed += 1
    elif status == "skipped":
        skipped += 1
    else:
        failed += 1

now = int(time.time() * 1000)
ctrf = {
    "results": {
        "tool": {"name": "cargo"},
        "summary": {
            "tests": len(tests),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pending": 0,
            "other": 0,
            "start": now,
            "stop": now,
        },
        "tests": tests,
    }
}

payload = json.dumps(ctrf, indent=2)
destinations = [
    Path("ctrf.json"),
    Path("/logs/ctrf.json"),
    Path("/logs/verifier/ctrf.json"),
    Path("/eval_assets/ctrf.json"),
]
for dest in destinations:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(payload)
    except OSError:
        pass

Path("/tmp/cargo-test.log").write_text(log_a + "\n" + log_b)
print(f"wrote {len(tests)} test results ({passed} passed, {failed} failed, {skipped} skipped)")
PY
