import pytest
from unittest.mock import patch

@patch('services.filter_configurations_service.FilterConfigurationsService.get_all')
def test_get_all_configurations(mock_get_all, client):
    mock_data = [
        {'id': 1, 'name': 'Config 1', 'filters': {}, 'notify': False, 'statistics': True,
         'created': '2024-01-01T10:00:00', 'modified': None}
    ]
    mock_get_all.return_value = mock_data
    response = client.get("/api/filter-configurations")
    assert response.status_code == 200
    assert response.json() == mock_data

@patch('services.filter_configurations_service.FilterConfigurationsService.create')
def test_create_configuration(mock_create, client):
    mock_create.return_value = {
        'id': 1, 'name': 'New Config', 'filters': {'page': 1}, 'notify': False, 'statistics': True,
        'created': '2024-01-01T10:00:00', 'modified': None
    }
    response = client.post("/api/filter-configurations", json={
        'name': 'New Config', 'filters': {'page': 1}, 'notify': False
    })
    assert response.status_code == 201
    assert response.json()['name'] == 'New Config'

@patch('services.filter_configurations_service.FilterConfigurationsService.create')
def test_create_duplicate_name(mock_create, client):
    mock_create.side_effect = ValueError("already exists")
    response = client.post("/api/filter-configurations", json={
        'name': 'Duplicate', 'filters': {}, 'notify': False
    })
    assert response.status_code == 400

@patch('services.filter_configurations_service.FilterConfigurationsService.get_by_id')
def test_get_configuration_by_id(mock_get, client):
    mock_get.return_value = {'id': 1, 'name': 'Test', 'filters': {}, 'notify': False, 'statistics': True,
                             'created': '2024-01-01T10:00:00', 'modified': None}
    response = client.get("/api/filter-configurations/1")
    assert response.status_code == 200
    assert response.json()['id'] == 1

@patch('services.filter_configurations_service.FilterConfigurationsService.update')
def test_update_configuration(mock_update, client):
    mock_update.return_value = {'id': 1, 'name': 'Updated', 'filters': {}, 'notify': True, 'statistics': True,
                                'created': '2024-01-01T10:00:00', 'modified': None}
    response = client.put("/api/filter-configurations/1", json={'name': 'Updated'})
    assert response.status_code == 200
    assert response.json()['name'] == 'Updated'

@patch('services.filter_configurations_service.FilterConfigurationsService.delete')
def test_delete_configuration(mock_delete, client):
    mock_delete.return_value = True
    response = client.delete("/api/filter-configurations/1")
    assert response.status_code == 204
