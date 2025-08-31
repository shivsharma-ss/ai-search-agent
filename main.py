"""CLI entrypoint for the AI Search Agent.

Provides a simple interactive CLI that uses the packaged pipeline.
For API usage, run: `uvicorn ai_search_agent.api:app --reload`.
"""

from ai_search_agent.pipeline import run_research


def run_cli() -> None:
    print("Multi-Source Research Agent (CLI)")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("Ask me anything: ")
        if user_input.lower() == "exit":
            print("Bye")
            break

        print("\nStarting parallel research process...")
        print("Launching Google, Bing, and Reddit searches...\n")
        final_state = run_research(user_input)

        final_answer = final_state.get("final_answer")
        if final_answer:
            print(f"\nFinal Answer:\n{final_answer}\n")

        print("-" * 80)


if __name__ == "__main__":
    run_cli()
