#!/usr/bin/env bash
# ===== AI Job Search parallel development workflow (Linux/Mac) =====
# Usage: ./scripts/dev.sh <command> [args]
#   new <name> [modules...] - clone ../ai_job_search-<name>, branch feat/<name> from master, prepare only those modules (default: all)
#   dep <pr> [modules...]   - clone ../ai_job_search-dependabot-<pr>, check out PR, prepare only those modules (default: all)
#   list                    - show sibling clones
#   checkout <branch>       - switch branch in the current clone
#   test [modules]          - run scripts/test.sh here (no args = the clone's selected modules, or everything)
#   sandbox <service> [...] - run scripts/test-sandbox.sh here
#   commit "msg"            - git add -A && git commit
#   push                    - push the current branch (never staging/master)
#   pr [title] [--base br]  - open a PR (default base: master)
#   merge [-k]              - wait for green checks, squash-merge, delete branch and clone (keep clone with -k)
#   sync                    - fast-forward staging from master and push it (run before dependabot work)
#   cleanup <name|path>     - delete a sibling clone by name, prefixed name, or path
#   status                  - branch, dirty state, ahead/behind vs master

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT="$(cd "$ROOT/.." && pwd -P)"
export UV_CACHE_DIR="${DEV_UV_CACHE_DIR:-$PARENT/.uv-cache}"
PREFIX="ai_job_search-"
GATE="${DEV_GATE_BRANCH:-staging}"
MAIN="${DEV_MAIN_BRANCH:-master}"
CMD="${1:-}"

usage() {
    awk 'NR==1 {next} /^#/ {sub(/^# ?/, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
    exit 1
}

curbranch() { git rev-parse --abbrev-ref HEAD; }

MODULES=()
add_module() {
    local m="$1"
    [[ " ${MODULES[*]-} " == *" $m "* ]] || MODULES+=("$m")
}
parse_modules() {
    MODULES=()
    [ $# -gt 0 ] || return 0
    local m
    for m in "$@"; do
        m="$(basename "$m")"
        [ -d "$ROOT/apps/$m" ] || { echo "Error: unknown module '$m'"; usage; }
        add_module "$m"
    done
    add_module commonlib
    if [[ " ${MODULES[*]} " == *" web "* ]]; then add_module e2e; fi
}
is_selected() {
    [ ${#MODULES[@]} -eq 0 ] || [[ " ${MODULES[*]} " == *" $1 "* ]]
}
save_modules() {
    local dest="$1"
    if [ ${#MODULES[@]} -gt 0 ]; then
        printf '%s\n' "${MODULES[@]}" > "$dest/.git/dev-modules"
    else
        rm -f "$dest/.git/dev-modules"
    fi
}

validate_clone() {
    local target="$1" base
    [ -d "$target" ] || return 1
    [ "$target" != "$ROOT" ] || return 1
    base="$(basename "$target")"
    case "$base" in "$PREFIX"*) ;; *) return 1 ;; esac
    [ "$(dirname "$target")" = "$PARENT" ] || return 1
}

resolve_clone() {
    local arg="$1" name candidate
    case "$arg" in
        "~") arg="$HOME" ;;
        "~/"*) arg="$HOME/${arg#\~/}" ;;
    esac
    case "$arg" in
        /*)
            [ -d "$arg" ] || return 1
            candidate="$(cd "$arg" && pwd -P)"
            ;;
        */*)
            if [ -d "$arg" ]; then
                candidate="$(cd "$arg" && pwd -P)"
            elif [ -d "$ROOT/$arg" ]; then
                candidate="$(cd "$ROOT/$arg" && pwd -P)"
            else
                return 1
            fi
            ;;
        *)
            name="${arg#$PREFIX}"
            [ -n "$name" ] || return 1
            [ -d "$PARENT/$PREFIX$name" ] || return 1
            candidate="$(cd "$PARENT/$PREFIX$name" && pwd -P)"
            ;;
    esac
    validate_clone "$candidate" || return 1
    printf '%s\n' "$candidate"
}

list_clones() {
    local dir found=false
    for dir in "$PARENT/$PREFIX"*/; do
        [ -d "$dir" ] || continue
        dir="$(cd "$dir" && pwd -P)"
        [ "$dir" = "$ROOT" ] && continue
        echo "  $(basename "$dir")"
        found=true
    done
    [ "$found" = true ] || echo "  (none)"
}

