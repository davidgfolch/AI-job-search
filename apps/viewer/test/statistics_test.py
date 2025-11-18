from unittest.mock import MagicMock, patch
import pandas as pd

class TestCreatedByDateStats:
    @patch('viewer.statistics.createdByDate.st')
    @patch('viewer.statistics.createdByDate.px')
    @patch('viewer.statistics.createdByDate.pd')
    @patch('viewer.statistics.createdByDate.mysqlCachedConnection')
    def test_created_by_date_run(self, mock_conn, mock_pd, mock_px, mock_st):
        from viewer.statistics.createdByDate import run
        
        mock_df = pd.DataFrame({
            'dateCreated': ['2025-01-01', '2025-01-02'],
            'total': [5, 3], 'source': ['LinkedIn', 'Indeed']
        })
        mock_pd.read_sql.return_value = mock_df
        mock_pd.to_datetime.return_value = pd.to_datetime(mock_df['dateCreated'])
        mock_fig = MagicMock()
        mock_px.bar.return_value = mock_fig
        
        run()
        
        mock_pd.read_sql.assert_called_once()
        mock_px.bar.assert_called_once()
        mock_st.plotly_chart.assert_called_once_with(mock_fig)

class TestCreatedByHoursStats:
    @patch('viewer.statistics.createdByHours.st')
    @patch('viewer.statistics.createdByHours.px')
    @patch('viewer.statistics.createdByHours.pd')
    @patch('viewer.statistics.createdByHours.mysqlCachedConnection')
    def test_created_by_hours_run(self, mock_conn, mock_pd, mock_px, mock_st):
        from viewer.statistics.createdByHours import run
        
        mock_df = pd.DataFrame({'hour': [9, 10, 11], 'total': [2, 5, 3]})
        mock_pd.read_sql.return_value = mock_df
        mock_fig = MagicMock()
        mock_px.bar.return_value = mock_fig
        
        run()
        
        mock_pd.read_sql.assert_called_once()
        mock_px.bar.assert_called_once()
        mock_st.plotly_chart.assert_called_once_with(mock_fig)