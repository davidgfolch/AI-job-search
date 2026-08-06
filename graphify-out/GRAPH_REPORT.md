# Graph Report - AI-job-search  (2026-08-06)

## Corpus Check
- 828 files · ~337,473 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5664 nodes · 10197 edges · 684 communities (336 shown, 348 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 356 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b345626c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- retry
- cron::commonlib_company_normalizer
- commonlib::ctypes
- terminalColor.py
- jobs.py
- scrapper::c_users_trendingpc_projects_ai_job_search_apps_scrapper_scrapper_core_py
- seleniumSocketConnRetry
- scrapper::commonlib_filesystemutil
- commonlib::pymongo
- StatisticsApi.ts
- backend::pydantic
- backend::time
- PersistenceManager
- commonlib::commonlib_sql
- IndeedScraplingNavigator
- Settings.tsx
- aiCvMatcher::commonlib_aienrichrepository
- backend::commonlib_environmentutil
- yellow
- patch
- MysqlUtil
- TestBaseNavigator
- configurations/hooks/useFilterConfigurations.ts
- commonlib::c_users_trendingpc_projects_ai_job_search_apps_commonlib_commonlib_decorator_py
- scrapper::commonlib_dateutil
- commonlib::concurrent_futures
- WakeableTimer
- Viewer.tsx
- scrapper::commonlib_findlastduplicated
- aiEnrichSkill/test/config_test.py
- aiFormFiller::dataclasses
- ai_helpers.py
- backend::commonlib_sql_mysqlutil
- persistence_manager_test.py
- test-utils.tsx
- web::c_users_trendingpc_projects_ai_job_search_apps_web_src_pages_viewer_api_salary
- GmailService
- backend::json
- backend::commonlib_company_matcher
- backend::commonlib_test_db_mock_util
- aiFormFiller::commonlib_terminalcolor
- web::src_resources_defaultfilterconfigurations
- ViewerApi.ts
- useViewer.ts
- web::src_pages_viewer_components_configurations_hooks_usefilterwatcher_last_watcher_check_time_key
- scrapper::email
- jobsApi
- environmentUtil.py
- backend::api
- extract_boolean_filters
- aiEnrichNew::commonlib_aienrichrepository
- TecnoempleoExecutor
- aiEnrich3::aienrich3_services_job_enrichment_service
- SeleniumService
- backend::pytest
- Adaptive scraping
- sqlUtil.py
- aiEnrich/dataExtractor.py
- JobRepository
- backend::commonlib_exceptionutil
- commonlib::tempfile
- GlassdoorExecutor
- aiEnrich3::aienrich3_services_extractors_modality_extractor
- aiFormFiller::pydantic
- commonlib::json
- scrapper::concurrent_futures
- SalaryCalculator.tsx
- MetricsCollector
- dateUtil.py
- web::src_pages_viewer_components_configurations_hooks_usefilterwatcher_watcherresult
- aiEnrichNew::commonlib_ai_helpers
- ScrapperStateRepository
- IndeedService
- web::c_users_trendingpc_projects_ai_job_search_apps_web_src_pages_skillsmanager_skillsmanager_handleexport
- build_jobs_where_clause
- Most Important Improvements for this Monorepo
- ContextLoader
- aiEnrichSkill::commonlib_dateutil
- AnswerResult
- TransactionManager
- IndeedNavigator
- useSqlEditor.ts
- Viewer.interactions.test.tsx
- compilerOptions
- aiEnrichNew/services/job_enrichment_service.py
- aiEnrichNew::unittest
- filter_configurations_service_test.py
- backend::commonlib_jobsnapshotrepository
- TestLinkedinNavigator
- commonlib::os
- aiEnrich3/services/test/job_enrichment_service_test.py
- query_ollama
- scrapper::random
- skills.py
- filter_configurations_repository_test.py
- CompanySynonymService
- QueryExecutor
- aiEnrich3/dataExtractor.py
- aiEnrich3::aienrich3_domain_entities
- aiEnrich::commonlib_ai_helpers
- aiFormFiller::c_users_trendingpc_projects_ai_job_search_apps_aiformfiller_src_aiformfiller_test_config_test_py
- aiFormFiller::unittest_mock
- viewer.helpers.ts
- persistence_manager.py
- commonlib::pathlib
- TestTecnoempleoNavigator
- devDependencies
- What You Must Do When Invoked
- SalaryHistoryRepository
- CronStateRepository
- aiEnrich3::unittest_mock
- aiEnrich::os
- backend::commonlib_company_normalizer
- GmailConnectionError
- commonlib::dotenv
- aiEnrich3/pipeline.py
- statistics_archived.py
- job_delete_service_test.py
- TestTransactionManager
- aiEnrichNew::os
- InfojobsExecutor
- compilerOptions
- Plan 0: Observability (Foundation for All Improvements)
- enrichment_service_test.py
- routes.py
- FilterConfigurationsService
- aiEnrichSkill::os
- TestJobQueries
- IndeedScraplingExecutor
- IndeedAuthenticator
- aiFormFiller::os
- commonlib::mathparse
- Modal.tsx
- web::c_users_trendingpc_projects_ai_job_search_apps_web_src_pages_viewer_api_jobs
- manifest.json
- BaseExecutor
- aiEnrichSkill::commonlib_environmentutil
- jobs_test.py
- CompanySynonymRepository
- JobSnapshotService
- commonlib::commonlib
- TestGetConnection
- architecture_test.py
- .layout_check.cjs
- web::src_index
- statistics_service_test.py
- aiEnrich::pytest
- AiEnrichRepository
- TestInfojobsNavigator
- testSetup.ts
- Screenshots
- commonlib::os_path
- AGENTS.md
- SkillsService
- WatcherService
- commonlib::collections
- JobsRepository
- StatisticsArchivedService
- TestQueryExecutor
- scheduler_test.py
- EditSkillModal.tsx
- .opencode/AGENTS.md
- getEnv
- company_synonyms.py
- create_mock_db
- CombinedStatsRepository
- aiEnrich::commonlib_environmentutil
- JobSnapshotRepository
- exceptionUtil_test.py
- connection_manager.py
- EmailReader
- TestEmailReader
- AI Job Search — Metrics & Observability
- KeepSystemAwake
- Advanced usages
- observability.py
- AI Job Search API
- web::c_users_trendingpc_projects_ai_job_search_apps_web_src_pages_skillsmanager_components_uselearnlist
- SkillsRepository
- CVLoader
- aiEnrichSkill::unittest_mock
- stringUtil.py
- Job Scrappers
- TestLinkedinService
- dependencies
- Plan B: RAG Cache Layer (Skip LLM Inference for Similar Jobs)
- panel.js
- commonlib::ast
- AI Form Filler
- TestQuestionAnsweringService
- JobDeleteRepository
- LinkedinExecutor
- TestIndeedService
- Plan A: Direct Ollama API (Remove CrewAI)
- Plan C: Two-Stage Pipeline (aiEnrich3 Fast Path + aiEnrich LLM Fallback)
- Plan E: Prompt & Token Optimization (Quick Wins)
- Requests & Responses
- cvMatcher_test.py
- LinkedinNavigator
- process_batch
- SnapshotsRepository
- StatisticsRepository
- MongoDbProvider
- CompanySalaryHistoryScanner
- e2e/package.json
- ScrapperStateCalculator
- scrapper_scheduler_test.py
- IndeedGmailService
- TestBaseService
- FilterConfigurationsTestUtils.tsx
- Plan F: Combined / Recommended Approach
- Setup Guide
- README.md
- ModalityExtractor
- process_batch
- SalaryHistoryService
- TestScraplingService
- jobs_applied_test.py
- _detect_captcha
- JobWriteRepository
- generate_config_view_sql
- AI Job Search Web UI
- @testing-library/user-event
- Plan D: GGUF Quantized Models via llama-cpp-python
- aiEnrichSkill
- api/salary.py
- company_synonym_service_test.py
- observability_test.py
- JobsService
- terminalUtil.py
- web/package.json
- SkillsManager.tsx
- Tools
- query_ollama
- FilterConfigurationsRepository
- MockBaseExecutor
- print_failed_info_table
- Version Bumper Instructions
- TODO
- run_e2e_tests.py
- Components
- SkillsManagerApi.ts
- TestApiRoutes
- TestContextLoader
- api/main.py
- getSrcPath
- Company Salary History Scanner
- TestInfojobsService
- backendDiscovery.ts
- SkillsTable.tsx
- graphify-inject-edges.py
- commonlib
- Statistics.tsx
- generate_html
- Fetching dynamic websites
- Examples
- Proxy management and handling Blocks
- AI Job Enrichment
- backend/repositories/__init__.py
- App.tsx
- extract_filter_params
- validationUtils.ts
- SettingsApi.ts
- get_pipeline
- OpenRouterProvider
- normalize_company_name
- systemUtil.py
- Common Library
- Cron — Background Scheduler
- GlassdoorGmailService
- driverUtil.py
- JobListParams
- SkillsManager.test.tsx
- opencode.json
- graphify reference: extra exports and benchmark
- Quick Start Commands for Docker Development
- HTTP requests
- Examples
- StealthyFetcher
- ExtractionPipeline
- parse_job_enrichment_result
- run
- LocalHFProvider
- filter_configurations_test.py
- skills_test.py
- BaseNavigator
- E2E Implementer Instructions
- HTTP Methods
- Getting started
- Test Implementer Instructions
- aiEnrichNew
- statistics.py
- api/test/settings_test.py
- statistics_test.py
- TestScrapperConfig
- react
- E2E Implementer Instructions
- Test Implementer Instructions
- E2E Implementer Instructions
- Test Implementer Instructions
- QuotesSpider
- Scrapling Examples
- Fetchers basics
- TestOpenAIProvider
- ScraplingService
- AI Enrichment — Speed Improvement Plans
- graphify reference: query, path, explain
- AI Job Search Default Development Guide
- Examples
- enrichment_service.py
- content.js
- BaseService
- .connect
- TestGlassdoorNavigator
- SkillsList.test.tsx
- filter_deps
- generate_labels
- mock_sleep
- PageHeader.tsx
- queryTestUtils.tsx
- .opencode/opencode.json
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- Contribute
- graphify.sh
- Migrating from BeautifulSoup to Scrapling
- Scrapling Implementer Instructions
- View Backend Logs Instructions
- SalaryCalculator.test.tsx
- tsconfig.json
- View Backend Logs Instructions
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- nvidia-linux-restart.sh
- test.sh
- .agent/rules/architecture-guidelines.md
- 01_fetcher_session.py
- 02_dynamic_session.py
- 03_stealthy_session.py
- .agent/skills/skill-builder/SKILL.md
- aiEnrich/run.sh
- aiEnrichNew/run.sh
- aiEnrichSkill/run.sh
- aiFormFiller/run.sh
- backend/run.sh
- cron/run.sh
- scrapper/run.sh
- TestGlassdoorAuthenticator
- DriverUtil
- build_prometheus_metrics
- jsdom
- CompanySynonymsManager.tsx
- vite
- @vitejs/plugin-react
- web/run.sh
- setup.ts
- .claude/rules/architecture-guidelines.md
- .claude/skills/skill-builder/SKILL.md
- .opencode/rules/architecture-guidelines.md
- extraction-spec.md
- .opencode/skills/skill-builder/SKILL.md
- install.sh
- backup.sh
- restore.sh
- runMysql.sh
- aiCvMatcher::commonlib_cv_loader
- aiCvMatcher::commonlib_dateutil
- aiCvMatcher::commonlib_environmentutil
- aiCvMatcher::commonlib_sql_mysqlutil
- aiCvMatcher::commonlib_sqlutil
- aiCvMatcher::commonlib_stopwatch
- aiCvMatcher::commonlib_stringutil
- aiCvMatcher::commonlib_terminalcolor
- aiCvMatcher::commonlib_terminalutil
- aiCvMatcher::importlib_metadata
- aiCvMatcher::json
- aiCvMatcher::numpy
- aiCvMatcher::pytest
- aiCvMatcher::sentence_transformers
- aiCvMatcher::sklearn_metrics_pairwise
- aiCvMatcher::sys
- aiCvMatcher::time
- aiCvMatcher::traceback
- aiCvMatcher::unittest_mock
- aiCvMatcher::warnings
- aiEnrich3::aienrich3_services_extractors_salary_extractor
- aiEnrich3::aienrich3_services_extractors_skills_extractor
- aiEnrich3::commonlib_ai_helpers
- aiEnrich3::commonlib_aienrichrepository
- aiEnrich3::commonlib_observability
- aiEnrich3::commonlib_services_metrics_collector
- aiEnrich3::commonlib_sql_mysqlutil
- aiEnrich3::commonlib_stopwatch
- aiEnrich3::commonlib_terminalcolor
- aiEnrich3::dataclasses
- aiEnrich3::gc
- aiEnrich3::gliner
- aiEnrich3::importlib_metadata
- aiEnrich3::io
- aiEnrich3::json
- aiEnrich3::os
- aiEnrich3::pytest
- aiEnrich3::sys
- aiEnrich3::time
- aiEnrich3::torch
- aiEnrich3::traceback
- aiEnrich3::transformers
- aiEnrich3::typing
- aiEnrich3::warnings
- aiEnrich::commonlib_aienrichrepository
- aiEnrich::commonlib_json_helpers
- aiEnrich::commonlib_observability
- aiEnrich::commonlib_services_metrics_collector
- aiEnrich::commonlib_sql_mysqlutil
- aiEnrich::commonlib_stopwatch
- aiEnrich::commonlib_terminalcolor
- aiEnrich::commonlib_terminalutil
- aiEnrich::importlib_metadata
- aiEnrich::json
- aiEnrich::requests
- aiEnrich::time
- aiEnrich::traceback
- aiEnrich::unittest_mock
- aiEnrich::warnings
- aiEnrichNew::commonlib_environmentutil
- aiEnrichNew::commonlib_observability
- aiEnrichNew::commonlib_services_metrics_collector
- aiEnrichNew::commonlib_sql_mysqlutil
- aiEnrichNew::commonlib_stopwatch
- aiEnrichNew::commonlib_terminalcolor
- aiEnrichNew::commonlib_terminalutil
- aiEnrichNew::importlib_metadata
- aiEnrichNew::json
- aiEnrichNew::pytest
- aiEnrichNew::sys
- aiEnrichNew::time
- aiEnrichNew::torch
- aiEnrichNew::traceback
- aiEnrichNew::transformers
- aiEnrichNew::typing
- aiEnrichNew::unittest_mock
- aiEnrichNew::warnings
- aiEnrichSkill::commonlib_observability
- aiEnrichSkill::commonlib_services_metrics_collector
- aiEnrichSkill::commonlib_skill_context
- aiEnrichSkill::commonlib_skill_enricher_service
- aiEnrichSkill::commonlib_sql_mysqlutil
- aiEnrichSkill::commonlib_stopwatch
- aiEnrichSkill::commonlib_terminalcolor
- aiEnrichSkill::commonlib_terminalutil
- aiEnrichSkill::importlib_metadata
- aiEnrichSkill::json
- aiEnrichSkill::pytest
- aiEnrichSkill::requests
- aiEnrichSkill::sys
- aiEnrichSkill::time
- aiEnrichSkill::torch
- aiEnrichSkill::traceback
- aiEnrichSkill::transformers
- aiEnrichSkill::typing
- aiEnrichSkill::warnings
- aiFormFiller::commonlib_environmentutil
- aiFormFiller::fastapi_middleware_cors
- aiFormFiller::fastapi_testclient
- aiFormFiller::importlib_metadata
- aiFormFiller::openai
- aiFormFiller::pathlib
- aiFormFiller::pytest
- aiFormFiller::tempfile
- aiFormFiller::time
- aiFormFiller::torch
- aiFormFiller::transformers
- aiFormFiller::typing
- aiFormFiller::unittest
- backend::commonlib_mongodb_provider
- backend::commonlib_prometheus_exporter
- backend::commonlib_repositories_salary_history_repository
- backend::commonlib_salary
- backend::commonlib_services_metrics_collector
- backend::commonlib_sql_scrapper_state_repository
- backend::commonlib_sqlutil
- backend::commonlib_terminalcolor
- backend::decimal
- backend::fastapi
- backend::fastapi_middleware_cors
- backend::fastapi_testclient
- backend::importlib_metadata
- backend::mysql
- backend::os
- backend::pandas
- backend::pathlib
- backend::prometheus_client
- backend::re
- backend::services
- backend::sys
- backend::typing
- backend::unittest_mock
- backend::uvicorn
- commonlib::c_users_trendingpc_projects_ai_job_search_apps_commonlib_commonlib_sql_py
- commonlib::c_users_trendingpc_projects_ai_job_search_apps_commonlib_commonlib_test_terminalcolor_test_py
- commonlib::contextlib
- commonlib::datetime
- commonlib::functools
- commonlib::ipaddress
- commonlib::math
- commonlib::mysql_connector
- commonlib::mysql_connector_types
- commonlib::pandas
- commonlib::pdfplumber
- commonlib::platform
- commonlib::prometheus_client
- commonlib::pytest
- commonlib::queue
- commonlib::random
- commonlib::re
- commonlib::socket
- commonlib::statistics
- commonlib::structlog
- commonlib::sys
- commonlib::threading
- commonlib::time
- commonlib::traceback
- commonlib::typing
- commonlib::unittest
- commonlib::unittest_mock
- commonlib::warnings
- cron::commonlib_mongodb_provider
- cron::commonlib_repositories_cron_state_repository
- cron::commonlib_repositories_salary_history_repository
- cron::commonlib_sql_mysqlutil
- cron::commonlib_terminalcolor
- cron::datetime
- cron::dotenv
- cron::os
- cron::pytest
- cron::re
- cron::time
- cron::unittest_mock
- scrapper::commonlib_decorator_retry
- scrapper::commonlib_environmentutil
- scrapper::commonlib_exceptionutil
- scrapper::commonlib_keep_system_awake
- scrapper::commonlib_sql_mysqlutil
- scrapper::commonlib_sql_scrapper_state_repository
- scrapper::commonlib_stringutil
- scrapper::commonlib_systemutil
- scrapper::commonlib_terminalcolor
- scrapper::commonlib_terminalutil
- scrapper::datetime
- scrapper::email_header
- scrapper::email_message
- scrapper::glob
- scrapper::hashlib
- scrapper::imaplib
- scrapper::importlib_metadata
- scrapper::json
- scrapper::markdownify
- scrapper::math
- scrapper::os
- scrapper::pathlib
- scrapper::pytest
- scrapper::re
- scrapper::scrapling_fetchers
- scrapper::selenium
- scrapper::selenium_common_exceptions
- scrapper::selenium_webdriver_common_by
- scrapper::selenium_webdriver_common_keys
- scrapper::selenium_webdriver_firefox_options
- scrapper::selenium_webdriver_remote_webelement
- scrapper::selenium_webdriver_support
- scrapper::selenium_webdriver_support_ui
- scrapper::subprocess
- scrapper::sys
- scrapper::tabulate
- scrapper::tempfile
- scrapper::time
- scrapper::traceback
- scrapper::typing
- scrapper::undetected_chromedriver
- scrapper::unittest_mock
- scrapper::urllib3
- scrapper::urllib_parse
- web::c_users_trendingpc_projects_ai_job_search_apps_web_src_pages_skillsmanager_components_uselearnlist_skill
- web::c_users_trendingpc_projects_ai_job_search_apps_web_src_pages_viewer_api_jobs_appliedcompanyjob
- web::c_users_trendingpc_projects_ai_job_search_apps_web_src_pages_viewer_api_jobs_job
- web::c_users_trendingpc_projects_ai_job_search_apps_web_src_pages_viewer_api_jobs_joblistparams
- web::c_users_trendingpc_projects_ai_job_search_apps_web_src_pages_viewer_api_salary_salarycalculationresponse
- web::c_users_trendingpc_projects_ai_job_search_apps_web_src_pages_viewer_components_salarycalculator_salarycalculator_handlesave
- web::src_pages_skillsmanager_hooks_uselearnlist_skill
- web::src_pages_viewer_components_configurations_hooks_usefilterwatcher_polling_interval
- web::src_pages_viewer_components_configurations_hooks_usefilterwatcher_types_polling_interval
- ChartCard.mocks.ts
- JobDeleteService
- TestGlassdoorService
- TestJobBooleanKeys
- StatisticsFilters.tsx
- get_skill_context
- MessageContainer.tsx
- CompanySalaryHistoryJob
- TestBooleanFilterKeys
- scripts
- common/utils/sqlEditorUtils.ts
- CustomTooltip.tsx
- chartUtils.ts
- docker-entrypoint.sh
- eslint
- globals
- @types/prismjs
- @types/react
- vitest

## God Nodes (most connected - your core abstractions)
1. `MysqlUtil` - 144 edges
2. `yellow()` - 97 edges
3. `SeleniumService` - 90 edges
4. `PersistenceManager` - 79 edges
5. `retry()` - 52 edges
6. `getEnv()` - 50 edges
7. `sleep()` - 43 edges
8. `seleniumSocketConnRetry()` - 43 edges
9. `AiEnrichRepository` - 42 edges
10. `GmailService` - 41 edges

## Surprising Connections (you probably didn't know these)
- `ai-job-search` --depends_on--> `commonlib`  [EXTRACTED]
  pyproject.toml → apps/commonlib/pyproject.toml
- `FastCVMatcher` --uses--> `AiEnrichRepository`  [INFERRED]
  apps/aiCvMatcher/src/aiCvMatcher/cvMatcher.py → apps/commonlib/commonlib/aiEnrichRepository.py
- `FastCVMatcher` --uses--> `CVLoader`  [INFERRED]
  apps/aiCvMatcher/src/aiCvMatcher/cvMatcher.py → apps/commonlib/commonlib/cv_loader.py
- `FastCVMatcher` --uses--> `MysqlUtil`  [INFERRED]
  apps/aiCvMatcher/src/aiCvMatcher/cvMatcher.py → apps/commonlib/commonlib/sql/mysqlUtil.py
- `dataExtractor()` --calls--> `MysqlUtil`  [INFERRED]
  apps/aiEnrich3/src/aiEnrich3/dataExtractor.py → apps/commonlib/commonlib/sql/mysqlUtil.py

## Import Cycles
- 3-file cycle: `apps/web/src/pages/viewer/components/configurations/hooks/useFilterConfigurations.ts -> apps/web/src/pages/viewer/components/configurations/hooks/useFilterWatcher.ts -> apps/web/src/pages/viewer/components/configurations/hooks/useFilterWatcher.utils.ts -> apps/web/src/pages/viewer/components/configurations/hooks/useFilterConfigurations.ts`

## Communities (684 total, 348 thin omitted)

### Community 0 - "retry"
Cohesion: 0.05
Nodes (22): Enum, Exception, Attempt to call a function, if it fails, try again with a specified delay., retry(), StackTrace, test_retry_custom_exception_handling(), test_retry_eventual_failure(), test_retry_eventual_success() (+14 more)

### Community 3 - "terminalColor.py"
Cohesion: 0.10
Nodes (23): Librería común para el monorepo, getAndCheckEnvVars(), htmlToMarkdown(), join(), printPage(), printScrapperTitle(), removeInvalidScapes(), removeLinks() (+15 more)

### Community 4 - "jobs.py"
Cohesion: 0.16
Nodes (28): get_applied_jobs_by_company(), get, bulk_delete_jobs(), bulk_update_jobs(), BulkJobDelete, BulkJobUpdate, create_job(), BaseModel (+20 more)

### Community 6 - "seleniumSocketConnRetry"
Cohesion: 0.05
Nodes (25): BrowserService, Remote, Switch or create to tab name. If no name specified switches to default tab., Poll driver.window_handles until a new handle (not in old_handles) appears., Close a window and switch back to the default tab., ElementService, Remote, WebElement (+17 more)

### Community 9 - "StatisticsApi.ts"
Cohesion: 0.23
Nodes (17): buildDateParams(), FilterConfigStat, getFilterConfigStats(), getHistoryStats(), getSourcesByDate(), getSourcesByHour(), getSourcesByWeekday(), HistoryStat (+9 more)

### Community 12 - "PersistenceManager"
Cohesion: 0.13
Nodes (7): PersistenceManager, Any, Returns (should_skip, start_page), manager(), mock_repo(), fixture, ScrapperStateRepository

### Community 14 - "IndeedScraplingNavigator"
Cohesion: 0.11
Nodes (5): _extract_text(), IndeedScraplingNavigator, create_mock_scrapling_service(), MockSelector, TestIndeedScraplingNavigator

### Community 15 - "Settings.tsx"
Cohesion: 0.23
Nodes (15): renderGroup(), renderInlineItem(), renderScrapperEditor(), renderSubgroup(), SetStateAction, Settings(), sortSubGroups(), mockEnvSettings (+7 more)

### Community 18 - "yellow"
Cohesion: 0.06
Nodes (35): FastCVMatcher, run(), footer(), printJob(), getDatetimeNowStr(), parse_skill_llm_output(), process_skill_enrichment(), Common logic for skill enrichment.          :param mysql: MysqlUtil instance (+27 more)

### Community 19 - "patch"
Cohesion: 0.12
Nodes (17): auto_discover_host(), discover_mysql_hosts(), get_local_subnets(), Auto-discover MySQL host on LAN. Returns host IP string or None., Detect local LAN subnets by finding the machine's IP via UDP connect., Scan a list of hosts on the given port. Returns list of responsive IPs., Scan LAN for hosts with open MySQL port. Returns list of IPs.      Args:, Verify host is our MySQL — connect and check the database exists. (+9 more)

### Community 20 - "MysqlUtil"
Cohesion: 0.06
Nodes (18): _save_skill_result(), MysqlUtil, any, Insert job record with given params., Check if job exists by job_id., Insert job from dict data., Get all scrapper state as {site: state_dict}., Replace all scrapper state entries. (+10 more)

### Community 21 - "TestBaseNavigator"
Cohesion: 0.13
Nodes (4): ConcreteNavigator, fixture, parametrize, TestBaseNavigator

### Community 22 - "configurations/hooks/useFilterConfigurations.ts"
Cohesion: 0.08
Nodes (24): ConfigurationDropdown(), ConfigurationDropdownProps, ConfigurationInput(), ConfigurationInputProps, useConfigDropdownState(), useConfigOperations(), UseConfigOperationsProps, useConfigToggles() (+16 more)

### Community 26 - "WakeableTimer"
Cohesion: 0.21
Nodes (11): mock_sleep(), mock_windows_api(), fixture, patch, test_console_timer_calls_wakeable_timer(), test_wakeable_timer_other_os(), test_wakeable_timer_windows(), Timer that can wake the Windows system from suspend state.     Uses CreateWaita (+3 more)

### Community 27 - "Viewer.tsx"
Cohesion: 0.07
Nodes (24): ConfirmModal(), ConfirmModalProps, normalizeFilters(), RESETTABLE_FILTERS, BooleanFilters(), BooleanFiltersProps, BooleanFilterGroups(), BooleanFilterGroupsProps (+16 more)

### Community 29 - "aiEnrichSkill/test/config_test.py"
Cohesion: 0.15
Nodes (28): get_backend(), get_hf_model_id(), get_hf_repetition_penalty(), get_hf_temperature(), get_hf_top_p(), get_input_max_len(), get_max_new_tokens(), get_ollama_base_url() (+20 more)

### Community 31 - "ai_helpers.py"
Cohesion: 0.10
Nodes (40): combineTaskResults(), _expand_parenthesized_skills(), flatten_skill_groups(), listsToString(), mapJob(), _normalizeModality(), Combina los resultados de todas las tareas en un único JSON, validateResult() (+32 more)

### Community 33 - "persistence_manager_test.py"
Cohesion: 0.13
Nodes (16): parametrize, test_add_failed_keyword(), test_clear_state(), test_finalize_scrapper(), test_get_failed_keywords(), test_get_last_execution(), test_get_state(), test_is_state_stale() (+8 more)

### Community 34 - "test-utils.tsx"
Cohesion: 0.12
Nodes (12): testQueryClient, mockJob, mockJob, mockJob, mockJobs, cleanupFakeTimers(), createMockFilters(), createMockJob() (+4 more)

### Community 36 - "GmailService"
Cohesion: 0.07
Nodes (22): GmailService, Check if Gmail service is connected, Close Gmail connection, parametrize, Test connect fails when credentials missing, Test connect handles exception gracefully, Test connect succeeds, Test Gmail service functionality (+14 more)

### Community 42 - "ViewerApi.ts"
Cohesion: 0.06
Nodes (37): CvMatchBarProps, calculateLapsedTime(), calculateLapsedTimeDetail(), getDayDiff(), getLapsed(), getLapsedParts(), getLapsedTime(), LapsedTime (+29 more)

### Community 43 - "useViewer.ts"
Cohesion: 0.11
Nodes (21): useModalityValues(), createDefaultJobMutationsProps(), createWrapper(), DEFAULT_FILTERS, STATE_FIELDS, createMockJob(), createMockProps(), mutationMocks (+13 more)

### Community 46 - "jobsApi"
Cohesion: 0.19
Nodes (11): NotificationService, mocks, jobsApi, cleanupMocks(), createWrapper(), mockSavedConfigs, resetTestQueryClient(), testQueryClient (+3 more)

### Community 47 - "environmentUtil.py"
Cohesion: 0.05
Nodes (48): get_env_settings(), get_scrapper_state(), get, post, update_env_setting(), update_env_settings_bulk(), update_scrapper_state(), BaseModel (+40 more)

### Community 49 - "extract_boolean_filters"
Cohesion: 0.19
Nodes (9): extract_boolean_filters(), Extract boolean filters from a filters dictionary.      Only includes keys tha, Tests for extract_boolean_filters function., Test extracting all boolean filter keys from a dictionary., Test extracting only some boolean filters., Test extracting from empty dictionary., Test extracting with custom key list., Test that missing keys are simply not included. (+1 more)

### Community 51 - "TecnoempleoExecutor"
Cohesion: 0.08
Nodes (19): find_last_duplicated(), Find the last duplicated job by title, company (excluding 'Joppy').     Returns, test_find_last_duplicated_empty_args(), test_find_last_duplicated_found(), test_find_last_duplicated_joppy(), test_find_last_duplicated_not_found(), Returns ok: bool, jobExistsInDb: bool, TecnoempleoExecutor (+11 more)

### Community 53 - "SeleniumService"
Cohesion: 0.06
Nodes (3): WebElement, SeleniumService, TestSeleniumService

### Community 55 - "Adaptive scraping"
Cohesion: 0.05
Nodes (36): Adaptive scraping, How the adaptive scraping feature works, How to use adaptive feature, Known Issues, No Matches Found, Real-World Scenario, The CSS/XPath Selection way, The manual way (+28 more)

### Community 56 - "sqlUtil.py"
Cohesion: 0.12
Nodes (17): avoidInjection(), binaryColumnIgnoreCase(), deleteJobsQuery(), formatSql(), getAndFilter(), getColumnTranslated(), inFilter(), Validate that a string doesn't contain potentially dangerous SQL patterns. (+9 more)

### Community 57 - "aiEnrich/dataExtractor.py"
Cohesion: 0.09
Nodes (30): dataExtractor(), get_job_enabled(), get_model(), get_ollama_base_url(), get_timeout_job(), _getJobIdsList(), _handle_error(), _process_job_safe() (+22 more)

### Community 58 - "JobRepository"
Cohesion: 0.06
Nodes (22): JobRepository, Any, callable, Repository for job-specific database operations., Insert a job record into the database.          Args:             params: Tup, Check if job exists in database by job_id., Insert job data and return row ID if successful.          Args:             j, fixture (+14 more)

### Community 61 - "GlassdoorExecutor"
Cohesion: 0.14
Nodes (12): GlassdoorExecutor, mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), fixture, parametrize, patch (+4 more)

