from commonlib.prometheus_exporter import build_prometheus_metrics


def test_empty_snapshot():
    snapshot = {"modules": {}, "timestamp": "2024-01-01T00:00:00", "global": {"total_jobs": 0, "total_errors": 0}}
    result = build_prometheus_metrics(snapshot)
    assert isinstance(result, bytes)
    assert result == b""


def test_build_metrics_with_module_data():
    snapshot = {
        "modules": {
            "aiEnrichNew": {
                "jobs_processed": 42, "jobs_succeeded": 40, "jobs_failed": 2,
                "total_duration": 840.0, "pending_jobs": 5,
                "cache_hits": 10, "cache_misses": 3,
                "p50": 18.5, "p90": 35.2, "p99": 60.1, "avg": 20.0,
                "last_processed_at": "2024-06-15T10:30:00",
            }
        },
        "global": {"total_jobs": 42, "total_errors": 2},
    }
    result = build_prometheus_metrics(snapshot)
    output = result.decode()

    assert 'ai_enrich_jobs_processed_total{module="aiEnrichNew"} 42.0' in output
    assert 'ai_enrich_jobs_succeeded_total{module="aiEnrichNew"} 40.0' in output
    assert 'ai_enrich_jobs_failed_total{module="aiEnrichNew"} 2.0' in output
    assert 'ai_enrich_duration_seconds_total{module="aiEnrichNew"} 840.0' in output
    assert 'ai_enrich_pending_jobs{module="aiEnrichNew"} 5.0' in output
    assert 'ai_enrich_cache_hits_total{module="aiEnrichNew"} 10.0' in output
    assert 'ai_enrich_cache_misses_total{module="aiEnrichNew"} 3.0' in output
    assert 'ai_enrich_duration_seconds_p50{module="aiEnrichNew"} 18.5' in output
    assert 'ai_enrich_duration_seconds_p90{module="aiEnrichNew"} 35.2' in output
    assert 'ai_enrich_duration_seconds_p99{module="aiEnrichNew"} 60.1' in output
    assert 'ai_enrich_duration_seconds_avg{module="aiEnrichNew"} 20.0' in output
    assert 'ai_enrich_last_processed_timestamp{module="aiEnrichNew"}' in output

    assert "ai_enrich_total_jobs 42.0" in output
    assert "ai_enrich_total_errors 2.0" in output
    assert "ai_enrich_modules_count 1.0" in output


def test_multiple_modules():
    snapshot = {
        "modules": {
            "mod_a": {
                "jobs_processed": 10, "jobs_succeeded": 8, "jobs_failed": 2,
                "total_duration": 100.0, "pending_jobs": 0,
                "cache_hits": 5, "cache_misses": 1,
                "p50": 10.0, "p90": 15.0, "p99": 20.0, "avg": 12.0,
            },
            "mod_b": {
                "jobs_processed": 5, "jobs_succeeded": 5, "jobs_failed": 0,
                "total_duration": 25.0, "pending_jobs": 2,
                "cache_hits": 0, "cache_misses": 0,
                "p50": 5.0, "p90": 7.0, "p99": 9.0, "avg": 5.0,
            },
        },
        "global": {"total_jobs": 15, "total_errors": 2},
    }
    result = build_prometheus_metrics(snapshot)
    output = result.decode()

    assert 'ai_enrich_jobs_processed_total{module="mod_a"} 10.0' in output
    assert 'ai_enrich_jobs_processed_total{module="mod_b"} 5.0' in output
    assert 'ai_enrich_pending_jobs{module="mod_b"} 2.0' in output
    assert "ai_enrich_modules_count 2.0" in output


def test_missing_optional_fields():
    snapshot = {
        "modules": {
            "minimal": {
                "jobs_processed": 1, "jobs_succeeded": 1, "jobs_failed": 0,
                "total_duration": 5.0, "pending_jobs": 0,
                "cache_hits": 0, "cache_misses": 0,
            }
        },
        "global": {"total_jobs": 1, "total_errors": 0},
    }
    result = build_prometheus_metrics(snapshot)
    output = result.decode()

    assert 'ai_enrich_jobs_processed_total{module="minimal"} 1.0' in output
    assert 'ai_enrich_duration_seconds_p50{module=' not in output
    assert 'ai_enrich_last_processed_timestamp{module=' not in output
