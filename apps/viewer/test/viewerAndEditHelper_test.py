import sys
import os
import datetime
from types import SimpleNamespace

import pandas as pd

# Ensure the local `viewer` package (apps/viewer/viewer) is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import viewer.viewConstants as vc
import viewer.viewAndEditHelper as vah


def test_view_constants_pages():
    # basic sanity checks for constants
    assert vc.PAGE_VIEW_IDX in vc.PAGES
    assert vc.PAGES[vc.PAGE_VIEW_IDX] == vc.PAGE_VIEW


def test_remove_regex_chars():
    from viewer.viewAndEdit import removeRegexChars

    txt = "abc(1) [2]"
    out = removeRegexChars(txt)
    # ensure parentheses and square brackets are escaped for regex
    assert "\\(" in out and "\\)" in out
    assert "\\[" in out and "\\]" in out


def test_format_date():
    from viewer.viewAndEdit import formatDate

    d = datetime.date(2020, 1, 5)
    assert formatDate(d) == '05-01-20'


def test_get_table_cols_config_and_preselect(monkeypatch):
    # Prepare a dummy getColumnTranslated to keep labels predictable
    monkeypatch.setattr(vah, 'getColumnTranslated', lambda c: c)

    # Replace streamlit column classes with simple sentinels to avoid
    # requiring Streamlit internals during tests
    monkeypatch.setattr(vah.st, 'column_config', SimpleNamespace(Column=lambda **kw: f"COL({kw.get('label')})"))
    monkeypatch.setattr(vah, 'CheckboxColumn', lambda **kw: 'CHECKBOX')

    fields = ['id', 'title', 'company', 'created']
    visible = {'title', 'company'}
    cfg = vah.getTableColsConfig(fields, visible, selector=True)

    # Expect selector and '0' keys, and numeric keys for other columns
    assert 'Sel' in cfg
    assert '0' in cfg
    # numeric keys (2..n) exist
    assert any(isinstance(k, int) for k in cfg.keys() if k != 'Sel' and k != '0')

    # test preSelectRows behaviour
    df = pd.DataFrame([{'a': 1}, {'a': 2}])
    # monkeypatch getState to simulate preselected row index 1
    monkeypatch.setattr(vah, 'getState', lambda key, default=None: ['1'] if key == vah.FF_KEY_PRESELECTED_ROWS else default)
    vah.preSelectRows(df, vah.FF_KEY_PRESELECTED_ROWS)
    assert 'Sel' in df.columns
    # the second row (index 1) should be True
    assert df['Sel'].iloc[1] == True


def test_remove_filters_in_not_filters(monkeypatch):
    # prepare state values
    monkeypatch.setattr(vah, 'getStateBoolValue', lambda a, b: True)
    monkeypatch.setattr(vah, 'getState', lambda key, default=None: [1, 2] if key == vah.FF_KEY_BOOL_FIELDS else ([2, 3] if key == vah.FF_KEY_BOOL_NOT_FIELDS else default))
    res = vah.removeFiltersInNotFilters()
    assert res == [3]


def test_select_next(monkeypatch):
    # Test selectNext when condition is met
    monkeypatch.setattr(vah, 'getState', lambda key, default=None: (['0'] if key == vah.FF_KEY_PRESELECTED_ROWS else None))
    monkeypatch.setattr(vah, 'setQueryParamOrState', lambda p, pv, sv=None: None)  # mock
    vah.selectNext(max=5)
    # No exception should be raised

    # Test selectNext when max boundary exceeded
    monkeypatch.setattr(vah, 'getState', lambda key, default=None: (['4'] if key == vah.FF_KEY_PRESELECTED_ROWS else None))
    vah.selectNext(max=5)
    # Should not advance beyond max


def test_select_previous(monkeypatch):
    # Test selectPrevious when condition is met
    monkeypatch.setattr(vah, 'getState', lambda key, default=None: (['1'] if key == vah.FF_KEY_PRESELECTED_ROWS else None))
    monkeypatch.setattr(vah, 'setQueryParamOrState', lambda p, pv, sv=None: None)  # mock
    vah.selectPrevious()
    # No exception should be raised

    # Test selectPrevious at boundary (row 0)
    monkeypatch.setattr(vah, 'getState', lambda key, default=None: (['0'] if key == vah.FF_KEY_PRESELECTED_ROWS else None))
    vah.selectPrevious()
    # Should not go below 0


def test_count_ids():
    from viewer.cleaner import countIds
    
    df = pd.DataFrame({'Ids': ['1,2,3']})
    # Test when selection=False (count all)
    count = countIds(df, False)
    assert count == 3
    
    df_selected = pd.DataFrame({'Ids': ['1,2']})
    # Test when selection=True
    count_sel = countIds(df_selected, True)
    assert count_sel == 2
    
    # Test with single ID
    df_single = pd.DataFrame({'Ids': ['5']})
    assert countIds(df_single) == 1
    
    # Test with empty DataFrame
    df_empty = pd.DataFrame({'Ids': []})
    assert countIds(df_empty) == 0
