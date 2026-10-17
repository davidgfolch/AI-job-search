#!/bin/bash
set -e
# Remove the dependencies and generated artifacts installed by install.*.
# Interactive menu; several items can be selected at once.
# No git command is used, and protected paths are never touched.

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APPS_DIR="$PROJECT_ROOT/apps"

remove_path() {
    local path="$1"
    if [ -e "$path" ] || [ -L "$path" ]; then
        echo "Removing $path"
        rm -rf "$path"
    fi
}

list_apps() {
    local dir name
    for dir in "$APPS_DIR"/*/; do
        [ -d "$dir" ] || continue
        name="${dir%/}"
        name="${name##*/}"
        echo "$name"
    done
}

remove_app() {
    local app="$1"
    local dir="$APPS_DIR/$app"
    if [ ! -d "$dir" ]; then
        echo "Skipping $app (not found)"
        return 0
    fi
    echo "Removing dependencies of $app..."
    remove_path "$dir/.venv"
    remove_path "$dir/.pytest_cache"
    remove_path "$dir/.coverage"
    remove_path "$dir/htmlcov"
    remove_path "$dir/coverage.xml"
    remove_path "$dir/coverage.txt"
    remove_path "$dir/node_modules"
    remove_path "$dir/test-results"
    remove_path "$dir/playwright-report"
    remove_path "$dir/uv.lock"
    remove_path "$dir/poetry.lock"
    find "$dir" -type d -name "__pycache__" -prune -exec rm -rf {} +
}

remove_root() {
    echo "Removing dependencies of the root project..."
    remove_path "$PROJECT_ROOT/.venv"
    remove_path "$PROJECT_ROOT/.pytest_cache"
    remove_path "$PROJECT_ROOT/.coverage"
}

remove_global_tool() {
    local tool="$1"
    if command -v uv > /dev/null 2>&1; then
        uv tool uninstall "$tool"
    fi
}

app_artifacts_present() {
    local app="$1"
    local dir="$APPS_DIR/$app"
    if [ ! -d "$dir" ]; then return 1; fi
    if [ -d "$dir/.venv" ]; then return 0; fi
    if [ -d "$dir/.pytest_cache" ]; then return 0; fi
    if [ -d "$dir/node_modules" ]; then return 0; fi
    if [ -d "$dir/htmlcov" ]; then return 0; fi
    if [ -d "$dir/test-results" ]; then return 0; fi
    if [ -d "$dir/playwright-report" ]; then return 0; fi
    if [ -f "$dir/.coverage" ]; then return 0; fi
    if [ -f "$dir/coverage.xml" ]; then return 0; fi
    if [ -f "$dir/coverage.txt" ]; then return 0; fi
    if [ -f "$dir/uv.lock" ]; then return 0; fi
    if [ -f "$dir/poetry.lock" ]; then return 0; fi
    if [ -n "$(find "$dir" -type d -name '__pycache__' -print -quit 2>/dev/null)" ]; then
        return 0
    fi
    return 1
}

root_artifacts_present() {
    if [ -d "$PROJECT_ROOT/.venv" ]; then return 0; fi
    if [ -d "$PROJECT_ROOT/.pytest_cache" ]; then return 0; fi
    if [ -f "$PROJECT_ROOT/.coverage" ]; then return 0; fi
    if [ -f "$PROJECT_ROOT/uv.lock" ]; then return 0; fi
    if [ -f "$PROJECT_ROOT/poetry.lock" ]; then return 0; fi
    if [ -n "$(find "$PROJECT_ROOT" -maxdepth 3 -type d -name '__pycache__' -print -quit 2>/dev/null)" ]; then
        return 0
    fi
    return 1
}

global_tool_installed() {
    local tool="$1"
    if command -v uv > /dev/null 2>&1; then
        if uv tool list 2>/dev/null | grep -qi "$tool"; then
            return 0
        fi
    fi
    return 1
}

CHOSEN=""
select_items() {
    local items=("$@")
    local count=${#items[@]}
    local choice rest token index invalid
    local selected=""
    local i item
    echo ""
    echo "Uninstallable items:"
    for ((i = 0; i < count; i++)); do
        echo "  $((i + 1))) ${items[i]}"
    done
    while :; do
        read -r -p "Select one or more [e.g. 1,3 5] (Enter to cancel): " choice
        if [ -z "$choice" ]; then
            return 0
        fi
        selected=""
        rest="${choice//,/ }"
        rest="$rest "
        invalid=0
        while [ -n "$rest" ]; do
            token="${rest%% *}"
            rest="${rest#* }"
            case "$token" in
                ''|*[!0-9]*)
                    invalid=1
                    ;;
                *)
                    index=$((10#$token))
                    if [ "$index" -lt 1 ] || [ "$index" -gt "$count" ]; then
                        invalid=1
                    else
                        item="${items[$((index - 1))]}"
                        selected="$selected $item"
                    fi
                    ;;
            esac
        done
        if [ "$invalid" -eq 0 ] && [ -n "$selected" ]; then
            CHOSEN="${selected# }"
            return 0
        fi
        echo "Invalid selection, try again."
    done
}

main() {
    local items=()
    local app
    while IFS= read -r app; do
        if app_artifacts_present "$app"; then
            items+=("$app")
        fi
    done < <(list_apps)
    if root_artifacts_present; then
        items+=("root")
    fi
    if global_tool_installed "graphify"; then
        items+=("graphify")
    fi
    if global_tool_installed "crawlee"; then
        items+=("crawlee")
    fi
    if [ "${#items[@]}" -eq 0 ]; then
        echo "Nothing to uninstall (no dependencies found)."
        exit 0
    fi
    select_items "${items[@]}"
    if [ -z "$CHOSEN" ]; then
        echo "Nothing selected, nothing removed."
        exit 0
    fi
    for item in $CHOSEN; do
        echo "Removing dependencies of $item..."
        case "$item" in
            root) remove_root ;;
            graphify|crawlee) remove_global_tool "$item" ;;
            *) remove_app "$item" ;;
        esac
    done
    echo "Done."
}

main
