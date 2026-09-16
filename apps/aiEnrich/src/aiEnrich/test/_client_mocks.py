from unittest.mock import MagicMock


def _build_response(content: str) -> MagicMock:
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


def make_choice_response(content: str) -> MagicMock:
    client = MagicMock()
    client.chat.completions.create.return_value = _build_response(content)
    return client


def make_sequence_choices(*contents) -> MagicMock:
    responses = [_build_response(c) if not isinstance(c, Exception) else c for c in contents]
    client = MagicMock()
    client.chat.completions.create.side_effect = responses
    return client