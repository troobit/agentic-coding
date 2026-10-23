#!/usr/bin/env python3
"""Run next-task repeatedly through Codex's local LM Studio provider."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile


SKILLS = Path(__file__).resolve().parents[1] / "claude" / "skills"


class Halt(Exception):
    """Work cannot continue unattended."""


def rune_json(root, tasks, command, *flags):
    result = subprocess.run(
        ["rune", command, str(tasks), *flags, "--format", "json"],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    if result.returncode:
        raise Halt(f"rune {command} failed: {result.stderr.strip() or result.stdout.strip()}")
    data = json.loads(result.stdout)
    if data.get("success") is not True:
        raise Halt(f"rune {command} failed: {data.get('message', data)}")
    return data


def task_states(ledger):
    """Flatten rune list's capitalized task tree; reject unexpected schemas."""
    states = {}

    def visit(tasks):
        for task in tasks:
            task_id, status = task["ID"], task["Status"]
            if not isinstance(task_id, str) or status not in (0, 1, 2) or task_id in states:
                raise Halt("Unexpected task IDs/statuses in rune list output")
            states[task_id] = status
            visit(task.get("Children") or [])

    visit(ledger["Tasks"] or [])
    return states


def selected_tasks(selection):
    """Include descendants when inspecting a next/phase selection."""
    def visit(tasks):
        for task in tasks:
            yield task
            yield from visit(task.get("children") or [])

    tasks = selection.get("tasks") or ([selection["next_task"]] if selection.get("next_task") else [])
    return list(visit(tasks))


def select_work(root, tasks, phase, states):
    selection = rune_json(root, tasks, "next", *(["--phase"] if phase else []))
    task = selection.get("next_task")
    # Match next-task's fallback for a top-level task rather than a subtask.
    if task and "." not in task["id"] and not phase:
        selection = rune_json(root, tasks, "next", "--phase")
    selected = selected_tasks(selection)
    if not selected:
        raise Halt(f"Incomplete tasks have no ready work: {selection.get('message', 'empty selection')}")
    selected_ids = {task["id"] for task in selected}
    if all(task.get("blocked") for task in selected):
        raise Halt("All selected tasks are blocked")
    for task in selected:
        if task.get("status", "").lower() == "completed":
            continue
        # A phase can unblock its own later tasks as earlier work completes.
        if task.get("blocked") and any(
            key not in selected_ids and states.get(key) != 2
            for key in task.get("blockedBy", [])
        ):
            raise Halt(f"Task {task['id']} is blocked: {task['title']}")
        if re.match(r"\s*(?:\[STOP\]|STOP\b)", task["title"]):
            raise Halt(f"Task {task['id']} requires human review: {task['title']}")
    return selection


def make_prompt(tasks, selection):
    return f"""Use the $next-task skill for this explicit tasks file: {json.dumps(str(tasks))}.
Read these skill manifests before implementation:
- {SKILLS / 'next-task' / 'SKILL.md'}
- {SKILLS / 'rune' / 'SKILL.md'}

This is a headless local-model iteration. The external runner will start a fresh
session for the next group. Execute the selected work sequentially in this
session; do not delegate to other agents. Read the referenced spec documents,
relevant docs/agent-notes, and project instructions before editing. Resolve spec
references from the repository root, or relative to the task file when needed.
Use the explicit absolute tasks path in every rune command.

The runner selected this work using rune (do not advance beyond this selection):
{json.dumps(selection, indent=2)}

Implement only this selection and its subtasks, validate using the project's
Makefile when present, and mark work complete with rune only after validation.
Keep the task graph and numbering unchanged. Leave changes for review without
committing or pushing. Update relevant implementation notes.

Never ask a question in this unattended session. If blocked, if human approval
is needed, or if you cannot complete the selected work, write .orbit/halt in
the repository root with a one-line reason and finish with ORBIT-HALT: <reason>.
Otherwise report completed task IDs, changed files and validation, then stop.
"""


def codex_command(root, model, final_path):
    return [
        "codex", "exec", "--oss", "--local-provider", "lmstudio", "--model", model,
        "--ignore-user-config", "--ephemeral", "--json", "--sandbox", "workspace-write",
        "-c", 'approval_policy="never"', "--cd", str(root),
        "--output-last-message", str(final_path), "-",
    ]


