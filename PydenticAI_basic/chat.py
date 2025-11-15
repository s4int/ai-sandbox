"""Interactive terminal-based chat agent with split screen display using Textual.

Run with:
    uv run ./chat.py
"""

import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime

from pydantic_ai import Agent, ModelMessage, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, RichLog, Static


@dataclass
class ChatMessage:
    role: str
    message: str
    timestamp: datetime


class ChatState:
    """State to track chat history"""

    def __init__(self):
        self._conversation_history: OrderedDict[str, ChatMessage] = OrderedDict()

    def add_message(self, role: str, message: str, timestamp: datetime|None = None) -> None:
        """Add a message to the chat history"""
        timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        h = hash(f"{role}:{message}")

        if h not in self._conversation_history.keys():
            self._conversation_history.update({h: ChatMessage(role=role, message=message, timestamp=timestamp)})

    def get_history(self) -> list[ChatMessage]:
        """Get the chat history"""
        return list(self._conversation_history.values())


# Initialize model
ollama_model = OpenAIChatModel(
    model_name="qwen3:14b",
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
    settings=ModelSettings(temperature=0.7, max_tokens=2000),
)

# Create agent
agent = Agent(
    ollama_model,
    system_prompt=(
        "You are a helpful and friendly AI assistant. "
        "Provide clear, concise, and thoughtful responses. "
        "Show your reasoning when solving problems."
    ),
)


class Chat(RichLog):
    """Widget to display chat messages"""

    DEFAULT_CSS = """
    Chat {
        width: 2fr;
        height: 1fr;
        border: solid cyan;
        padding: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__(highlight=True, markup=True, wrap=True)
        self.messages = ChatState()
        self.streaming_lines= False

    def _render_message(self, msg: ChatMessage, msg_style: str|None = None) -> Text:
        if msg.role == "user":
            text = Text(f"[{msg.timestamp}] You:\n", style="bold cyan")
            text.append(msg.message + "\n", style=msg_style or "cyan")
        elif msg.role == "assistant":
            text = Text(f"[{msg.timestamp}] Assistant:\n", style="bold green")
            text.append(msg.message + "\n", style=msg_style or "green")
        else:  # system
            text = Text(f"[{msg.timestamp}] {msg.message}\n", style=msg_style or "yellow dim")
        return text

    def add_message(self, role: str, message: str) -> None:
        """Add a message to the chat history"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages.add_message(role, message, timestamp)
        text = self._render_message(ChatMessage(role=role, message=message, timestamp=timestamp))
        self.write(text)

    def refresh_chat(self) -> None:
        """Refresh the chat"""
        self.clear()
        for msg in self.messages.get_history():
            text = self._render_message(msg)
            self.write(text)

    def update_streaming(self, partial_message: str) -> None:
        """Update the last message with streaming content"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = self._render_message(
            ChatMessage(role="assistant", message=partial_message, timestamp=timestamp),
             msg_style="green dim"
             )

        # Clear previous streaming content
        if self.streaming_lines:
            # Re-add all previous messages
            self.refresh_chat()

        # Add streaming content
        self.write(text)
        self.streaming_lines = True

    def finalize_streaming(self, complete_message: str) -> None:
        """Finalize streaming message"""
        self.streaming_lines = False
        self.add_message("assistant", complete_message)
        self.refresh_chat()


class ChatApp(App):
    """Main chat application"""

    CSS = """
    Screen {
        layout: vertical;
    }

    #main_container {
        height: 1fr;
    }

    #input_container {
        height: auto;
        padding: 1;
        border: solid cyan;
    }

    Input {
        width: 1fr;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+d", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.is_processing = False
        self.current_response = ""
        self.message_history: list[ModelMessage] | None = None

    def compose(self) -> ComposeResult:
        """Create the layout"""
        yield Header(show_clock=True)

        with Horizontal(id="main_container"):
            yield Chat()

        with Vertical(id="input_container"):
            yield Static("💭 Type your message and press Enter (Ctrl+C to quit)", id="status")
            yield Input(placeholder="Your message...", id="chat_input")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app"""
        self.title = "AI Chat Agent"
        self.sub_title = "Powered by PydanticAI"

        # Focus on input
        self.query_one("#chat_input", Input).focus()

        # Add welcome message
        chat = self.query_one(Chat)
        chat.write(Text("Welcome! Start chatting...\n\n", style="cyan dim italic"))


    @on(Input.Submitted, "#chat_input")
    async def handle_input(self, event: Input.Submitted) -> None:
        """Handle user input submission"""
        if self.is_processing:
            return

        user_input = event.value.strip()
        event.input.value = ""  # Clear input

        if not user_input:
            return

        # Check for exit commands
        if user_input.lower() in ["exit", "quit", "bye"]:
            self.exit()
            return

        # Add user message
        chat = self.query_one(Chat)
        chat.add_message("user", user_input)

        # Process with AI
        self.process_message(user_input)

    @work(exclusive=True)
    async def process_message(self, user_input: str) -> None:
        """Process user message with AI agent"""
        self.is_processing = True
        status = self.query_one("#status", Static)
        status.update("⏳ Processing...")

        chat = self.query_one(Chat)

        self.current_response = ""

        try:
            # Stream the response
            async with agent.run_stream(
                user_input,
                message_history=self.message_history,
                ) as result:

                async for resp, is_last in result.stream_responses(debounce_by=0.01):
                    for part in resp.parts:
                        if part.part_kind == "thinking":
                            chat.add_message('system', "thinking: "+part.content)
                        if part.part_kind == "text":
                            self.current_response = part.content
                            chat.update_streaming(self.current_response)
                    await asyncio.sleep(0.01)

                # Finalize the message
                chat.finalize_streaming(self.current_response)
                self.message_history = result.all_messages()
                # Log usage info
                usage = result.usage()
                chat.add_message('system',
                    f"Tokens - Input: {usage.input_tokens}, "
                    f"Output: {usage.output_tokens}, Total: {usage.total_tokens}"
                )

        except Exception as e:
            error_msg = f"Error: {e!s}"
            chat.add_message('system',f"❌ {error_msg}")
            chat.add_message("system", error_msg)

        finally:
            self.is_processing = False
            status.update("💭 Type your message and press Enter (Ctrl+C to quit)")
            self.current_response = ""


def main() -> None:
    """Entry point"""
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
