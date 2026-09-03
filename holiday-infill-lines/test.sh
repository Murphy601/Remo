# >>> RUN TESTS (task-specific) <<<
# cargo-nextest has no --junit flag; JUnit is enabled via a config file.
# IDs the grader reads are classname.name, e.g.
#   plumbline::infill_command.a_missing_config_is_refused
export CARGO_TERM_COLOR=never

if [ -f /app/Cargo.toml ]; then
  cd /app
elif [ -f Cargo.toml ]; then
  :
else
  echo "ERROR: Cargo.toml not found" >&2
  exit 6
fi

mkdir -p /logs/verifier

write_nextest_cfg() {
  local dest="$1"
  local junit="$2"
  cat > "$dest" <<EOF
[profile.default]
failure-output = "immediate"
success-output = "never"
fail-fast = false

[profile.default.junit]
path = "$junit"
store-success-output = false
store-failure-output = true
EOF
}

CFG_BASE="$(mktemp)"
CFG_NEW="$(mktemp)"
write_nextest_cfg "$CFG_BASE" "/logs/verifier/base.xml"
write_nextest_cfg "$CFG_NEW" "/logs/verifier/new.xml"

# Existing suite (P2P) -> base.xml; new infill tests (F2P) -> new.xml.
# Nonzero exit from failing tests is normal; the grader reads the XML.
set +e
cargo nextest run \
  --workspace --all-targets --no-fail-fast \
  --config-file "$CFG_BASE" \
  -E 'not (binary_id(plumbline::infill_command) | binary_id(plumbline::infill_edges))' \
  > /logs/verifier/base.log 2>&1
base_rc=$?
cargo nextest run \
  --workspace --all-targets --no-fail-fast \
  --config-file "$CFG_NEW" \
  -E 'binary_id(plumbline::infill_command) | binary_id(plumbline::infill_edges)' \
  > /logs/verifier/new.log 2>&1
new_rc=$?
set -e

rm -f "$CFG_BASE" "$CFG_NEW"
echo "base nextest rc=$base_rc; new nextest rc=$new_rc (nonzero on failing tests is normal; graded from XML)"
# >>> END RUN TESTS <<<
