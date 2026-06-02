from unittest.mock import MagicMock, patch

from crammer.utils import deepseek_chat


def test_retry_then_success():
    with patch("crammer.utils.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello there"

        mock_client.chat.completions.create.side_effect = [
            Exception("timeout"),
            Exception("timeout"),
            mock_response,
        ]

        result = deepseek_chat([{"role": "user", "content": "hi"}], "sk-test")
        assert result == "Hello there"
        assert mock_client.chat.completions.create.call_count == 3