### Community 66 - "SalaryCalculator.tsx"
Cohesion: 0.22
Nodes (13): JobDetail(), formatSavedLabel(), SalaryCalculator(), SalaryCalculatorProps, SalaryCalculatorResults(), SalaryCalculatorResultsProps, CalcMode, paramsEqual() (+5 more)

### Community 67 - "MetricsCollector"
Cohesion: 0.06
Nodes (23): get_enum_values(), get_schema(), get, patch, test_get_schema(), DdlRepository, patch, test_get_enum_values() (+15 more)

### Community 68 - "dateUtil.py"
Cohesion: 0.14
Nodes (12): get_tz(), getDatetimeNow(), getTimeUnits(), parseDatetime(), Convert seconds to a detailed time unit string (e.g., 1h 35m 10s)., parametrize, patch, TestTimeFunctions (+4 more)

### Community 71 - "ScrapperStateRepository"
Cohesion: 0.11
Nodes (7): Any, callable, ScrapperStateRepository, fixture, parametrize, Tests for scrapper_state_repository module., TestScrapperStateRepository

### Community 72 - "IndeedService"
Cohesion: 0.09
Nodes (14): IndeedExecutor, Return true if job was inserted, mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), fixture, parametrize (+6 more)

### Community 74 - "build_jobs_where_clause"
Cohesion: 0.14
Nodes (23): build_jobs_where_clause(), _col(), get_boolean_condition(), get_days_old_condition(), get_modality_condition(), get_salary_condition(), get_search_conditions(), parse_job_order() (+15 more)

