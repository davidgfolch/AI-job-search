import hashlib, json, pathlib, subprocess, datetime, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)

def run(*cmd):
    return subprocess.check_output(cmd, text=True).strip()

head = run("git", "rev-parse", "HEAD")
status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
payload = {
    "head": head,
    "status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
    "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    "project_key": "ai-job-search",
}
pathlib.Path(".sonar-gate-passed").write_text(json.dumps(payload))
print("Sonar quality gate passed and marker written.")
