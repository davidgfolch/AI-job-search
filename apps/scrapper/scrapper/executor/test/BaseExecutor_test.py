import pytest
from unittest.mock import patch, MagicMock
from scrapper.core.scrapper_config import SCRAPPERS, TIMER
from scrapper.executor.BaseExecutor import BaseExecutor
from scrapper.executor import BaseExecutor as base_module

@pytest.fixture
def mocks():
    sel = MagicMock()
    pm = MagicMock()
    return {'sel': sel, 'pm': pm}

@pytest.fixture
def run_mocks():
    names = ['Infojobs', 'Linkedin', 'Glassdoor', 'Tecnoempleo', 'Indeed']
    # Patch the actual executor modules, not inside BaseExecutor
    patchers = {name: patch(f'scrapper.executor.{name}Executor.{name}Executor') for name in names}
    yield {name: p.start() for name, p in patchers.items()}
    for p in patchers.values(): p.stop()

class MockBaseExecutor(BaseExecutor):
    def _create_service(self, mysql):
        return MagicMock()
    def _process_keyword(self, keyword, start_page):
        pass

class TestExecutor:
    def test_execute_preload(self, mocks):
        # Use concrete class for testing base methods
        executor = MockBaseExecutor(mocks['sel'], mocks['pm'], False)
        executor.site_name = "TestSite"
        props = {}
        
        with patch.object(executor, 'run') as mock_run:
            executor.execute_preload(props)
            mock_run.assert_called_with(preload_page=True)
            assert props['preloaded'] is True

    def test_execute(self, mocks):
        executor = MockBaseExecutor(mocks['sel'], mocks['pm'], False)
        executor.site_name = "TestSite"
        props = {}
        
        with patch.object(executor, 'run') as mock_run:
            executor.execute(props)
            mock_run.assert_called_with(preload_page=False)
            mocks['pm'].update_last_execution.assert_called()
            mocks['pm'].update_last_ran_at.assert_called_with(executor.site_name_key)

    def test_execute_exception(self, mocks):
        executor = MockBaseExecutor(mocks['sel'], mocks['pm'], False)
        executor.site_name = "TestSite"
        props = {}
        
        # Simulate exception in run
        with patch.object(executor, 'run', side_effect=Exception("Scrapper failed")):
            executor.execute(props)
        
        # Verify set_error is called
        mocks['pm'].set_error.assert_called_with(executor.site_name_key, "Scrapper failed")
        # Verify last_execution updated to None
        mocks['pm'].update_last_execution.assert_called_with(executor.site_name_key, None)
        # Verify last_ran_at is always updated
        mocks['pm'].update_last_ran_at.assert_called_with(executor.site_name_key)

    def test_preload_failure_sets_error_in_persistence(self, mocks):
        # Setup - patch the executor to test execute_preload directly
        name = "infojobs"
        properties = {"preloaded": False}
        
        # We need to simulate the class/instance structure expected by execute_preload
        # BaseExecutor.execute_preload calls self.run(preload_page=True)
        # We can reuse MockBaseExecutor
        
        executor = MockBaseExecutor(mocks['sel'], mocks['pm'], False)
        executor.site_name = "INFOJOBS"

        
        with patch.object(executor, 'run', side_effect=Exception("Preload Error")):
            # Call bound method
            result = executor.execute_preload(properties)
            
            # Verify
            assert result is True
            assert properties["preloaded"] is False
            mocks['pm'].set_error.assert_called_once()
            args = mocks['pm'].set_error.call_args[0]
            assert args[0] == "Infojobs"
            assert "Preload Error" in args[1]


def service_mock(*attributes):
    return MagicMock(spec=['prepare_resume', *attributes])