copy_runtime() {
    local dest="$1" f mod d
    # .env is tracked, so the clone already has it.
    if [ -f "$ROOT/.env.secrets" ] && [ ! -f "$dest/.env.secrets" ]; then
        cp "$ROOT/.env.secrets" "$dest/.env.secrets"
        echo "Copied .env.secrets"
    fi
    if [ -f "$ROOT/.env.local" ] && [ ! -f "$dest/.env.local" ]; then
        cp "$ROOT/.env.local" "$dest/.env.local"
        echo "Copied .env.local"
    fi
    if [ ! -f "$dest/.env.local" ]; then
        : > "$dest/.env.local"
        echo "Created empty .env.local"
    fi
    for f in "$ROOT"/apps/*/uv.lock "$ROOT"/apps/*/poetry.lock "$ROOT"/apps/*/package-lock.json; do
        [ -f "$f" ] || continue
        mod="$(basename "$(dirname "$f")")"
        is_selected "$mod" || continue
        if [ ! -f "$dest/apps/$mod/$(basename "$f")" ]; then
            mkdir -p "$dest/apps/$mod"
            cp "$f" "$dest/apps/$mod/"
            echo "Copied apps/$mod/$(basename "$f")"
        fi
    done
    for d in "$ROOT"/apps/*/node_modules; do
        [ -d "$d" ] || continue
        mod="$(basename "$(dirname "$d")")"
        is_selected "$mod" || continue
        if [ -d "$dest/apps/$mod/node_modules" ]; then continue; fi
        mkdir -p "$dest/apps/$mod"
        if ! cp -a --reflink=auto "$d" "$dest/apps/$mod/node_modules" 2>/dev/null; then
            rm -rf "$dest/apps/$mod/node_modules"
            cp -a "$d" "$dest/apps/$mod/node_modules"
        fi
        echo "Copied apps/$mod/node_modules"
    done
    if [ -f "$ROOT/.codegraph/codegraph.db" ]; then
        mkdir -p "$dest/.codegraph"
        if python3 - "$ROOT/.codegraph/codegraph.db" "$dest/.codegraph/codegraph.db" <<'PY'
import sqlite3
import sys
src = sqlite3.connect("file:" + sys.argv[1] + "?mode=ro", uri=True)
dst = sqlite3.connect(sys.argv[2])
src.backup(dst)
dst.close()
src.close()
PY
        then
            echo "Copied CodeGraph index snapshot"
        else
            echo "Warning: could not snapshot CodeGraph index"
        fi
    fi
}

prepare_runtime() {
    local dest="$1" mode="$2" dir mod
    for dir in "$dest"/apps/*; do
        [ -f "$dir/uv.lock" ] || continue
        mod="$(basename "$dir")"
        is_selected "$mod" || continue
        echo "Preparing $mod dependencies (uv, offline)..."
        if ! (cd "$dir" && uv sync --offline); then
            echo "Offline sync failed for $mod; retrying with network."
            (cd "$dir" && uv sync)
        fi
    done
    if is_selected scrapper && [ -f "$dest/apps/scrapper/poetry.lock" ]; then
        echo "Preparing scrapper dependencies (poetry)..."
        if ! (cd "$dest/apps/scrapper" && poetry install --no-interaction); then
            (cd "$dest/apps/scrapper" && poetry lock && poetry install --no-interaction)
        fi
    fi
    if [ "$mode" = "dep" ]; then
        for mod in web e2e; do
            is_selected "$mod" || continue
            [ -f "$dest/apps/$mod/package.json" ] || continue
            echo "Preparing $mod dependencies (npm, prefer offline)..."
            if ! (cd "$dest/apps/$mod" && npm ci --prefer-offline); then
                (cd "$dest/apps/$mod" && npm install --prefer-offline)
            fi
        done
    fi
    if [ -f "$dest/.codegraph/codegraph.db" ] && command -v codegraph >/dev/null 2>&1; then
        echo "Refreshing CodeGraph index in $dest..."
        codegraph sync "$dest" || echo "Warning: could not refresh CodeGraph index in $dest"
    fi
}

create_clone() {
    local name="$1"
    CLONE="$PARENT/$PREFIX$name"
    if [ -d "$CLONE" ]; then
        echo "Reusing clone: $CLONE"
    else
        echo "Cloning $(git remote get-url origin) to $CLONE..."
        git clone "$(git remote get-url origin)" "$CLONE" || { echo "Error: clone failed."; return 1; }
    fi
    copy_runtime "$CLONE"
    save_modules "$CLONE"
    cd "$CLONE"
}

stop_codegraph_daemon() {
    local pf="$1" pid
    [ -f "$pf" ] || return 0
    pid="$(sed -n 's/.*"pid": *\([0-9]*\).*/\1/p' "$pf" | head -1)"
    [ -n "$pid" ] || return 0
    if kill -0 "$pid" 2>/dev/null && ps -o args= -p "$pid" 2>/dev/null | grep -q 'codegraph'; then
        echo "Stopping CodeGraph daemon $pid (tracked by $pf)"
        kill "$pid" 2>/dev/null || true
    fi
}