### Community 75 - "Most Important Improvements for this Monorepo"
Cohesion: 0.06
Nodes (30): 1.1 Critical: Files Exceeding 200-Line Limit (Architecture Rule #1), 1.2 Module Consolidation: AI Enrich Variants, 1.3 Commonlib Coupling Issues, 1.4 Layer Architecture Violations, 1.5 Service Layer Analysis, 1.6 Test Architecture, 1. PYTHON MODULES (Backend & Commonlib), 2.1 Component File Size Analysis (+22 more)

### Community 76 - "ContextLoader"
Cohesion: 0.12
Nodes (7): init_routes(), ContextLoader, Path, create_app(), run(), TempFiles, TestMain

### Community 78 - "AnswerResult"
Cohesion: 0.17
Nodes (8): AIProvider, AnswerResult, ABC, get_pipeline(), OpenAIProvider, TestAIProvider, TestAnswerResult, QuestionAnsweringService

### Community 79 - "TransactionManager"
Cohesion: 0.14
Nodes (12): Get a cursor with automatic connection and cleanup., Any, MySQLConnection, Handles database transactions including rollback and commit operations., Execute a callback within a transaction, committing on success or         rolli, Execute a query callback without transaction commit., Execute a query and commit, returning affected row count., Execute multiple queries in a single transaction, returning row counts. (+4 more)

### Community 80 - "IndeedNavigator"
Cohesion: 0.06
Nodes (9): IndeedNavigator, WebElement, Close modal 'email me with new offers'.  It appears randomly in time after searc, pre scroll to bottom to force load of li's, fixture, object, parametrize, patch (+1 more)

### Community 81 - "useSqlEditor.ts"
Cohesion: 0.16
Nodes (13): DdlSchemaResponse, fetchDdlSchema(), getModalityValues(), mockApiClient, useSqlEditor(), UseSqlEditorProps, SqlEditor(), SqlEditorProps (+5 more)

### Community 82 - "Viewer.interactions.test.tsx"
Cohesion: 0.19
Nodes (18): MockFilters(), MockJobActions(), MockJobDetail(), MockJobEditForm(), MockJobList(), MockReactMarkdownCustom(), MockViewTabs(), runTimers() (+10 more)

### Community 83 - "compilerOptions"
Cohesion: 0.07
Nodes (27): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+19 more)

