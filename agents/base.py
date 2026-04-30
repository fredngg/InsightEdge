import anthropic
from config.settings import ANTHROPIC_API_KEY, CLAUDE_MODEL


class BaseAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = CLAUDE_MODEL
        self._input_tokens: int = 0
        self._output_tokens: int = 0

    def ask_claude(self, system_prompt: str, user_message: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        self._input_tokens += response.usage.input_tokens
        self._output_tokens += response.usage.output_tokens
        return response.content[0].text

    def _reset_usage(self):
        self._input_tokens = 0
        self._output_tokens = 0

    def _get_usage(self) -> dict:
        return {"input": self._input_tokens, "output": self._output_tokens}
