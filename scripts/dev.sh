#!/usr/bin/env bash
# ===== AI Job Search parallel development workflow (Linux/Mac) =====
# Usage: ./scripts/dev.sh <command> [args]
#   new <name>              - clone ../ai_job_search-<name>, branch feat/<name> from the gate branch, copy env + lockfiles
#   dep <pr>                - clone ../ai_job_search-dependabot-<pr> and check out that PR (used by dependabot-agent)
#   list                    - show sibling clones
#   checkout <branch>       - switch branch in the current clone
#   test [modules]          - run scripts/test.sh here (no args = everything)
#   sandbox <service> [...] - run scripts/test-sandbox.sh here
#   commit "msg"            - git add -A && git commit
#   push                    - push the current branch (never staging/master)
#   pr [title] [--base br]  - open a PR (default base: the staging gate)
#   merge [-k]              - wait for green checks, squash-merge, delete branch and clone (keep clone with -k)
#   sync                    - fast-forward staging from master and push it (run before dependabot work)
#   cleanup <name|path>     - delete a sibling clone by name, prefixed name, or path
#   status                  - branch, dirty state, ahead/behind vs the gate branch

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT="$(cd "$ROOT/.." && pwd -P)"
PREFIX="ai_job_search-"
GATE="${DEV_GATE_BRANCH:-staging}"
MAIN="${DEV_MAIN_BRANCH:-master}"
CMD="${1:-}"

usage() {
    awk 'NR==1 {next} /^#/ {sub(/^# ?/, ""); print; next} {exit}' "${BASH_SOURCE[0]}"
    exit 1
}

curbranch() { git rev-parse --abbrev-ref HEAD; }

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
    local dest="$1" f mod
    for f in .env .env.secrets; do
        if [ -f "$ROOT/$f" ] && [ ! -f "$dest/$f" ]; then
            cp "$ROOT/$f" "$dest/$f"
            echo "Copied $f"
        fi
    done
    for f in "$ROOT"/apps/*/uv.lock "$ROOT"/apps/*/poetry.lock "$ROOT"/apps/*/package-lock.json; do
        [ -f "$f" ] || continue
        mod="$(basename "$(dirname "$f")")"
        mkdir -p "$dest/apps/$mod"
        if [ ! -f "$dest/apps/$mod/$(basename "$f")" ]; then
            cp "$f" "$dest/apps/$mod/"
            echo "Copied apps/$mod/$(basename "$f")"
        fi
    done
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

delete_clone() {
    local target="$1"
    stop_codegraph_daemon "$target/.codegraph/daemon.pid"
    cd "$target/.." || return 1
    echo "Deleting clone $target..."
    rm -rf "$target" 2>/dev/null || true
    if [ -e "$target" ]; then
        echo "Error: could not delete $target (is a terminal or CodeGraph daemon holding it?)."
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
        create_clone "$NAME"
        git fetch origin >/dev/null 2>&1 || true
        BRANCH="feat/$NAME"
        BASE_REF="origin/$GATE"
        git rev-parse --verify -q "$BASE_REF" >/dev/null || BASE_REF="origin/$MAIN"
        git checkout -b "$BRANCH" "$BASE_REF" 2>/dev/null || git checkout "$BRANCH" 2>/dev/null || { echo "Error: could not set branch $BRANCH."; exit 1; }
        echo
        echo "Clone ready: $CLONE"
        echo "Branch: $BRANCH (from $BASE_REF)"
        ;;
    dep)
        PR="${2:-}"
        [ -n "$PR" ] || usage
        PR="${PR#\#}"
        require_gh
        create_clone "dependabot-$PR"
        gh pr checkout "$PR"
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
        BASE="$GATE"
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
            git fetch origin "$GATE" >/dev/null 2>&1 || true
            if git rebase "origin/$GATE"; then
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
        git rev-list --left-right --count "origin/$GATE...HEAD" 2>/dev/null || true
        ;;
    *)
        usage
        ;;
esac
