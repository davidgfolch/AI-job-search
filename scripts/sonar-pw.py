import base64
import json
import os
import time
import urllib.parse
import urllib.request
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)

HOST = os.environ.get("SONAR_HOST_URL", "http://localhost:9000").rstrip("/")
SECRETS = pathlib.Path(".env.secrets")
MARKER = pathlib.Path(".sonarqube/admin_pw_set")
PROJECT_KEY = "ai-job-search"


def load_secrets():
    data = {}
    if SECRETS.exists():
        for line in SECRETS.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
    return data


def request(path, method="GET", auth=None, data=None):
    url = HOST + path
    headers = {}
    body = None
    if auth:
        headers["Authorization"] = "Basic " + base64.b64encode(auth.encode()).decode()
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()
    except Exception as exc:  # pragma: no cover - network errors
        return 0, str(exc)


def save_token(token_value, new_pw):
    lines = []
    if SECRETS.exists():
        lines = SECRETS.read_text().splitlines()
    updated = False
    for index, line in enumerate(lines):
        if line.startswith("SONAR_TOKEN="):
            lines[index] = "SONAR_TOKEN=" + token_value
            updated = True
    if not updated:
        lines.append("SONAR_TOKEN=" + token_value)
    if not SECRETS.exists():
        lines.insert(0, "SONAR_ADMIN_PASSWORD=" + new_pw)
    SECRETS.write_text("\n".join(lines) + "\n")


secrets = load_secrets()
new_pw = secrets.get("SONAR_ADMIN_PASSWORD") or os.environ.get("SONAR_ADMIN_PASSWORD") or "admin"
marker_existed = MARKER.exists()

status = ""
for _ in range(30):
    code, raw = request("/api/system/status")
    try:
        status = json.loads(raw).get("status", "")
    except Exception:
        status = ""
    if status == "UP":
        break
    time.sleep(5)

if status != "UP":
    print("Error: SonarQube did not become ready within 150s.")
    raise SystemExit(1)


def configure_quality_gate():
    gate_name = "AI Job Search 90 Coverage"
    code, _ = request("/api/qualitygates/create", "POST", auth="admin:" + new_pw, data={"name": gate_name})
    if code in (200, 409):
        request("/api/qualitygates/create_condition", "POST", auth="admin:" + new_pw, data={
            "gateName": gate_name, "metric": "coverage", "op": "LT", "error": "90"
        })
        request("/api/qualitygates/select", "POST", auth="admin:" + new_pw, data={
            "gateName": gate_name, "projectKey": PROJECT_KEY
        })
        print("Quality gate configured (>= 90% coverage).")
    else:
        print(f"Warning: could not create quality gate (HTTP {code}).")
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.touch()


if marker_existed:
    print("SonarQube already configured.")
    configure_quality_gate()
    raise SystemExit(0)

code, raw = request("/api/users/change_password", "POST", auth="admin:admin", data={
    "login": "admin", "previousPassword": "admin", "password": new_pw
})
if code == 200:
    print("Admin password set.")
else:
    print(f"Admin password already set or change not required (HTTP {code}).")

code, raw = request("/api/user_tokens/generate", "POST", auth="admin:" + new_pw, data={"name": "ai-job-search-local-ci"})
token_value = ""
try:
    token_value = json.loads(raw).get("token", "")
except Exception:
    token_value = ""
if token_value:
    print("Token generated.")
    save_token(token_value, new_pw)
else:
    print("Warning: could not generate token. Generate one manually at " + HOST)

configure_quality_gate()
print("SonarQube bootstrap complete.")