class TestKeywordLoop:
    def test_skips_blank_keywords(self, persistence, process_keyword, stub_executor):
        executor = stub_executor(persistence, service_mock())
        executor.jobs_search = 'python,,  ,java'
        executor._execute_scrapping()
        assert [call.args for call in process_keyword.call_args_list] == [('python', 1), ('java', 1)]

    def test_delegates_the_skip_decision_to_the_service(self, persistence, process_keyword, stub_executor):
        service = service_mock('should_skip_keyword')
        service.should_skip_keyword.return_value = (True, 4)
        executor = stub_executor(persistence, service)
        executor._execute_scrapping()
        process_keyword.assert_not_called()
        service.should_skip_keyword.assert_any_call('python')

    def test_processes_a_keyword_the_service_does_not_skip(self, persistence, process_keyword, stub_executor):
        service = service_mock('should_skip_keyword')
        service.should_skip_keyword.return_value = (False, 3)
        executor = stub_executor(persistence, service)
        executor._execute_scrapping()
        assert process_keyword.call_args_list[0].args == ('python', 3)

    def test_resumes_from_the_saved_page_when_the_service_has_no_skip_hook(self, persistence, process_keyword, stub_executor):
        persistence.get_state.return_value = {'keyword': 'java', 'page': 5}
        executor = stub_executor(persistence, service_mock())
        executor._execute_scrapping()
        assert process_keyword.call_args_list[-1].args == ('java', 5)

    def test_starts_at_page_one_for_a_keyword_before_the_saved_one(self, persistence, process_keyword, stub_executor):
        persistence.get_state.return_value = {'keyword': 'java', 'page': 5}
        executor = stub_executor(persistence, service_mock())
        executor._execute_scrapping()
        assert process_keyword.call_args_list[0].args == ('python', 1)

    def test_marks_a_keyword_as_failed_when_processing_raises(self, persistence, stub_executor):
        service = service_mock('should_skip_keyword')
        service.should_skip_keyword.return_value = (False, 1)
        executor = stub_executor(persistence, service)
        with patch.object(stub_executor, '_process_keyword', side_effect=RuntimeError('boom')):
            executor._execute_scrapping()
        persistence.add_failed_keyword.assert_any_call('Stub', 'python')
        persistence.set_error.assert_called()
        persistence.remove_failed_keyword.assert_not_called()

    def test_prepares_the_resume_state_and_finalizes(self, persistence, process_keyword, stub_executor):
        service = service_mock('should_skip_keyword')
        service.should_skip_keyword.return_value = (False, 1)
        executor = stub_executor(persistence, service)
        executor._execute_scrapping()
        service.prepare_resume.assert_called_once()
        persistence.finalize_scrapper.assert_called_once_with('Stub')


class TestPreloadRun:
    def test_preload_only_runs_the_preload_action(self, persistence, process_keyword, stub_executor):
        executor = stub_executor(persistence, service_mock())
        with patch.object(base_module, 'printScrapperTitle'):
            executor.run(preload_page=True)
        process_keyword.assert_not_called()

    def test_preload_action_is_a_no_op_by_default(self, persistence, stub_executor):
        assert BaseExecutor._preload_action(stub_executor(persistence, service_mock())) is None


class TestKeyboardInterrupt:
    @pytest.mark.parametrize("method, props", [('execute', {}), ('execute_preload', {'preloaded': False})], ids=["execute", "preload"])
    def test_double_interrupt_aborts_the_run(self, persistence, method, props, stub_executor):
        executor = stub_executor(persistence, service_mock())
        with patch.object(executor, 'run', side_effect=KeyboardInterrupt), \
             patch.object(base_module, 'abortExecution', return_value=True):
            assert getattr(executor, method)(props) is False
        persistence.update_last_execution.assert_called_once_with('Stub', None)

    @pytest.mark.parametrize("method, props", [('execute', {}), ('execute_preload', {'preloaded': False})], ids=["execute", "preload"])
    def test_a_single_interrupt_keeps_going(self, persistence, method, props, stub_executor):
        executor = stub_executor(persistence, service_mock())
        with patch.object(executor, 'run', side_effect=KeyboardInterrupt), \
             patch.object(base_module, 'abortExecution', return_value=False):
            assert getattr(executor, method)(props) is True
