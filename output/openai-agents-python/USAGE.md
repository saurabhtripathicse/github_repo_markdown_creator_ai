# Usage Guide

# Usage Guide for OpenAI Agents SDK

The OpenAI Agents SDK is a versatile framework designed to facilitate the creation of multi-agent workflows. This guide will walk you through the installation process, basic and advanced usage, configuration options, and troubleshooting tips.

## Installation

To get started with the OpenAI Agents SDK, follow these steps:

1. **Set up your Python environment**:

    ```bash
    python -m venv env
    source env/bin/activate
    ```

2. **Install the Agents SDK**:

    ```bash
    pip install openai-agents
    ```

    For additional voice support, use the optional `voice` group:

    ```bash
    pip install 'openai-agents[voice]'
    ```

## Basic Usage

Here's a simple example to help you get started with the OpenAI Agents SDK:

```python
from agents import Agent, Runner

# Create an agent with basic instructions
agent = Agent(name="Assistant", instructions="You are a helpful assistant")

# Run the agent with a sample input
result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Expected output:
# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.
```

Ensure you have set the `OPENAI_API_KEY` environment variable before running the code.

## Advanced Usage

For more complex workflows, you can utilize handoffs and custom functions:

### Handoffs Example

```python
from agents import Agent, Runner
import asyncio

# Define agents with specific language instructions
spanish_agent = Agent(name="Spanish agent", instructions="You only speak Spanish.")
english_agent = Agent(name="English agent", instructions="You only speak English")

# Triage agent to handoff based on language
triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
)

async def main():
    result = await Runner.run(triage_agent, input="Hola, ¿cómo estás?")
    print(result.final_output)
    # Expected output: ¡Hola! Estoy bien, gracias por preguntar. ¿Y tú, cómo estás?

if __name__ == "__main__":
    asyncio.run(main())
```

### Functions Example

```python
import asyncio
from agents import Agent, Runner, function_tool

# Define a custom function tool
@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny."

# Create an agent with the custom tool
agent = Agent(
    name="Weather Agent",
    instructions="You are a helpful agent.",
    tools=[get_weather],
)

async def main():
    result = await Runner.run(agent, input="What's the weather in Tokyo?")
    print(result.final_output)
    # Expected output: The weather in Tokyo is sunny.

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The OpenAI Agents SDK offers several configuration options to tailor the behavior of agents:

- **Model Settings**: Customize the model and its parameters used by the agents.
- **Tracing**: Enable or disable tracing to monitor and debug agent workflows.
- **Max Turns**: Limit the number of iterations an agent can perform in a loop.

To configure these options, refer to the SDK's documentation for detailed instructions.

## Troubleshooting

Here are some common issues and their solutions:

- **Environment Variable Error**: Ensure the `OPENAI_API_KEY` is set correctly in your environment.
- **Installation Issues**: Verify that your Python environment is activated and dependencies are installed.
- **Agent Not Responding**: Check the agent's instructions and ensure they are correctly defined.

For more detailed troubleshooting, consult the [documentation](https://openai.github.io/openai-agents-python/).

By following this guide, you should be able to effectively utilize the OpenAI Agents SDK to build and manage complex multi-agent workflows. For further examples and detailed documentation, explore the [examples directory](https://github.com/openai/openai-agents-python/tree/main/examples) and the [official documentation](https://openai.github.io/openai-agents-python/).