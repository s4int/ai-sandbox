"""
Basic async example using Pydentic AI.

Run with:

    uv run ./basic_async.py
"""
import asyncio

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
from rich import print
from rich.pretty import pprint


class CityLocation(BaseModel):
    city: str
    country: str

ollama_model = OpenAIChatModel(
    # model_name='llama3:8b', # text
    model_name='llama3.1:8b', # tools
    # model_name='gpt-oss:20b', # tools, thinking
    provider=OllamaProvider(base_url='http://localhost:11434/v1'),
)

agent = Agent(
    ollama_model,
    system_prompt='You are a helpful assistant that can answer questions about the world.',
    output_type=CityLocation,
    )


async def main():
    result = await agent.run('Where were the olympics held in 2012?')
    print(f"Response:\n{result.output}\n")

    print("All messages:")
    pprint(result.all_messages(), expand_all=True, indent_guides=True)

    print(f"Usage:\n{result.usage()}")

if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