### Community 84 - "aiEnrichNew/services/job_enrichment_service.py"
Cohesion: 0.11
Nodes (30): get_batch_size(), get_enrich_timeout_job(), get_input_max_len(), get_job_system_prompt(), should_cleanup_gpu(), build_job_prompt_messages(), map_db_job_to_domain(), Any (+22 more)

### Community 86 - "filter_configurations_service_test.py"
Cohesion: 0.08
Nodes (26): mock_repo(), fixture, patch, Test error when deleting non-existent configuration, Test seeding default configurations from JSON file, Test auto-seeding when database is empty, Test no seeding when database already has data, Test getting configuration by ID (+18 more)

### Community 88 - "TestLinkedinNavigator"
Cohesion: 0.10
Nodes (3): parametrize, patch, TestLinkedinNavigator

### Community 90 - "aiEnrich3/services/test/job_enrichment_service_test.py"
Cohesion: 0.17
Nodes (24): enrich_jobs(), _fetch_and_sort_jobs(), _process_job_batch_local(), Any, retry_failed_job(), _save_job_result(), _update_error_state(), mock_pipeline() (+16 more)

### Community 91 - "query_ollama"
Cohesion: 0.18
Nodes (8): _get_num_predict(), ping_ollama(), query_ollama(), _strip_provider_prefix(), patch, TestPingOllama, TestQueryOllama, TestStripProviderPrefix

### Community 93 - "skills.py"
Cohesion: 0.13
Nodes (21): bulk_create_skills(), create_skill(), delete_skill(), get_skill(), list_skills(), delete, get, post (+13 more)

### Community 94 - "filter_configurations_repository_test.py"
Cohesion: 0.08
Nodes (25): mock_db(), fixture, Test updating configuration, Test partial update (name only), Test deleting configuration, Create repository with mocked database, Test counting configurations, Test finding all configurations (+17 more)

### Community 95 - "CompanySynonymService"
Cohesion: 0.09
Nodes (10): JobQueryRepository, test_find_applied_by_company(), CompanySynonymService, Any, JobQueryService, Any, mock_repo(), mock_synonym_service() (+2 more)

### Community 96 - "QueryExecutor"
Cohesion: 0.09
Nodes (18): MySQLConnection, Get the MySQL connection., Backward compatible property for connection access., Setter for backward compatibility., callable, T, QueryExecutor, Execute a query callback with cursor management. (+10 more)

### Community 97 - "aiEnrich3/dataExtractor.py"
Cohesion: 0.17
Nodes (19): get_batch_size(), get_input_max_len(), get_job_enabled(), get_skill_enabled(), getEnvBool(), dataExtractor(), run(), parametrize (+11 more)

### Community 102 - "viewer.helpers.ts"
Cohesion: 0.17
Nodes (23): setupApiSafetyNet(), setupAppBootstrapMocks(), setupModalityMock(), setupPageLogging(), setupSalaryHistoryMocks(), setupTimezoneMock(), searchJobs(), setupDefaultJobsRoute() (+15 more)

### Community 103 - "persistence_manager.py"
Cohesion: 0.10
Nodes (25): get_debug(), ScrapperScheduler, Check if preload is needed based on properties., runPreload(), create_executor(), process_page_url(), Process a specific URL (only LinkedIn is currently supported)., Factory method to create executor instances by name. (+17 more)

### Community 106 - "devDependencies"
Cohesion: 0.08
Nodes (25): devDependencies, baseline-browser-mapping, coverage-badges-cli, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh, @testing-library/jest-dom, @testing-library/react (+17 more)

### Community 107 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 108 - "SalaryHistoryRepository"
Cohesion: 0.13
Nodes (7): get_best_candidate(), search_partial_company(), datetime, SalaryHistoryRepository, parametrize, TestGetBestCandidate, TestSearchPartialCompany

### Community 113 - "GmailConnectionError"
Cohesion: 0.23
Nodes (10): EmailNotFoundError, GmailConnectionError, GmailTimeoutError, Exception, Exception raised when verification code cannot be extracted from email, Exception raised when Gmail operation times out, Exception raised when Gmail connection fails, Exception raised when expected email is not found (+2 more)

### Community 115 - "aiEnrich3/pipeline.py"
Cohesion: 0.11
Nodes (13): GLiNER, SalaryExtractor, GLiNER, Extracts skills from text and separates them into required and optional., SkillsExtractor, extractor(), fixture, parametrize (+5 more)

### Community 116 - "statistics_archived.py"
Cohesion: 0.13
Nodes (18): get_archived_history_stats(), get_archived_sources_by_date(), get_archived_sources_by_hour(), get_archived_sources_by_weekday(), get_combined_history_stats(), get_combined_sources_by_date(), get_combined_sources_by_hour(), get_combined_sources_by_weekday() (+10 more)

### Community 117 - "job_delete_service_test.py"
Cohesion: 0.19
Nodes (7): mock_get_job(), mock_repo(), fixture, parametrize, service(), service_with_callback(), test_update_jobs_by_ids()

### Community 118 - "TestTransactionManager"
Cohesion: 0.09
Nodes (13): fixture, Tests for transaction_manager module., Mock get_connection_ctx function., Create TransactionManager instance with mock., Should initialize with get_connection_ctx function., execute_transaction should commit on success., execute_transaction should rollback on error., execute_query should not commit (read-only). (+5 more)

### Community 120 - "InfojobsExecutor"
Cohesion: 0.11
Nodes (10): InfojobsExecutor, mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), fixture, parametrize, TestInfojobsExecutor (+2 more)

### Community 121 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+14 more)

### Community 122 - "Plan 0: Observability (Foundation for All Improvements)"
Cohesion: 0.09
Nodes (22): aiEnrich3, aiEnrich (3 files), aiEnrichNew, `apps/backend/api/metrics.py`, `apps/commonlib/commonlib/metrics_collector.py`, `apps/commonlib/commonlib/observability.py`, Architecture, Architecture (+14 more)

### Community 123 - "enrichment_service_test.py"
Cohesion: 0.21
Nodes (21): _enrich_ollama(), enrich_skills(), generate_skill_description_ollama(), capture_process_batch_callbacks(), make_ollama_mocks(), run_process_skill_batch(), parametrize, patch (+13 more)

### Community 124 - "routes.py"
Cohesion: 0.24
Nodes (19): answer(), answer_batch(), follow_up(), health(), get, post, AnswerRequest, AnswerResponse (+11 more)

### Community 125 - "FilterConfigurationsService"
Cohesion: 0.10
Nodes (26): create_configuration(), delete_configuration(), get_all_configurations(), get_configuration(), get_service(), delete, get, post (+18 more)

### Community 127 - "TestJobQueries"
Cohesion: 0.09
Nodes (12): Tests for job_queries module., Tests for SQL query constants., QRY_FIND_JOB_BY_JOB_ID should be a non-empty string., QRY_INSERT should be a non-empty string., QRY_SELECT_JOBS_VIEWER should be a non-empty string., QRY_SELECT_COUNT_JOBS should be a non-empty string., SELECT_APPLIED_JOB_IDS_BY_COMPANY should be a non-empty string., SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT should be a non-empty string. (+4 more)

### Community 128 - "IndeedScraplingExecutor"
Cohesion: 0.18
Nodes (8): IndeedScraplingExecutor, Execution logic for Indeed using Scrapling framework to bypass Cloudflare, mock_env_vars(), mock_mysql(), mock_persistence_manager(), mock_selenium(), fixture, TestIndeedScraplingExecutor

### Community 129 - "IndeedAuthenticator"
Cohesion: 0.09
Nodes (12): check_for_otp_error(), is_element_present(), raise_if_otp_invalid(), wait_for_cloudflare_filter(), wait_for_element_present(), IndeedAuthenticator, fixture, TestExceptionHandler (+4 more)

### Community 132 - "Modal.tsx"
Cohesion: 0.15
Nodes (8): Modal(), ModalProps, useAutoResizeTextArea(), EditSynonymGroupModalProps, AppliedModal(), AppliedModalProps, JobFormFields(), JobFormFieldsProps

### Community 134 - "manifest.json"
Cohesion: 0.10
Nodes (20): background, service_worker, content_scripts, description, host_permissions, icons, 128, 16 (+12 more)

### Community 135 - "BaseExecutor"
Cohesion: 0.09
Nodes (15): cleanUnresolvedTrace(), parametrize, TestAbortExecution, TestDebug, TestPageExists, TestRunPreload, abortExecution(), pageExists() (+7 more)

### Community 137 - "jobs_test.py"
Cohesion: 0.15
Nodes (20): _get_query_from_mock(), mock_db_session(), fixture, parametrize, patch, Test listing jobs with boolean and combined filters, Test listing jobs filtered by specific IDs, Test listing jobs with created_after filter (+12 more)

### Community 138 - "CompanySynonymRepository"
Cohesion: 0.18
Nodes (11): CompanySynonymRepository, Any, test_create_group(), test_create_group_empty(), test_find_synonyms(), test_find_synonyms_not_found(), test_list_groups(), test_list_groups_empty() (+3 more)

### Community 139 - "JobSnapshotService"
Cohesion: 0.16
Nodes (5): JobSnapshotService, datetime, mock_repo(), fixture, service()

### Community 141 - "TestGetConnection"
Cohesion: 0.10
Nodes (14): mock_mysql_connect(), fixture, Tests for connection_manager module., Mock the mysqlConnector.connect to avoid real DB connection.     Also resets CO, Tests for get_connection function., Should return a MySQL connection object., Pool should only be created once across multiple calls., Third call (get from pool) should only pass pool_name. (+6 more)

