# Integration Contract Regression Gate

A lightweight CLI tool that decides whether proposed agent/tool integration changes are safe to proceed. It acts as a gatekeeper for CI/CD pipelines and orchestration agents.

## What It Does

The regression gate:
1. Takes a candidate integration change (or contract ID) plus target environment profile
2. Runs hermetic replays against the change (via existing sandbox utilities)
3. Compares outcomes against the previously approved contract snapshot
4. Outputs a structured gate report and machine-consumable remediation plan
5. Returns exit code 0 on pass, non-zero on fail

## Installation

No external dependencies - uses Python standard library only.

```bash
# Ensure the script is executable
chmod +x main.py
```

## Usage

### Basic Command

```bash
./main.py run --contract <contract_id> --change <path_to_trace> --env <profile>
```

### Arguments

- `--contract CONTRACT`: Contract identifier (e.g., `myagent-v1`) or path to a contract JSON file. If an identifier is provided, the gate looks for `contracts/{id}.json`.
- `--change PATH`: Path to the change set or trace file containing the proposed modifications
- `--env PROFILE`: Target environment profile (e.g., `staging`, `production`, `dev`)

### Exit Codes

- `0`: Gate passed - integration changes are safe
- `1`: Gate failed - regressions detected, review required
- `2`: Gate error - unable to execute (missing files, config errors)

## Output Files

### gate_report.json

Structured report containing:

```json
{
  "contract_id": "string",
  "environment": "string",
  "change": "string",
  "decision": "PASS|FAIL",
  "diffs": {
    "performance": "degraded",
    "schema": "new violations"
  },
  "generated_at": "ISO8601 timestamp"
}
```

### remediation_plan.json

Machine-consumable plan for addressing failures:

```json
{
  "gate_decision": "PASS|FAIL",
  "required_actions": [
    {
      "action": "string",
      "reason": "string",
      "details": {}
    }
  ]
}
```

## Integration Contract Snapshots

The gate compares against approved snapshots stored in:

```
./snapshots/{contract_id}/approved.json
```

Each snapshot should contain metrics like:
- `successful_calls`: baseline success count
- `total_calls`: baseline total count
- `schema_violations`: baseline violation list
- `generated_at`: timestamp of approval

If a snapshot doesn't exist, the gate treats the baseline as zero (effectively failing on any success).

## Examples

### Successful Gate

```bash
$ ./main.py run --contract myagent-v1 --change ./trace.json --env staging

Gate Decision: PASS
```

Output files:
- `gate_report.json` - detailed comparison
- `remediation_plan.json` - empty actions list or proceed

### Failed Gate

```bash
$ ./main.py run --contract myagent-v1 --change ./broken_trace.json --env staging

Gate Decision: FAIL
```

Output files will contain diffs and required actions like `{"action": "review", "details": diffs}`.

## Programmatic Use

```python
import subprocess

result = subprocess.run([
    './main.py', 'run',
    '--contract', 'mycontract',
    '--change', './changes.json',
    '--env', 'staging'
])

if result.returncode == 0:
    print("Integration changes approved")
    # Proceed with deployment
else:
    print("Integration changes rejected - see gate_report.json")
    # Abort or fix issues
```

## How It Works

1. **Snapshot Loading**: Attempts to load the approved contract snapshot from standard locations
2. **Replay Execution**: Invokes the Tool Sandbox Replayer (create-a-tool-call-sandbox-replayer-for) to execute a hermetic replay.
3. **Comparison**: Compares current results against baseline metrics
4. **Decision**: Applies thresholds (e.g., 10% success rate degradation triggers failure)
5. **Output**: Writes JSON reports and prints human summary

## Prerequisites

This gate relies on the **Tool Sandbox Replayer** script, which should be located at:

```
../create-a-tool-call-sandbox-replayer-for/main.py
```

relative to this script. If the replayer is installed elsewhere, adjust the `rpth` variable in `main.py` accordingly.

- **Contract files**: For a contract ID, the gate expects `contracts/{id}.json`. You may also provide a direct path to a JSON file by using a `.json` extension in the `--contract` argument.
- **Snapshots**: Place approved baseline reports in `snapshots/{contract_id}/approved.json`. The snapshot should contain at least `successful_calls`, `schema_violations` (list), and `idempotency_violations` (list).
- **Outputs**: The gate writes `gate_report.json` and `remediation_plan.json` to the current directory.

## License

Part of the Schemaon farm artifacts. See repository root for licensing.