# Containers leave root-owned files inside a clone (sandbox datadir, container logs,
# __pycache__), which a plain `rm -rf` as the invoking user cannot delete. Clear the tree
# as root through the mysql image (already pulled for the sandbox), then drop the dir.
clear_clone_as_root() {
    local target="$1"
    command -v docker >/dev/null 2>&1 || return 1
    docker run --rm --entrypoint sh -v "$target:/c" mysql:9 -c 'rm -rf /c/* /c/.[!.]*' >/dev/null 2>&1 || return 1
    rmdir "$target" 2>/dev/null
}

delete_clone() {
    local target="$1"
    stop_codegraph_daemon "$target/.codegraph/daemon.pid"
    cd "$target/.." || return 1
    echo "Deleting clone $target..."
    rm -rf "$target" 2>/dev/null || true
    if [ -e "$target" ]; then
        clear_clone_as_root "$target" || true
    fi
    if [ -e "$target" ]; then
        echo "Error: could not delete $target (is a terminal or CodeGraph daemon holding it, or root-owned files left by the sandbox?)."
        return 1
    fi
    echo "Clone deleted."
}

require_gh() {
    command -v gh >/dev/null 2>&1 || { echo "Error: 'gh' CLI is required. Install GitHub CLI and authenticate."; exit 1; }
}

