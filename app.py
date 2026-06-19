from agents import sql_agent


def print_intro():
    print("\n" + "=" * 60)
    print("SQL AI POWERED DATA AGENT")
    print("=" * 60)
    print("""
Welcome

This is an AI powered SQL and data agent.

It can:
- Download Kaggle datasets into local project
- Explore temp_csv dataset folders
- Load and preview CSV files using pandas
- Help understand and prepare data

Example queries:
- Download the movies dataset from Kaggle
- Show datasets in temp_csv
- Load movies_metadata.csv and show preview

Type 'exit' to quit
    """)
    print("=" * 60 + "\n")


def main():
    print_intro()

    agent = sql_agent()

    chat_history = []

    # Chat loop
    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit", "q", "stop","bye"]:
            print("Exiting SQL AI Agent. Goodbye.")
            break

        if not user_input:
            continue

        try:
            # 1. Register the current human prompt to the timeline sequence array
            chat_history.append(("user", user_input))

            # 2. Forward the full structural message timeline to the LangGraph executor
            query_payload = {"messages": chat_history}

            response = agent.invoke(query_payload)

            # 3. Handle the response and save full message state returned by the graph
            if isinstance(response, dict) and "messages" in response:
                # Update our history track with the entire execution run state (includes tool calls and agent text)
                chat_history = response["messages"]

                # Extract the last textual thought message generated to show the client
                print("\nAgent:", chat_history[-1].content, "\n")
            else:
                print("\nAgent:", response, "\n")

        except Exception as e:
            print("\nError:", str(e), "\n")


if __name__ == "__main__":
    main()
