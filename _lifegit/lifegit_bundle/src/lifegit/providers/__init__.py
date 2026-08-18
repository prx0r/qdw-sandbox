from .chatgpt import ChatGPTProvider
from .claude import ClaudeProvider

PROVIDERS = {"chatgpt": ChatGPTProvider, "claude": ClaudeProvider}
