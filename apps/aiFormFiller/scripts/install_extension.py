"""Install or uninstall the AI Form Filler extension in existing Chrome/Firefox installs."""
import argparse
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from commonlib.observability import CONSOLE_MESSAGE, configure_logging, get_logger
import browser_policies as policies
import extension_packages as packages

configure_logging("aiFormFiller", console=CONSOLE_MESSAGE)
logger = get_logger("aiFormFiller.install_extension")


def report(message, level="info"):
    getattr(logger, level)("extension.install_report", console=message)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Install the AI Form Filler browser extension persistently")
    parser.add_argument("--browser", choices=("chrome", "firefox", "all"), default="all")
    parser.add_argument("--uninstall", action="store_true", help="Remove the registration and generated packages")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written without changing anything")
    return parser.parse_args(argv)


def selected_browsers(choice):
    if choice != "all":
        return [choice]
    candidates = (("chrome", ("chrome", "google-chrome", "chromium", "chrome.exe")), ("firefox", ("firefox", "firefox.exe")))
    return [name for name, executables in candidates if policies.browser_installed(executables)]


def install_browser(browser, dry_run):
    if dry_run:
        report(f"[dry-run] Would build and register the {browser} package")
        return
    if browser == "chrome":
        identifier, crx = packages.pack_chrome()
        if platform.system() == "Linux":
            path = policies.chrome_external_install(identifier, crx)
            method = "external extensions"
        else:
            update_url = (packages.artifact_dir() / "update.xml").resolve().as_uri()
            path = policies.chrome_policy_install(identifier, update_url)
            method = "enterprise policy"
        packages.save_state(identifier)
        report(f"Chrome extension {identifier} registered via {method}: {path}")
    else:
        _, xpi = packages.pack_firefox()
        path = policies.firefox_install(xpi)
        report(f"Firefox extension {packages.FIREFOX_ID} registered via policies.json: {path}")


def uninstall_browser(browser, dry_run):
    if dry_run:
        report(f"[dry-run] Would unregister the {browser} package")
        return
    if browser == "chrome":
        identifier = packages.stored_chrome_id()
        if not identifier:
            report("No Chrome extension registration found", "warning")
            return
        removed = policies.chrome_external_uninstall(identifier) + policies.chrome_policy_uninstall(identifier)
        report(f"Chrome registration removed: {removed or 'nothing to remove'}")
    else:
        removed = policies.firefox_uninstall()
        report(f"Firefox registration removed: {removed or 'nothing to remove'}")


def main(argv=None):
    args = parse_args(argv)
    browsers = selected_browsers(args.browser)
    if not browsers:
        report("No supported browser is installed", "warning")
        return 1
    for browser in browsers:
        if args.uninstall:
            uninstall_browser(browser, args.dry_run)
        else:
            install_browser(browser, args.dry_run)
    if not args.dry_run and args.uninstall:
        packages.clean_artifacts()
    if not args.dry_run:
        report("Restart the browser to apply the change. Use --uninstall to remove it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
