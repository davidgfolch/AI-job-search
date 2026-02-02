from commonlib.terminalColor import cyan
from ..core.scrapper_config import SCRAPPERS, get_debug
from ..util.persistence_manager import PersistenceManager
from ..services.selenium.seleniumService import SeleniumService

def create_executor(name: str, selenium_service: SeleniumService, persistence_manager: PersistenceManager):
    """Factory method to create executor instances by name."""
    from ..executor.InfojobsExecutor import InfojobsExecutor
    from ..executor.TecnoempleoExecutor import TecnoempleoExecutor
    from ..executor.LinkedinExecutor import LinkedinExecutor
    from ..executor.GlassdoorExecutor import GlassdoorExecutor
    from ..executor.IndeedExecutor import IndeedExecutor
    debug_val = get_debug(name)
    match name.lower():
        case 'infojobs':
            return InfojobsExecutor(selenium_service, persistence_manager, debug_val)
        case 'tecnoempleo':
            return TecnoempleoExecutor(selenium_service, persistence_manager, debug_val)
        case 'linkedin':
            return LinkedinExecutor(selenium_service, persistence_manager, debug_val)
        case 'glassdoor':
            return GlassdoorExecutor(selenium_service, persistence_manager, debug_val)
        case 'indeed':
            return IndeedExecutor(selenium_service, persistence_manager, debug_val)
    raise ValueError(f"Unknown scrapper: {name}")

def process_page_url(url: str):
    """Process a specific URL (only LinkedIn is currently supported)."""
    for name, _ in SCRAPPERS.items():
        if url.find(name.lower()) != -1:
            print(cyan(f'Running scrapper for pageUrl: {url}'))
            from ..executor.LinkedinExecutor import LinkedinExecutor
            match name.lower():
                case 'linkedin':
                    LinkedinExecutor.process_specific_url(url)
                case _:
                    raise Exception(f"Invalid scrapper web page name {name}, only linkedin is implemented")
            return
