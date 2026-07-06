from agents import sql_agent

from rich.console import Console
from rich.panel import Panel
from InquirerPy import inquirer
from llm import get_llm
from dotenv import load_dotenv

load_dotenv()


console = Console()

def extract_content(content):
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text = []

        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text.append(block.get("text", ""))

            elif hasattr(block, "text"):
                text.append(block.text)

        return "".join(text)

    return str(content)


def intro():
    console.print(
        Panel.fit(
            "[bold cyan]SQL AI POWERED DATA AGENT[/bold cyan]\n\n"
            "Examples:\n"
            "• Download the movies dataset from Kaggle\n"
            "• Show datasets in temp_csv\n"
            "• Load movies_metadata.csv into PostgreSQL\n\n"
            "[yellow]Exit commands:[/yellow]\n"
            "exit | quit | q | bye",
            title="🚀 Welcome",
            border_style="cyan",
        )
    )


def tool_started(name):
    console.print(
        Panel(
            f"[dim cyan]Running {name}[/dim cyan]",
            title="🔧 Tool",
            border_style="cyan",
            style="dim",
        )
    )


def tool_finished(name):
    console.print(
        Panel(
            f"[dim green]{name} completed[/dim green]",
            title="✅ Tool Complete",
            border_style="green",
            style="dim",
        )
    )


def main():
    intro()
    provider = inquirer.select(
        message="Select Ai provider:",
        choices=[
            "Ollama",
            "Google",
        ],
    ).execute()
    
    model_llm = get_llm(provider) 
    agent = sql_agent(model_llm=model_llm)

    chat_history = []

    while True:
        user = input("\nYou > ").strip()

        if user.lower() in {"exit", "quit", "q", "bye"}:
            console.print("\n👋 Goodbye\n")
            break

        if not user:
            continue

        chat_history.append(("user", user))

        try:
            final_answer = None

            with console.status("[cyan]Thinking...[/cyan]", spinner="dots") as status:

                for event in agent.stream({"messages": chat_history}):

                    if "model" in event:
                        msgs = event["model"].get("messages", [])

                        for msg in msgs:

                            if hasattr(msg, "tool_calls") and msg.tool_calls:

                                for tool in msg.tool_calls:
                                    tool_name = tool["name"]

                                    status.update(
                                        f"[cyan]Running tool:[/cyan] {tool_name}"
                                    )

                                    tool_started(tool_name)

                            if getattr(msg, "content", None):
                                content = extract_content(msg.content).strip()

                                if content:
                                    final_answer = content

                    elif "tools" in event:
                        msgs = event["tools"].get("messages", [])

                        for msg in msgs:

                            tool_name = getattr(msg, "name", "tool")

                            status.update(
                                f"[green]Completed:[/green] {tool_name}"
                            )

                            tool_finished(tool_name)

            if final_answer:
                console.print(
                    Panel(
                        final_answer,
                        title="🤖 Agent",
                        border_style="blue",
                    )
                )

        except Exception as e:
            console.print(
                Panel(
                    str(e),
                    title="❌ Error",
                    border_style="red",
                )
            )


if __name__ == "__main__":
    main()