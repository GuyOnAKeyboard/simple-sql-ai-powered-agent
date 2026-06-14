from langchain.agents import create_agent

from llm import llm
from tools import tool_kit


def sql_agent():
    """
    Creates and returns a LangChain SQL/data agent.
    """

    agent = create_agent(
        model=llm,
        tools=tool_kit,
    )

    return agent