### Community 142 - "architecture_test.py"
Cohesion: 0.22
Nodes (15): check_layer(), get_file_imports(), _validate_dependencies(), getLongFiles(), get_test_naming_violations(), get_files_without_sibling_test(), get_test_location_violations(), count_lines() (+7 more)

### Community 143 - ".layout_check.cjs"
Cohesion: 0.10
Nodes (19): api, distinctBands, extX, fn, fs, html, internal, intMaxX (+11 more)

### Community 145 - "statistics_service_test.py"
Cohesion: 0.14
Nodes (7): Any, StatisticsService, mock_filter_repo(), mock_jobs_repo(), mock_repo(), fixture, service()

### Community 147 - "AiEnrichRepository"
Cohesion: 0.08
Nodes (18): _update_error_state(), AiEnrichRepository, emptyToNone(), maxLen(), Any, MockMysqlUtil, mockRepo(), test_count_pending_cv_match() (+10 more)

### Community 149 - "testSetup.ts"
Cohesion: 0.18
Nodes (15): createAxiosInstanceMock(), createAxiosMock(), mockAxios, setupAxiosMock(), cleanupDOMMocks(), setupDOMMocks(), setupElementSizeMocks(), setupIntersectionObserverMock() (+7 more)

### Community 150 - "Screenshots"
Cohesion: 0.06
Nodes (34): AI daemons & fullstack app logs, AI Job Search Monorepo  [![backend-build-lint-and-tests](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml/badge.svg)](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml), Build the graph, Change detection rules, CI / GitHub Actions Pipeline, Cross-module edges, Distributed execution, Docker Compose Profiles (+26 more)

### Community 152 - "AGENTS.md"
Cohesion: 0.11
Nodes (17): Architecture, Build and Development Commands, Code Style, Configuration, Database, E2E Tests (apps/e2e), Environment Setup, graphify (+9 more)

### Community 153 - "SkillsService"
Cohesion: 0.25
Nodes (11): Skill, Any, Skill, SkillsService, patch, test_bulk_create_skills(), test_create_skill(), test_delete_skill() (+3 more)

### Community 154 - "WatcherService"
Cohesion: 0.11
Nodes (19): get_watcher_service(), mock_db(), fixture, patch, test_get_watcher_stats_empty_ids(), test_get_watcher_stats_from_view(), Any, WatcherRepository (+11 more)

### Community 156 - "JobsRepository"
Cohesion: 0.20
Nodes (6): _execute_with_error_handler(), JobsRepository, Any, execute_with_error_handler(), test_execute_with_error_handler_success(), test_execute_with_error_handler_with_items()

### Community 157 - "StatisticsArchivedService"
Cohesion: 0.18
Nodes (6): Any, StatisticsArchivedService, mock_snapshots_repo(), mock_stats_repo(), fixture, service()

### Community 158 - "TestQueryExecutor"
Cohesion: 0.09
Nodes (13): fixture, Tests for query_executor module., Mock get_connection_ctx function., Create QueryExecutor instance with mock., Should initialize with get_connection_ctx function., count should return the count value., fetch_one should return a single row., fetch_all should return all matching rows. (+5 more)

### Community 159 - "scheduler_test.py"
Cohesion: 0.22
Nodes (16): _parse_cadency(), Scheduler, _MockJob, test_cron_job_base_run_raises(), test_parse_cadency_days(), test_parse_cadency_default(), test_parse_cadency_hours(), test_parse_cadency_minutes() (+8 more)

### Community 160 - "EditSkillModal.tsx"
Cohesion: 0.12
Nodes (12): FormField(), FormFieldProps, EditSkillModal(), SkillDescriptionField(), SkillDescriptionFieldProps, SkillLearningPathField(), SkillLearningPathFieldProps, testQueryClient (+4 more)

### Community 161 - ".opencode/AGENTS.md"
Cohesion: 0.11
Nodes (17): Architecture Patterns, Backend (FastAPI Layered), Build & Test Commands, Code Style Guidelines, Definition of Done, Development & Linting, Environment Setup, Frontend (React/TypeScript) (+9 more)

### Community 162 - "getEnv"
Cohesion: 0.26
Nodes (15): get_cv_path(), get_hf_model(), get_looking_for_path(), get_max_tokens(), get_openai_api_key(), get_openai_model(), get_openrouter_api_key(), get_openrouter_model() (+7 more)

### Community 163 - "company_synonyms.py"
Cohesion: 0.21
Nodes (15): add_to_group(), create_synonym_group(), get_synonyms(), list_synonym_groups(), delete, get, post, remove_name() (+7 more)

### Community 164 - "create_mock_db"
Cohesion: 0.23
Nodes (16): parametrize, patch, test_add_to_group(), test_create_group(), test_create_group_invalid(), test_get_synonyms(), test_get_synonyms_not_found(), test_list_synonym_groups() (+8 more)

### Community 165 - "CombinedStatsRepository"
Cohesion: 0.25
Nodes (7): CombinedStatsRepository, DataFrame, test_get_combined_history_stats_df(), test_get_combined_history_stats_df_with_dates(), test_get_combined_sources_by_date_df_with_dates(), test_get_combined_sources_by_hour_df_with_dates(), test_get_combined_sources_by_weekday_df_with_dates()

### Community 167 - "JobSnapshotRepository"
Cohesion: 0.14
Nodes (6): JobSnapshotRepository, datetime, mock_mysql(), fixture, test_get_snapshots_by_reason(), test_save_snapshot()

### Community 168 - "exceptionUtil_test.py"
Cohesion: 0.22
Nodes (17): filter_trace_by_paths(), getProjectTraceItems(), Exception, try_or_warn(), fail_fn(), ok_fn(), parametrize, patch (+9 more)

### Community 169 - "connection_manager.py"
Cohesion: 0.12
Nodes (20): get_connection(), getConnection(), _init_pool(), _parse_host_targets(), _parse_ip_range(), _probe_mysql(), MySQLConnection, Resolve MySQL host — try configured targets, fall back to LAN discovery. (+12 more)

### Community 170 - "EmailReader"
Cohesion: 0.14
Nodes (9): EmailReader, Wait for and extract the latest verification code from a sender, Close the IMAP connection, Connect to Gmail IMAP server, Select the inbox folder, Search for emails from a specific sender since a given date, Extract email body from email, Extract verification code from email subject (4-6 digits) (+1 more)

### Community 171 - "TestEmailReader"
Cohesion: 0.17
Nodes (4): fixture, parametrize, patch, TestEmailReader

### Community 172 - "AI Job Search — Metrics & Observability"
Cohesion: 0.11
Nodes (17): Accessing the Dashboard, Adding a New Enrichment Module, AI Job Search — Metrics & Observability, Architecture, Business Overview, Dashboard, Data Flow, Docker Volume Mounts for Logs (+9 more)

### Community 173 - "KeepSystemAwake"
Cohesion: 0.19
Nodes (11): AbstractContextManager, _clear_power_request(), _close_handle(), DetailedStructure, KeepSystemAwake, Context manager to prevent the system from going to sleep or turning off the dis, REASON_CONTEXT, ReasonUnion (+3 more)

### Community 174 - "Advanced usages"
Cohesion: 0.12
Nodes (16): Advanced usages, Concurrency Control, Detailed Stats, How It Works, Knowing If You're Resuming, Lifecycle Hooks, Logging, on_close (+8 more)

### Community 175 - "observability.py"
Cohesion: 0.15
Nodes (15): get_job_enabled(), dataExtractor(), retry_failed_jobs(), get_pipeline(), run(), patch, test_dataExtractor_calls_service(), test_retry_calls_service() (+7 more)

### Community 176 - "AI Job Search API"
Cohesion: 0.12
Nodes (16): AI Job Search API, API Documentation, API Endpoints, Company Synonyms, Database, Features, How it affects the applied-by-company search, Installation (+8 more)

### Community 178 - "SkillsRepository"
Cohesion: 0.24
Nodes (9): Any, Skill, SkillsRepository, patch, test_create_skill(), test_delete_skill(), test_list_skills(), test_update_skill() (+1 more)

### Community 179 - "CVLoader"
Cohesion: 0.26
Nodes (4): CVLoader, extractTextFromPDF(), patch, TestCVLoader

### Community 181 - "stringUtil.py"
Cohesion: 0.26
Nodes (8): hasLen(), hasLenAnyText(), removeBlanks(), removeExtraEmptyLines(), removeNewLines(), toBool(), parametrize, TestStringUtil

### Community 182 - "Job Scrappers"
Cohesion: 0.12
Nodes (17): Architecture, Configuration, Dual Architecture (Selenium vs Scrapling), Dynamic Cadency (Time-based), Features, Gmail Configuration, Installation, Job Scrappers (+9 more)

### Community 183 - "TestLinkedinService"
Cohesion: 0.15
Nodes (3): fixture, parametrize, TestLinkedinService

### Community 184 - "dependencies"
Cohesion: 0.12
Nodes (17): dependencies, axios, prismjs, react-dom, react-markdown, react-router-dom, react-simple-code-editor, recharts (+9 more)

### Community 185 - "Plan B: RAG Cache Layer (Skip LLM Inference for Similar Jobs)"
Cohesion: 0.12
Nodes (16): `apps/aiEnrich/pyproject.toml`, `apps/aiEnrich/src/aiEnrich/crew.py`, `apps/aiEnrich/src/aiEnrich/dataExtractor.py`, `apps/aiEnrich/src/aiEnrich/embedding_service.py`, `apps/aiEnrich/src/aiEnrich/rag_cache.py`, Architecture, Dependencies, Files to Create (+8 more)

### Community 186 - "panel.js"
Cohesion: 0.16
Nodes (14): answerAll(), answerAllBtn, container, detectAllFields(), errorSection, errorText, fields, fillAllBtn (+6 more)

### Community 188 - "AI Form Filler"
Cohesion: 0.12
Nodes (15): 1. Prepare context documents, 2. Start the backend, 3. Install the browser extension, AI Form Filler, AI Providers, API Endpoints, Architecture, Development (+7 more)

### Community 189 - "TestQuestionAnsweringService"
Cohesion: 0.37
Nodes (4): patch, TestQuestionAnsweringService, make_mock_cfg(), make_mock_provider()

### Community 190 - "JobDeleteRepository"
Cohesion: 0.22
Nodes (6): JobDeleteRepository, Any, mock_mysql(), fixture, test_delete_jobs_by_ids(), test_delete_jobs_by_ids_empty()

### Community 191 - "LinkedinExecutor"
Cohesion: 0.14
Nodes (8): LinkedinExecutor, mock_mysql(), mock_pm(), mock_selenium(), mocks(), fixture, parametrize, TestLinkedinExecutor

### Community 192 - "TestIndeedService"
Cohesion: 0.16
Nodes (3): parametrize, patch, TestIndeedService

### Community 193 - "Plan A: Direct Ollama API (Remove CrewAI)"
Cohesion: 0.12
Nodes (15): `apps/aiEnrich/pyproject.toml`, `apps/aiEnrich/src/aiEnrich/crew.py`, `apps/aiEnrich/src/aiEnrich/dataExtractor.py`, `apps/aiEnrich/src/aiEnrich/ollama_client.py`, `apps/aiEnrich/src/aiEnrich/skillEnricher.py`, Architecture, Dependencies, Files to Create (+7 more)

