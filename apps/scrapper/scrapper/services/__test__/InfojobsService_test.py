import pytest
from unittest.mock import MagicMock
from scrapper.services.InfojobsService import InfojobsService, REMOVE_IN_MARKDOWN
from commonlib.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager
class TestInfojobsCleaning:

    @pytest.fixture
    def service(self):
        mock_mysql = MagicMock(spec=MysqlUtil)
        mock_persistence_manager = MagicMock(spec=PersistenceManager)
        return InfojobsService(mock_mysql, mock_persistence_manager)

    @pytest.mark.parametrize("input_md, required_substrings", [
        (
            """
# Job Title

Description of the job.


¿Te gusta esta oferta?
Prueba el Asistente de IA y mejora tus posibilidades.

Asistente IA


Requirements...
""",
            ["Description of the job.", "Requirements..."]
        ),
        (
            """
# Job Title
Content

¿Te gusta esta oferta?   
  
Prueba el Asistente de IA y mejora tus posibilidades.
  
Asistente IA

More Content
""",
            ["Content", "More Content"]
        )
    ])
    def test_post_process_markdown(self, service, input_md, required_substrings):
        cleaned_md = service.post_process_markdown(input_md)
        for remove in REMOVE_IN_MARKDOWN:
            assert remove not in cleaned_md
        for required in required_substrings:
            assert required in cleaned_md
