# >>> RUN TESTS (task-specific) <<<
# The verifier image may not ship cargo-nextest. cargo test is always
# present; we turn its output into the JUnit files the grader reads.
# Node ids are classname.name, e.g. plumbline::infill_command.a_missing_config_is_refused
export CARGO_TERM_COLOR=never

if [ -f /app/Cargo.toml ]; then
  cd /app
elif [ -f Cargo.toml ]; then
  :
fi

mkdir -p /logs/verifier

python3 - << 'PY'
import os, re, subprocess, xml.etree.ElementTree as ET
from pathlib import Path

root = Path("/app") if Path("/app/Cargo.toml").exists() else Path.cwd()
os.chdir(root)
log_path = Path("/logs/verifier/run-cargo.log")
f2p_suites = {"infill_command", "infill_edges"}

proc = subprocess.run(
    ["cargo", "test", "--no-fail-fast", "--all-targets", "--color=never"],
    cwd=root,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)
out = proc.stdout or ""
try:
    log_path.write_text(out)
except OSError:
    pass
print(out, end="" if out.endswith("\n") else "\n")

run_re = re.compile(r"Running tests/([A-Za-z0-9_]+)\.rs")
test_re = re.compile(r"^test (.+) \.\.\. (ok|FAILED|ignored|failed)")
suite = None
rows = []
for line in out.splitlines():
    match = run_re.search(line)
    if match:
        suite = match.group(1)
        continue
    match = test_re.match(line.strip())
    if not match or not suite:
        continue
    name, raw = match.group(1), match.group(2).lower()
    if raw == "ok":
        status = "passed"
    elif raw == "ignored":
        status = "skipped"
    else:
        status = "failed"
    rows.append((suite, name, status, line.strip()))

def write_junit(path, selected):
    suites = {}
    for suite_name, name, status, raw in selected:
        suites.setdefault(suite_name, []).append((name, status, raw))
    testsuites = ET.Element("testsuites", name="cargo-test")
    total = failed = skipped = 0
    for suite_name, cases in sorted(suites.items()):
        classname = f"plumbline::{suite_name}"
        fails = sum(1 for _, status, _ in cases if status == "failed")
        skips = sum(1 for _, status, _ in cases if status == "skipped")
        ts = ET.SubElement(
            testsuites,
            "testsuite",
            name=classname,
            tests=str(len(cases)),
            failures=str(fails),
            skipped=str(skips),
            errors="0",
        )
        total += len(cases)
        failed += fails
        skipped += skips
        for name, status, raw in cases:
            case = ET.SubElement(
                ts, "testcase", name=name, classname=classname, time="0"
            )
            if status == "failed":
                fail = ET.SubElement(case, "failure", message=raw)
                fail.text = raw
            elif status == "skipped":
                ET.SubElement(case, "skipped")
    testsuites.set("tests", str(total))
    testsuites.set("failures", str(failed))
    testsuites.set("skipped", str(skipped))
    path.parent.mkdir(parents=True, exist_ok=True)
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        testsuites, encoding="unicode"
    )
    path.write_text(xml)

p2p = [row for row in rows if row[0] not in f2p_suites]
f2p = [row for row in rows if row[0] in f2p_suites]
write_junit(Path("/logs/verifier/base.xml"), p2p)
write_junit(Path("/logs/verifier/new.xml"), f2p)
print(
    f"wrote {len(p2p)} p2p tests to base.xml and {len(f2p)} f2p tests to new.xml "
    f"(cargo rc={proc.returncode})"
)
PY
# >>> END RUN TESTS <<<