### Community 194 - "Plan C: Two-Stage Pipeline (aiEnrich3 Fast Path + aiEnrich LLM Fallback)"
Cohesion: 0.12
Nodes (15): `apps/aiEnrich3/src/aiEnrich3/pipeline.py`, `apps/aiEnrich/pyproject.toml`, `apps/aiEnrich/src/aiEnrich/dataExtractor.py`, `apps/aiEnrich/src/aiEnrich/hybrid_extractor.py` (new), Architecture, Files to Modify, Goal, Implementation Order (+7 more)

### Community 195 - "Plan E: Prompt & Token Optimization (Quick Wins)"
Cohesion: 0.12
Nodes (15): Dependencies, E.1: Reduce Output Tokens (`num_predict`), E.2: Input Compression, E.3: Ollama JSON Mode, E.4: Optimized Prompt Template, E.5: Disable Skill Enrichment in Main Loop, Files to Modify, Goal (+7 more)

### Community 196 - "Requests & Responses"
Cohesion: 0.13
Nodes (13): Callbacks, Deduplication, Disabling Referer Flow, Request Meta, Request Priority, Requests & Responses, Response.follow(), The Request Object (+5 more)

### Community 197 - "cvMatcher_test.py"
Cohesion: 0.23
Nodes (13): mock_all(), fixture, test_disabled(), test_footer_err(), test_init(), test_job_none(), test_match(), test_match_exc() (+5 more)

### Community 198 - "LinkedinNavigator"
Cohesion: 0.11
Nodes (5): LinkedinNavigator, Login in english is a button[type=submit], in spanish is a button[type=button], mock_selenium(), navigator(), fixture

### Community 199 - "process_batch"
Cohesion: 0.20
Nodes (6): process_batch(), Any, Exception, T, patch, TestLLMUtils

### Community 200 - "SnapshotsRepository"
Cohesion: 0.21
Nodes (6): DataFrame, SnapshotsRepository, mock_connection(), fixture, test_get_history_stats_df(), test_get_snapshot_count_by_reason()

### Community 201 - "StatisticsRepository"
Cohesion: 0.28
Nodes (7): DataFrame, StatisticsRepository, patch, test_get_history_stats_df(), test_get_history_stats_df_with_dates(), test_get_sources_by_date_df(), test_get_sources_by_hour_df()

### Community 202 - "MongoDbProvider"
Cohesion: 0.22
Nodes (9): get_mongo_provider(), MongoDbProvider, CQRS-style MongoDB connection provider.      Separates read and write connecti, test_get_database_returns_database(), test_get_database_write_returns_writer(), test_get_mongo_provider_caches(), test_get_mongo_provider_different_keys(), test_provider_creates_read_and_write_clients() (+1 more)

### Community 203 - "CompanySalaryHistoryScanner"
Cohesion: 0.29
Nodes (9): CompanySalaryHistoryScanner, patch, test_scanner_backfill_new_jobs(), test_scanner_incremental_new_jobs(), test_scanner_last_run_at_no_updates(), test_scanner_no_new_jobs(), test_scanner_updated_jobs_no_prior_record(), test_scanner_updated_jobs_salary_changed() (+1 more)

### Community 204 - "e2e/package.json"
Cohesion: 0.13
Nodes (14): devDependencies, @playwright/test, @types/node, typescript, @types/node, typescript, name, private (+6 more)

### Community 205 - "ScrapperStateCalculator"
Cohesion: 0.26
Nodes (5): ScrapperStateCalculator, mocks(), fixture, parametrize, TestScrapperStateCalculator

### Community 206 - "scrapper_scheduler_test.py"
Cohesion: 0.24
Nodes (13): mock_selenium_service(), mocks(), fixture, parametrize, patch, run_mocks(), scheduler(), setup_scrappers() (+5 more)

### Community 207 - "IndeedGmailService"
Cohesion: 0.20
Nodes (5): IndeedGmailService, Wait for Indeed verification code with predefined sender, Get verification code from latest Indeed email, Indeed-specific Gmail service with predefined sender and convenience methods, TestIndeedGmailService

### Community 208 - "TestBaseService"
Cohesion: 0.15
Nodes (4): ConcreteService, fixture, parametrize, TestBaseService

### Community 209 - "FilterConfigurationsTestUtils.tsx"
Cohesion: 0.23
Nodes (9): byCompanyConfigs, TestConfig, testConfigs, configureMockServiceBehavior(), mockFilters, { mockService }, setup(), waitForLoad() (+1 more)

### Community 210 - "Plan F: Combined / Recommended Approach"
Cohesion: 0.13
Nodes (14): Architecture, Comparison Script, Configuration, Goal, Gradual Rollout, Implementation Phases, Per-Phase Validation, Performance Budget (+6 more)

### Community 211 - "Setup Guide"
Cohesion: 0.13
Nodes (15): 1. Install Poetry (Python), 2. Install uv (Python), 3. Install Node.js & npm, 4. Install Ollama & llama3.2 model, 5. Install Project Dependencies, Backup, Configuration, Database Backup & Restore (+7 more)

### Community 212 - "README.md"
Cohesion: 0.26
Nodes (4): AI CV Matcher, Quickstart, Requirements, aiEnrich3

### Community 213 - "ModalityExtractor"
Cohesion: 0.20
Nodes (9): ExtractionResult, ModalityType, Enum, ModalityExtractor, extractor(), fixture, parametrize, test_extract_modality() (+1 more)

### Community 214 - "process_batch"
Cohesion: 0.22
Nodes (12): get_gpu_cleanup(), process_batch(), Any, Exception, T, test_get_gpu_cleanup_default_true(), patch, test_cleanup_gpu() (+4 more)

### Community 215 - "SalaryHistoryService"
Cohesion: 0.26
Nodes (6): get_company_history(), get_job_history(), get_service(), get, test_get_service_returns_service(), SalaryHistoryService

### Community 216 - "TestScraplingService"
Cohesion: 0.15
Nodes (3): _make_service(), fixture, TestScraplingService

### Community 217 - "jobs_applied_test.py"
Cohesion: 0.21
Nodes (13): parametrize, patch, Test that various SQL injection attempts are blocked, Test that missing company parameter returns validation error, Test that empty company parameter is rejected, test_get_applied_jobs_by_company(), test_get_applied_jobs_by_company_empty_string(), test_get_applied_jobs_by_company_missing_parameter() (+5 more)

### Community 218 - "_detect_captcha"
Cohesion: 0.38
Nodes (3): _detect_captcha(), fixture, TestCaptchaHandler

### Community 219 - "JobWriteRepository"
Cohesion: 0.23
Nodes (6): JobWriteRepository, patch, Verify that update_jobs_by_filter returns the result of executeAndCommit     ins, test_update_jobs_by_filter_uses_return_value(), patch, test_update_job()

### Community 220 - "generate_config_view_sql"
Cohesion: 0.19
Nodes (13): Test generating SQL for dropping config view, Test generating SQL with all supported filters including sql_filter, status, etc, Test generating SQL with boolean filters at the top level, Test generating SQL for config view, Test generating SQL with duplicated filter, test_drop_config_view_sql(), test_generate_config_view_sql(), test_generate_config_view_sql_with_all_filters() (+5 more)

### Community 221 - "AI Job Search Web UI"
Cohesion: 0.14
Nodes (13): AI Job Search Web UI, Backend Discovery, Environment Variables (`.env` & `.env.secrets`), Features, Installation, Prerequisites, Project Structure, Running Development Server (+5 more)

### Community 223 - "Plan D: GGUF Quantized Models via llama-cpp-python"
Cohesion: 0.14
Nodes (13): `apps/aiEnrichNew/pyproject.toml`, `apps/aiEnrichNew/src/aiEnrichNew/llm_client.py`, `apps/aiEnrichNew/src/aiEnrichNew/llm_utils.py`, Architecture, Files to Modify, Goal, Implementation Order, Installation (+5 more)

### Community 224 - "aiEnrichSkill"
Cohesion: 0.15
Nodes (12): aiEnrichSkill, Architecture, Backends, Configuration, Dependencies, General, HuggingFace Backend, Linux / Mac (+4 more)

### Community 225 - "api/salary.py"
Cohesion: 0.14
Nodes (17): calculate_salary(), BaseModel, post, SalaryCalculationRequest, SalaryService, parametrize, patch, test_calculate_salary() (+9 more)

### Community 226 - "company_synonym_service_test.py"
Cohesion: 0.17
Nodes (5): mock_repo(), fixture, parametrize, sut(), test_create_group_invalid()

### Community 227 - "observability_test.py"
Cohesion: 0.45
Nodes (10): configure_logging(), get_logger(), _reset(), test_configure_logging_idempotent(), test_get_logger_returns_bound_logger(), test_get_logger_with_name(), test_log_rotation(), test_log_writes_to_jsonl_file() (+2 more)

### Community 228 - "JobsService"
Cohesion: 0.14
Nodes (12): get_service(), get_job(), get_service(), get_watcher_stats(), list_jobs(), get, JobsService, Any (+4 more)

### Community 229 - "terminalUtil.py"
Cohesion: 0.19
Nodes (10): getSeconds(), timeUnit: 30s|8m|2h|1h 30m, consoleTimer(), consoleTimerDocker(), _consoleTimerLocal(), Spinner, patch, TestTerminalFunctions (+2 more)

### Community 230 - "web/package.json"
Cohesion: 0.33
Nodes (5): name, private, type, version, queryClient

### Community 231 - "SkillsManager.tsx"
Cohesion: 0.16
Nodes (16): downloadFile(), Skill, EditSkillModalProps, SkillTag(), SkillTagProps, createWrapper(), mockClient, mockSkills (+8 more)

### Community 232 - "Tools"
Cohesion: 0.17
Nodes (11): `bulk_fetch` -- Browser fetch (multiple URLs), `bulk_get` -- HTTP request (multiple URLs), `bulk_stealthy_fetch` -- Stealth browser fetch (multiple URLs), Content extraction tips, `fetch` -- Browser fetch (single URL), `get` -- HTTP request (single URL), Scrapling MCP Server, Setup (+3 more)

### Community 233 - "query_ollama"
Cohesion: 0.35
Nodes (10): _get_num_predict(), ping_ollama(), query_ollama(), _strip_provider_prefix(), parametrize, patch, test_ping_ollama(), test_query_ollama_failure_all_retries() (+2 more)

### Community 236 - "MockBaseExecutor"
Cohesion: 0.24
Nodes (5): MockBaseExecutor, mocks(), fixture, run_mocks(), TestExecutor

### Community 237 - "print_failed_info_table"
Cohesion: 0.29
Nodes (10): _collect_failed_info(), print_failed_info_table(), mock_pm(), fixture, parametrize, test_collect_failed_info(), test_collect_failed_info_with_error_details(), test_collect_failed_info_with_multiple_keywords() (+2 more)

### Community 238 - "Version Bumper Instructions"
Cohesion: 0.17
Nodes (11): 1. Detect Modified Apps, 2. Ask User for Bump Type, 3. Update the Version File, 4. Sync commonlib Dependency Version, 5. Version Reference Table, 6. Verify, aiFormFiller extension (extension/manifest.json):, npm apps (web, e2e — package.json): (+3 more)

### Community 239 - "TODO"
Cohesion: 0.17
Nodes (11): apps/aiEnrich, apps/aiEnrich3, apps/aiEnrichNew, apps/backend, apps/commonlib, apps/scrapper, apps/web, cross module tasks (+3 more)

