"""Information about whales — an example of streamed structured response validation.

This script streams structured responses about whales, validates the data
and displays it as a dynamic table using Rich as the data is received.

Run with:

    uv run ./stream_whales.py
"""

import asyncio
from typing import Annotated

import logfire
from pydantic import Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from rich.console import Console
from rich.live import Live
from rich.table import Table
from typing_extensions import NotRequired, TypedDict

# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_pydantic_ai()


class Whale(TypedDict):
    name: str
    length: Annotated[
        float, Field(description='Average length of an adult whale in meters as a single number.')
    ]
    weight: NotRequired[
        Annotated[
            float,
            Field(description='Average weight of an adult whale in kilograms as a single number.', ge=50),
        ]
    ]
    ocean: NotRequired[str]
    description: NotRequired[Annotated[str, Field(description='Short Description')]]


ollama_model = OpenAIChatModel(
    model_name='llama3.1:8b', # tools
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)

agent = Agent(
    ollama_model,
    output_type=list[Whale],
    retries=3,
    )



async def main():
    console = Console()
    with Live('\n' * 36, console=console) as live:
        console.print('Requesting data...', style='cyan')
        async with agent.run_stream('Generate me details of 3 species of Whale.') as result:
            console.print('Response:', style='green')

            async for whales in result.stream_output(debounce_by=0.01):
                table = Table(
                    title='Species of Whale',
                    caption='Streaming Structured responses from GPT-OSS',
                    width=120,
                )
                table.add_column('ID', justify='right')
                table.add_column('Name')
                table.add_column('Avg. Length (m)', justify='right')
                table.add_column('Avg. Weight (kg)', justify='right')
                table.add_column('Ocean')
                table.add_column('Description', justify='right')

                for wid, whale in enumerate(whales, start=1):
                    table.add_row(
                        str(wid),
                        whale['name'],
                        f'{whale["length"]:0.0f}',
                        f'{w:0.0f}' if (w := whale.get('weight')) else '…',
                        whale.get('ocean') or '…',
                        whale.get('description') or '…',
                    )
                live.update(table)


if __name__ == '__main__':
    asyncio.run(main())
