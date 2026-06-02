from unittest.mock import MagicMock, patch

from crammer.utils import deepseek_verify


def test_verify_valid_key():
    with patch("crammer.utils.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock()

        assert deepseek_verify("sk-fake") is True
        mock_client.chat.completions.create.assert_called_once()


def test_verify_invalid_key():
    with patch("crammer.utils.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized")

        assert deepseek_verify("sk-bad") is False
        mock_client.chat.completions.create.assert_called_once()