### Community 240 - "run_e2e_tests.py"
Cohesion: 0.26
Nodes (11): cleanup_all_e2e_databases(), get_e2e_connection(), get_free_port(), Main orchestration function., Finds a free port on localhost., Creates a fresh database and runs DDL., Finds and drops all test databases matching jobs_e2e_* pattern., Waits for backend health check to be green. (+3 more)

### Community 241 - "Components"
Cohesion: 0.18
Nodes (10): Checkpoint System, Comparison with Scrapy, Components, Crawler Engine, Data Flow, Output, Scheduler, Session Manager (+2 more)

### Community 242 - "SkillsManagerApi.ts"
Cohesion: 0.15
Nodes (9): skillsApi, mocks, mocks, mocks, mocks, mocks, mocks, mocks (+1 more)

### Community 245 - "api/main.py"
Cohesion: 0.33
Nodes (4): get_timezone(), health_check(), get, Returns the server's UTC offset in minutes.     Example: UTC+1 returns 60.

### Community 246 - "getSrcPath"
Cohesion: 0.36
Nodes (6): createFolder(), getSrcPath(), listFiles(), Path, patch, TestFileSystemUtil

### Community 247 - "Company Salary History Scanner"
Cohesion: 0.18
Nodes (10): 1. New job backfill (`_fetch_jobs`), 2. Updated job detection (`_fetch_updated`), Company name matching, Company Salary History Scanner, Configuration, Data model, Duplicate prevention, How it works (+2 more)

### Community 248 - "TestInfojobsService"
Cohesion: 0.24
Nodes (3): fixture, parametrize, TestInfojobsService

### Community 249 - "backendDiscovery.ts"
Cohesion: 0.31
Nodes (7): cidrToHosts(), detectLocalSubnets(), discoverBackendUrl(), probeBackend(), scanPort(), createMockSocket(), socketFactory()

### Community 251 - "graphify-inject-edges.py"
Cohesion: 0.38
Nodes (10): Graph, _belongs_to_module(), find_representative_node(), inject_edges(), load_graph(), main(), Path, Check if a node belongs to a module by repo attribute or ID prefix. (+2 more)

### Community 252 - "commonlib"
Cohesion: 0.18
Nodes (11): ai-job-search, aiCvMatcher, aiEnrich, aiEnrich3, aiEnrichNew, aiEnrichSkill, aiFormFiller, api (+3 more)

### Community 253 - "Statistics.tsx"
Cohesion: 0.22
Nodes (10): Statistics(), testQueryClient, testQueryClient, testQueryClient, getColorForSource(), renderDateChart(), renderFilterConfigChart(), renderHistoryChart() (+2 more)

### Community 254 - "generate_html"
Cohesion: 0.33
Nodes (10): community_colors(), generate_html(), hsl_to_hex(), _js_safe(), main(), module_order(), Path, Escape </script> sequences so embedded JSON cannot break out of the script tag. (+2 more)

### Community 255 - "Fetching dynamic websites"
Cohesion: 0.20
Nodes (10): 1. Vanilla Playwright, 2. Real Chrome, 3. CDP Connection, Async Session Usage, Basic Usage, Fetching dynamic websites, Full list of arguments, Session Benefits (+2 more)

### Community 256 - "Examples"
Cohesion: 0.20
Nodes (10): Browser Automation, Domain Blocking, Downloading Files, Examples, General example, Network Control, Proxy Rotation, Resource Control (+2 more)

### Community 257 - "Proxy management and handling Blocks"
Cohesion: 0.20
Nodes (9): Blocked Request Handling, Custom Block Detection, Custom Rotation Strategies, Customizing Retries, Per-Request Proxy Override, Proxy management and handling Blocks, ProxyRotator, Random Rotation (+1 more)

### Community 258 - "AI Job Enrichment"
Cohesion: 0.20
Nodes (10): 1. Install `uv` Package Manager, 2. Install Project Dependencies, AI Job Enrichment, Automated Loop, Configuration, Installation, LLM Model Selection, Manual Run (Dev) (+2 more)

### Community 259 - "backend/repositories/__init__.py"
Cohesion: 0.26
Nodes (3): JobReadRepository, patch, test_list_jobs()

### Community 260 - "App.tsx"
Cohesion: 0.24
Nodes (7): App(), CompanySynonymsManager, Settings, SkillsManager, Statistics, Viewer, LoadingFallback()

### Community 261 - "extract_filter_params"
Cohesion: 0.15
Nodes (12): build_where_params(), extract_filter_params(), Any, Filter parsing utilities for consistent filter extraction across the backend., Extract all standard filter parameters from a filters dictionary.      Args:, Build WHERE clause clauses and parameters from filter parameters.      This is, Tests for filter_parser utility module., Test extracting all filter parameters. (+4 more)

### Community 262 - "validationUtils.ts"
Cohesion: 0.42
Nodes (6): getFilesRecursively(), getTestFiles(), extractImports(), ImportViolation, checkImportViolation(), validateFeatureFolder()

### Community 263 - "SettingsApi.ts"
Cohesion: 0.28
Nodes (8): apiClient, useDefaultComment(), useEnvSettings(), ScrapperStateUpdateDto, settingsApi, SettingsEnvUpdateDto, SalaryActions(), SalaryActionsProps

### Community 264 - "get_pipeline"
Cohesion: 0.44
Nodes (6): get_pipeline(), patch, test_get_pipeline_cuda_available(), test_get_pipeline_initialization(), test_get_pipeline_pad_token_set(), test_get_pipeline_singleton()

### Community 265 - "OpenRouterProvider"
Cohesion: 0.36
Nodes (3): OpenRouterProvider, patch, TestOpenRouterProvider

### Community 266 - "normalize_company_name"
Cohesion: 0.36
Nodes (7): normalize_company_name(), test_collapses_spaces(), test_empty_name(), test_lowercases_and_trims(), test_removes_parentheticals(), test_removes_special_chars(), test_removes_suffixes()

### Community 267 - "systemUtil.py"
Cohesion: 0.31
Nodes (6): isDocker(), isLinuxOS(), isMacOS(), isWindowsOS(), patch, TestSystemUtil

### Community 268 - "Common Library"
Cohesion: 0.22
Nodes (8): Common Library, Contents, Installation, MySQL connection, Resolution order, Supported host formats, Testing, Usage

### Community 269 - "Cron — Background Scheduler"
Cohesion: 0.22
Nodes (8): Configuration, Cron — Background Scheduler, Docker, How it works, Registered jobs, Running, Tech Stack, Testing

### Community 270 - "GlassdoorGmailService"
Cohesion: 0.25
Nodes (4): GlassdoorGmailService, Wait for Glassdoor/Indeed OTP verification code with predefined sender, Glassdoor-specific Gmail service with predefined sender for Indeed OTP login, TestGlassdoorGmailService

### Community 271 - "driverUtil.py"
Cohesion: 0.11
Nodes (10): TestDriverUtil, TestStealthScripts, Benefits, Configuration, How It Works, Option 1: Environment Variable (Recommended), Option 2: Programmatic, Overview (+2 more)

### Community 272 - "JobListParams"
Cohesion: 0.12
Nodes (19): persistenceApi, persistenceDefaults, HistoryInputProps, useConfirmationModal(), filterConfigsApi, FilterConfiguration, FilterConfigurationCreate, FilterConfigurationUpdate (+11 more)

### Community 273 - "SkillsManager.test.tsx"
Cohesion: 0.42
Nodes (7): initialSkills, MockEditSkillModal(), mockRemoveSkill, mockReorderSkills, mockSaveSkill, mockUpdateSkill, setupLearnListMock()