case "$CMD" in
    new)
        NAME="${2:-}"
        [ -n "$NAME" ] || usage
        NAME="$(basename "$NAME")"
        NAME="${NAME#$PREFIX}"
        parse_modules "${@:3}"
        create_clone "$NAME"
        git fetch origin >/dev/null 2>&1 || true
        BRANCH="feat/$NAME"
        BASE_REF="origin/$MAIN"
        git rev-parse --verify -q "$BASE_REF" >/dev/null || BASE_REF="origin/HEAD"
        git checkout -b "$BRANCH" "$BASE_REF" 2>/dev/null || git checkout "$BRANCH" 2>/dev/null || { echo "Error: could not set branch $BRANCH."; exit 1; }
        prepare_runtime "$CLONE" new
        echo
        echo "Clone ready: $CLONE"
        echo "Branch: $BRANCH (from $BASE_REF)"
        ;;
    dep)
        PR="${2:-}"
        [ -n "$PR" ] || usage
        PR="${PR#\#}"
        require_gh
        parse_modules "${@:3}"
        create_clone "dependabot-$PR"
        gh pr checkout "$PR"
        prepare_runtime "$CLONE" dep
        echo
        echo "Clone ready: $CLONE (PR #$PR checked out)"
        ;;
    list)
        echo "Sibling clones under $PARENT:"
        list_clones
        ;;
    checkout)
        [ -n "${2:-}" ] || usage
        git checkout "$2"
        ;;
    test)
        shift
        if [ $# -eq 0 ] && [ -f "$ROOT/.git/dev-modules" ]; then
            mods=()
            while IFS= read -r m; do [ -n "$m" ] && mods+=("$m"); done < "$ROOT/.git/dev-modules"
            set -- "${mods[@]}"
        fi
        (cd "$ROOT" && bash scripts/test.sh "$@")
        ;;
    sandbox)
        shift
        (cd "$ROOT" && bash scripts/test-sandbox.sh "$@")
        ;;
    commit)
        [ -n "${2:-}" ] || { echo "Usage: ./scripts/dev.sh commit \"message\""; exit 1; }
        git add -A
        git commit -m "$2"
        ;;
    push)
        BR="$(curbranch)"
        case "$BR" in
            "$GATE"|"$MAIN") echo "Refusing to push $BR directly."; exit 1 ;;
        esac
        git push -u origin "$BR"
        ;;
    pr)
        shift
        require_gh
        BR="$(curbranch)"
        case "$BR" in
            "$GATE"|"$MAIN") echo "Refusing to open a PR from $BR."; exit 1 ;;
        esac
        BASE="$MAIN"
        TITLE=""
        while [ $# -gt 0 ]; do
            case "$1" in
                --base) BASE="${2:-}"; [ -n "$BASE" ] || usage; shift 2 ;;
                *) TITLE="$1"; shift ;;
            esac
        done
        [ -n "$TITLE" ] || TITLE="$(git log -1 --pretty=%s)"
        gh pr create --base "$BASE" --head "$BR" --title "$TITLE" --body "Automated PR from the dev workflow for branch \`$BR\` (base \`$BASE\`)."
        ;;
    merge|auto-merge)
        KEEP="${2:-}"
        require_gh
        BR="$(curbranch)"
        case "$BR" in
            "$GATE"|"$MAIN") echo "Cannot merge from $BR. Run inside a feature/dependabot clone."; exit 1 ;;
        esac
        PRNUM="$(gh pr list --head "$BR" --json number --jq '.[0].number' || true)"
        [ -n "$PRNUM" ] || { echo "Error: no open PR found for branch $BR."; exit 1; }

        echo "Waiting for PR #$PRNUM checks to appear..."
        CHECKS=0
        for _ in $(seq 1 30); do
            CHECKS="$(gh pr view "$PRNUM" --json statusCheckRollup --jq '.statusCheckRollup | length' 2>/dev/null || echo 0)"
            [ "${CHECKS:-0}" -gt 0 ] && break
            sleep 10
        done
        if [ "${CHECKS:-0}" -eq 0 ]; then
            echo "No checks reported for PR #$PRNUM. Clone kept for inspection."
            exit 1
        fi

        echo "Waiting for PR checks to be green..."
        if ! timeout 900 gh pr checks "$PRNUM" --watch; then
            echo "PR checks did not all pass within timeout. Clone kept for inspection."
            exit 1
        fi

        BAD_CHECKS="$(gh pr view "$PRNUM" --json statusCheckRollup --jq '[.statusCheckRollup[]? | select(.conclusion == "FAILURE" or .conclusion == "CANCELLED" or .conclusion == "TIMED_OUT" or .conclusion == "ACTION_REQUIRED" or .state == "ERROR") | .name] | join(", ")')"
        [ -z "$BAD_CHECKS" ] || { echo "PR has failing or cancelled checks: $BAD_CHECKS. Clone kept for inspection."; exit 1; }

        if ! gh pr view "$PRNUM" --json mergeable --jq '.mergeable' | grep -q 'MERGEABLE'; then
            echo "PR is not mergeable yet; attempting to auto-resolve conflicts..."
            PR_BASE="$(gh pr view "$PRNUM" --json baseRefName --jq '.baseRefName')"
            git fetch origin "$PR_BASE" >/dev/null 2>&1 || true
            if git rebase "origin/$PR_BASE"; then
                echo "Rebase succeeded."
                git push --force-with-lease origin "$BR" || { echo "Push after rebase failed. Clone kept."; exit 1; }
            else
                git rebase --abort >/dev/null 2>&1
                echo "Error: could not auto-resolve conflicts. Resolve manually, then re-run merge. Clone kept."
                exit 1
            fi
        fi

        echo "Merging PR #$PRNUM..."
        if gh pr merge "$PRNUM" --squash --delete-branch; then
            STATE=""
            for _ in $(seq 1 90); do
                STATE="$(gh pr view "$PRNUM" --json state --jq '.state')"
                [ "$STATE" = "MERGED" ] && break
                if [ "$STATE" = "CLOSED" ]; then
                    echo "PR closed without merging. Clone kept for inspection."
                    exit 1
                fi
                sleep 10
            done
            [ "$STATE" = "MERGED" ] || { echo "Timed out waiting for the merge. Clone kept for inspection."; exit 1; }
            echo "PR merged."
            HERE="$(pwd -P)"
            if [ "$KEEP" = "-k" ]; then
                echo "Keeping clone: $HERE"
            elif validate_clone "$HERE"; then
                delete_clone "$HERE"
            fi
        else
            echo "PR merge failed. Clone kept for inspection."
            exit 1
        fi
        ;;
    sync)
        cd "$ROOT"
        git fetch origin
        git checkout "$GATE"
        git pull --ff-only origin "$GATE"
        BEFORE="$(git rev-parse HEAD)"
        git merge --ff-only "origin/$MAIN" || { echo "Error: $GATE and $MAIN diverged. Resolve manually instead of creating a merge commit."; exit 1; }
        if [ "$(git rev-parse HEAD)" != "$BEFORE" ]; then
            git push origin "$GATE"
            echo "$GATE fast-forwarded to $MAIN and pushed."
        else
            echo "$GATE already contains $MAIN."
        fi
        ;;
    cleanup)
        NAME="${2:-}"
        [ -n "$NAME" ] || usage
        if TARGET="$(resolve_clone "$NAME")"; then
            delete_clone "$TARGET"
        else
            echo "Nothing to clean: '$NAME' does not resolve to an existing clone under $PARENT."
            echo "Discovered clones:"
            list_clones
            exit 1
        fi
        ;;
    status)
        echo "Branch: $(curbranch)"
        echo
        git status --short
        echo
        git rev-list --left-right --count "origin/$MAIN...HEAD" 2>/dev/null || true
        ;;
    *)
        usage
        ;;
esac
