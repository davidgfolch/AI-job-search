from tabulate import tabulate
from commonlib.terminalColor import yellow, red

def print_failed_info_table(persistence_manager):
    data = _collect_failed_info(persistence_manager)
    if not data:
        return
    print("\n" + yellow("=" * 100))
    print(yellow("FAILED INFORMATION SUMMARY"))
    print(yellow("=" * 100))
    table = tabulate(data, headers=["Scrapper", "Failed Keywords", "Last Error", "Error Time"], tablefmt="grid")
    print(table)
    print(yellow("=" * 100) + "\n")

def _collect_failed_info(persistence_manager):
    data = []
    for scrapper_name, scrapper_state in persistence_manager.state.items():
        failed_keywords = scrapper_state.get('failed_keywords', [])
        last_error = scrapper_state.get('last_error', '')
        error_time = scrapper_state.get('last_error_time', '')
        if failed_keywords or last_error:
            keywords_str = ', '.join(failed_keywords) if failed_keywords else '-'
            error_str = last_error if last_error else '-'
            time_str = error_time if error_time else '-'
            data.append([scrapper_name, keywords_str, error_str, time_str])
    return data