### Community 274 - "opencode.json"
Cohesion: 0.22
Nodes (8): formatter, ruff, uv, instructions, disabled, $schema, disabled, .opencode/rules/*.md

### Community 275 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 276 - "Quick Start Commands for Docker Development"
Cohesion: 0.20
Nodes (10): All Services, Core Services (Backend + Web + Viewer), Development Tips, Quick Start Commands for Docker Development, Related Documentation, Service URLs, Troubleshooting, Web container: stale `node_modules` (+2 more)

### Community 277 - "HTTP requests"
Cohesion: 0.40
Nodes (4): HTTP requests, Session Benefits, Session Management, When to Use

### Community 278 - "Examples"
Cohesion: 0.25
Nodes (8): Basic HTTP Request, Downloading Files, Examples, Form Submission, Navigation Menu, Pagination Handling, Product Scraping, Table Extraction

### Community 279 - "StealthyFetcher"
Cohesion: 0.25
Nodes (8): Async Session Usage, Basic Usage, Full list of arguments, Session Benefits, Session Management, StealthyFetcher, What does it do?, When to Use

### Community 280 - "ExtractionPipeline"
Cohesion: 0.32
Nodes (6): ExtractionPipeline, mock_pipeline_deps(), fixture, parametrize, test_pipeline_init(), test_pipeline_process_job()

### Community 281 - "parse_job_enrichment_result"
Cohesion: 0.32
Nodes (6): parse_job_enrichment_result(), Any, Pure function to parse and validate job enrichment LLM output.     Returns None, parametrize, patch, test_parse_job_enrichment_result()

### Community 282 - "run"
Cohesion: 0.40
Nodes (8): get_enabled(), run(), test_get_enabled_default_true(), patch, test_run_disabled(), test_run_enriched_some_skills(), test_run_no_skills_waits(), test_run_persists_after_each_enrich_cycle()

### Community 283 - "LocalHFProvider"
Cohesion: 0.43
Nodes (3): LocalHFProvider, patch, TestLocalHFProvider

### Community 284 - "filter_configurations_test.py"
Cohesion: 0.43
Nodes (7): patch, test_create_configuration(), test_create_duplicate_name(), test_delete_configuration(), test_get_all_configurations(), test_get_configuration_by_id(), test_update_configuration()

### Community 285 - "skills_test.py"
Cohesion: 0.43
Nodes (7): patch, test_create_skill(), test_delete_skill(), test_delete_skill_not_found(), test_list_skills(), test_update_skill(), test_update_skill_not_found()

### Community 286 - "BaseNavigator"
Cohesion: 0.16
Nodes (3): BaseNavigator, ABC, Fast forwards to the start_page by clicking next page button.         Returns t

### Community 287 - "E2E Implementer Instructions"
Cohesion: 0.29
Nodes (6): 1. Location & Structure, 2. Naming Conventions, 3. Best Practices, 4. Architecture Verification, E2E Implementer Instructions, Usage

### Community 288 - "HTTP Methods"
Cohesion: 0.29
Nodes (7): Basic Usage, DELETE, GET, HTTP Methods, POST, PUT, Shared arguments

### Community 289 - "Getting started"
Cohesion: 0.29
Nodes (6): Exporting Data, Filtering Domains, Following Links, Getting started, Running the Spider, Your First Spider

### Community 290 - "Test Implementer Instructions"
Cohesion: 0.29
Nodes (6): 1. Test Location & Structure, 2. Naming Conventions, 3. Coding Best Practices, 4. Architecture Verification, Test Implementer Instructions, Usage

### Community 291 - "aiEnrichNew"
Cohesion: 0.29
Nodes (7): aiEnrichNew, Configuration, Linux / Mac, Manual, Prerequisites, Usage, Windows

### Community 292 - "statistics.py"
Cohesion: 0.48
Nodes (6): get_filter_config_stats(), get_history_stats(), get_sources_by_date(), get_sources_by_hour(), get_sources_by_weekday(), get

### Community 294 - "statistics_test.py"
Cohesion: 0.48
Nodes (6): patch, test_get_filter_config_stats(), test_get_history_stats(), test_get_history_stats_exclude_old_jobs(), test_get_sources_by_date(), test_get_sources_by_hour()

### Community 296 - "react"
Cohesion: 0.31
Nodes (7): react, createHeadingRenderer(), getText(), ReactMarkdownCustom(), ReactMarkdownCustomProps, slugify(), react

### Community 297 - "E2E Implementer Instructions"
Cohesion: 0.29
Nodes (6): 1. Location & Structure, 2. Naming Conventions, 3. Best Practices, 4. Architecture Verification, E2E Implementer Instructions, Usage

### Community 298 - "Test Implementer Instructions"
Cohesion: 0.29
Nodes (6): 1. Test Location & Structure, 2. Naming Conventions, 3. Coding Best Practices, 4. Architecture Verification, Test Implementer Instructions, Usage

### Community 299 - "E2E Implementer Instructions"
Cohesion: 0.29
Nodes (6): 1. Location & Structure, 2. Naming Conventions, 3. Best Practices, 4. Architecture Verification, E2E Implementer Instructions, Usage

### Community 300 - "Test Implementer Instructions"
Cohesion: 0.29
Nodes (6): 1. Test Location & Structure, 2. Naming Conventions, 3. Coding Best Practices, 4. Architecture Verification, Test Implementer Instructions, Usage

### Community 301 - "QuotesSpider"
Cohesion: 0.33
Nodes (4): QuotesSpider, Example 4: Python - Spider (auto-crawling framework)  Scrapes ALL pages of quo, Response, Spider

### Community 302 - "Scrapling Examples"
Cohesion: 0.33
Nodes (5): Escalation Guide, Examples, Quick Start, Running, Scrapling Examples

### Community 303 - "Fetchers basics"
Cohesion: 0.25
Nodes (6): Fetchers basics, Fetchers Overview, Introduction, Parser configuration in all fetchers, Response Object, Set parser config per request

### Community 306 - "AI Enrichment — Speed Improvement Plans"
Cohesion: 0.33
Nodes (5): AI Enrichment — Speed Improvement Plans, Context, Modules Overview, Plans Index, Recommended Order

### Community 307 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 308 - "AI Job Search Default Development Guide"
Cohesion: 0.33
Nodes (6): Agent Skills, AI Job Search Default Development Guide, Development with VS Code, Related Documentation, Skill Builder, Testing

### Community 309 - "Examples"
Cohesion: 0.40
Nodes (5): Browser Automation, Cloudflare and stealth options, Examples, Real-world example (Amazon), Wait Conditions

### Community 310 - "enrichment_service.py"
Cohesion: 0.18
Nodes (14): get_batch_size(), get_enrich_limit(), get_timeout(), build_skill_prompt_messages(), parse_skill_enrichment_result(), parametrize, patch, test_build_skill_prompt_messages() (+6 more)

### Community 312 - "content.js"
Cohesion: 0.60
Nodes (3): cssSelector(), detectAllQuestions(), detectQuestion()

### Community 313 - "BaseService"
Cohesion: 0.11
Nodes (6): CustomConverter, BaseService, ABC, Extract job ID from URL, Hook for post-processing markdown. Defaults to identity., MarkdownConverter

### Community 315 - "TestGlassdoorNavigator"
Cohesion: 0.17
Nodes (3): fixture, patch, TestGlassdoorNavigator

### Community 316 - "SkillsList.test.tsx"
Cohesion: 0.40
Nodes (4): mockIsInLearnList, mockLearnList, mockSaveSkill, mockToggleSkill

### Community 317 - "filter_deps"
Cohesion: 0.70
Nodes (4): filter_deps(), is_external_dep(), main(), Path

### Community 318 - "generate_labels"
Cohesion: 0.70
Nodes (4): generate_labels(), main(), Path, _skip_label()

### Community 319 - "mock_sleep"
Cohesion: 0.50
Nodes (3): mock_sleep(), fixture, Mock sleep and wait functions globally to speed up test execution.     Reduces

### Community 320 - "PageHeader.tsx"
Cohesion: 0.19
Nodes (4): DropdownProps, HeaderMenu(), PageHeader(), PageHeaderProps

### Community 321 - "queryTestUtils.tsx"
Cohesion: 0.67
Nodes (3): createHookTestWrapper(), createTestQueryClient(), wrapper

### Community 322 - ".opencode/opencode.json"
Cohesion: 0.50
Nodes (3): plugin, $schema, .opencode/plugins/graphify.js

### Community 323 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 324 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 325 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 326 - "Contribute"
Cohesion: 0.50
Nodes (4): Contribute, Development guide-lines, Related Documentation, Tests & coverage

### Community 327 - "graphify.sh"
Cohesion: 0.83
Nodes (3): clean_graph(), extract_module(), graphify.sh script

### Community 332 - "SalaryCalculator.test.tsx"
Cohesion: 0.24
Nodes (8): { mockPost }, salaryApi, SalaryCalculationRequest, SalaryCalculationResponse, mockJob, mockSalaryResponse(), skipInitialCalculation(), waitForDebounce()

### Community 357 - "TestGlassdoorAuthenticator"
Cohesion: 0.23
Nodes (4): fixture, object, patch, TestGlassdoorAuthenticator

### Community 359 - "build_prometheus_metrics"
Cohesion: 0.31
Nodes (8): get_prometheus_metrics(), get, build_log_metrics(), build_prometheus_metrics(), test_build_metrics_with_module_data(), test_empty_snapshot(), test_missing_optional_fields(), test_multiple_modules()

### Community 361 - "CompanySynonymsManager.tsx"
Cohesion: 0.36
Nodes (7): companySynonymsApi, SynonymGroup, CompanySynonymsManager(), CompanySynonymsTable(), CompanySynonymsTableProps, EditSynonymGroupModal(), useCompanySynonyms()

### Community 666 - "ChartCard.mocks.ts"
Cohesion: 0.27
Nodes (7): defaultProps, renderWithQueryClient(), mockGetFilterConfigStats, mockGetHistoryStats, mockGetSourcesByDate, mockGetSourcesByHour, mockGetSourcesByWeekday

### Community 667 - "JobDeleteService"
Cohesion: 0.31
Nodes (3): JobDeleteService, Any, Any

### Community 668 - "TestGlassdoorService"
Cohesion: 0.24
Nodes (3): fixture, parametrize, TestGlassdoorService

### Community 669 - "TestJobBooleanKeys"
Cohesion: 0.22
Nodes (6): parametrize, Tests for JOB_BOOLEAN_KEYS backward compatibility alias., Test that JOB_BOOLEAN_KEYS is defined (backward compatibility)., Test that JOB_BOOLEAN_KEYS is the same as BOOLEAN_FILTER_KEYS., Test that specific keys are present in JOB_BOOLEAN_KEYS., TestJobBooleanKeys

### Community 671 - "StatisticsFilters.tsx"
Cohesion: 0.22
Nodes (4): StatisticsControlsProps, StatisticsFiltersProps, TIME_RANGE_OPTIONS, defaultProps

### Community 672 - "get_skill_context"
Cohesion: 0.36
Nodes (4): _fetch_skill_context_safe(), get_skill_context(), Fetches context for a skill by looking at required and optional technologies, TestSkillContext

### Community 673 - "MessageContainer.tsx"
Cohesion: 0.32
Nodes (3): MessageContainerProps, Messages(), MessagesProps

### Community 674 - "CompanySalaryHistoryJob"
Cohesion: 0.48
Nodes (5): CompanySalaryHistoryJob, patch, test_job_has_name_and_cadency(), test_job_run_no_prior_state(), test_job_run_with_prior_state()

### Community 675 - "TestBooleanFilterKeys"
Cohesion: 0.33
Nodes (4): Tests for BOOLEAN_FILTER_KEYS constant., Test that BOOLEAN_FILTER_KEYS is defined., Test that all boolean keys are valid field names., TestBooleanFilterKeys

### Community 676 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 677 - "common/utils/sqlEditorUtils.ts"
Cohesion: 0.47
Nodes (4): SQL_FUNCTIONS, Suggestion, Token, tokenizeSql()

### Community 678 - "CustomTooltip.tsx"
Cohesion: 0.40
Nodes (4): CustomTooltip(), CustomTooltipProps, formatDate(), mockPayload

### Community 679 - "chartUtils.ts"
Cohesion: 0.53
Nodes (4): COLORS_PALETTE, getDateRange(), getSeriesKeys(), pivotData()

## Knowledge Gaps
- **804 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `aiCvMatcher`, `aiEnrich3`, `ExtractionResult` (+799 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **348 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MysqlUtil` connect `MysqlUtil` to `IndeedScraplingExecutor`, `backend/repositories/__init__.py`, `terminalColor.py`, `BaseExecutor`, `CompanySynonymRepository`, `JobSnapshotService`, `yellow`, `AiEnrichRepository`, `WatcherService`, `run`, `JobsRepository`, `TestGlassdoorService`, `ai_helpers.py`, `get_skill_context`, `JobSnapshotRepository`, `connection_manager.py`, `observability.py`, `environmentUtil.py`, `SkillsRepository`, `TecnoempleoExecutor`, `enrichment_service.py`, `TestLinkedinService`, `aiEnrich/dataExtractor.py`, `JobRepository`, `BaseService`, `GlassdoorExecutor`, `JobDeleteRepository`, `LinkedinExecutor`, `TestIndeedService`, `MetricsCollector`, `ScrapperStateRepository`, `IndeedService`, `CompanySalaryHistoryScanner`, `TransactionManager`, `TestBaseService`, `JobWriteRepository`, `CompanySynonymService`, `QueryExecutor`, `aiEnrich3/dataExtractor.py`, `TestInfojobsService`, `persistence_manager.py`, `FilterConfigurationsRepository`, `InfojobsExecutor`, `enrichment_service_test.py`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `LinkedinNavigator` connect `LinkedinNavigator` to `terminalColor.py`, `yellow`, `TestLinkedinNavigator`, `BaseNavigator`, `LinkedinExecutor`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `SeleniumService` connect `SeleniumService` to `IndeedScraplingExecutor`, `retry`, `terminalColor.py`, `LinkedinNavigator`, `BaseExecutor`, `persistence_manager.py`, `IndeedService`, `seleniumSocketConnRetry`, `DriverUtil`, `TecnoempleoExecutor`, `TestBaseNavigator`, `InfojobsExecutor`, `TestGlassdoorNavigator`, `GlassdoorExecutor`, `BaseNavigator`, `LinkedinExecutor`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 62 inferred relationships involving `MysqlUtil` (e.g. with `FastCVMatcher` and `.process_db_jobs()`) actually correct?**
  _`MysqlUtil` has 62 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `yellow()` (e.g. with `.check_results()` and `.finalize_scrapper()`) actually correct?**
  _`yellow()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `SeleniumService` (e.g. with `ScrapperScheduler` and `TestGlassdoorExecutor`) actually correct?**
  _`SeleniumService` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `PersistenceManager` (e.g. with `ScrapperScheduler` and `ScrapperStateCalculator`) actually correct?**
  _`PersistenceManager` has 20 INFERRED edges - model-reasoned connections that need verification._