def run_session(command, prompt, root, log, timeout):
    with log.open("w") as output:
        process = subprocess.Popen(
            command, cwd=root, stdin=subprocess.PIPE, stdout=output,
            stderr=subprocess.STDOUT, text=True, start_new_session=True,
        )
        try:
            process.communicate(prompt, timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            # Stop commands launched by the agent as well as the agent process.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise
    if process.returncode:
        raise Halt(f"Codex exited with status {process.returncode}; see {log}")
    # Some CLI versions report a failed turn without a non-zero exit code.
    with log.open() as output:
        for line in output:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and event.get("type") in ("turn.failed", "error"):
                raise Halt(f"Codex reported an error; see {log}")


def execute(args, root, tasks):
    halt_file = root / ".orbit" / "halt"
    run_dir = None
    for iteration in range(1, args.max_iterations + 1):
        if halt_file.exists():
            raise Halt(f"{halt_file}: {halt_file.read_text().strip()}")
        before = task_states(rune_json(root, tasks, "list"))
        if all(status == 2 for status in before.values()):
            print(f"All tasks complete: {tasks}")
            return 0
        selection = select_work(root, tasks, args.phase, before)
        prompt = make_prompt(tasks, selection)
        if args.dry_run:
            command = codex_command(root, args.model, Path("<iteration-dir>/final.txt"))
            print(shlex.join(command))
            print(prompt)
            return 0
        if run_dir is None:
            log_dir = tasks.parent / ".orbit" / "local-next-task"
            log_dir.mkdir(parents=True, exist_ok=True)
            run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=log_dir))
        log = run_dir / f"{iteration:03d}.jsonl"
        final = run_dir / f"{iteration:03d}.final.txt"
        (run_dir / f"{iteration:03d}.prompt.txt").write_text(prompt)
        print(f"Iteration {iteration}/{args.max_iterations}: {args.model}; log: {log}", flush=True)
        try:
            run_session(codex_command(root, args.model, final), prompt, root, log, args.timeout)
        except subprocess.TimeoutExpired:
            raise Halt(f"Iteration {iteration} timed out after {args.timeout}s; see {log}")
        message = final.read_text() if final.exists() else ""
        signal_match = re.search(r"^ORBIT-HALT:\s*(.+)", message, re.MULTILINE)
        if signal_match:
            raise Halt(signal_match[1])
        if halt_file.exists():
            raise Halt(f"{halt_file}: {halt_file.read_text().strip()}")
        after = task_states(rune_json(root, tasks, "list"))
        if before.keys() != after.keys() or any(before[key] == 2 and after[key] != 2 for key in before):
            raise Halt(f"Task IDs changed or completed work was reopened; review {log}")
        completed = [key for key in before if before[key] != 2 and after[key] == 2]
        if not completed:
            raise Halt(f"No tasks completed in iteration {iteration}; see {log}")
        print(f"Completed: {', '.join(completed)}", flush=True)
        if all(status == 2 for status in after.values()):
            print(f"All tasks complete: {tasks}")
            return 0
    raise Halt(f"Reached iteration limit ({args.max_iterations}); re-run to continue")


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", type=Path, help="Explicit path to a rune tasks.md file")
    parser.add_argument("--model", default="8-bit", help="Exact LM Studio model ID (default: 8-bit)")
    parser.add_argument("--phase", action="store_true", help="Select an entire phase per iteration")
    parser.add_argument("--max-iterations", type=positive_int, default=20)
    parser.add_argument("--timeout", type=positive_int, default=1800, help="Seconds per session (default: 1800)")
    parser.add_argument("--dry-run", action="store_true", help="Print the next invocation without calling the model or writing files")
    args = parser.parse_args(argv)
    try:
        for name in ("git", "rune", "codex"):
            if not shutil.which(name):
                raise Halt(f"Required command not found: {name}")
        for name in ("next-task", "rune"):
            if not (SKILLS / name / "SKILL.md").is_file():
                raise Halt(f"Required skill not found: {SKILLS / name / 'SKILL.md'}")
        tasks = args.tasks.expanduser().resolve(strict=True)
        result = subprocess.run(
            ["git", "-C", str(tasks.parent), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode:
            raise Halt("The tasks file must be inside a Git working tree")
        root = Path(result.stdout.strip()).resolve()
        tasks.relative_to(root)
        return execute(args, root, tasks)
    except KeyboardInterrupt:
        print("ORBIT-HALT: Interrupted; review the last iteration before resuming", file=sys.stderr)
        return 130
    except (Halt, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"ORBIT-HALT: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
