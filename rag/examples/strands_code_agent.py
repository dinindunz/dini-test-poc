#!/usr/bin/env python3
"""
Strands Agent for code generation using RAG (Retrieval Augmented Generation)

This agent can search your vectorised codebase and generate code based on examples.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strands import Agent
from tools.strands_retrieval_tool import retrieve_code_examples


# Create an agent with the code retrieval tool
agent = Agent(
    name="CodeGeneratorAgent",
    description="An expert Spring Boot developer that helps generate code based on examples from your codebase.",
    instructions="""
You are an expert Spring Boot developer with access to a vectorised codebase.

When a user asks you to generate code:
1. Use the retrieve_code_examples tool to find relevant examples
2. Analyse the retrieved examples to understand patterns and structure
3. Generate new code following the same patterns and best practices
4. Always use Australian English spelling in code comments and documentation
5. Cite which examples you used when generating code

Important:
- Use the tool proactively when code examples would help
- Apply metadata filters (file_type, layer) to get more relevant examples
- Explain your code and how it relates to the retrieved examples
    """,
    tools=[retrieve_code_examples],
    model="anthropic/claude-3-5-sonnet-20241022"
)


def main():
    """
    Example usage of the code generator agent
    """
    print("🤖 Code Generator Agent with RAG")
    print("=" * 60)
    print("\nThis agent can help you generate Spring Boot code")
    print("by searching through vectorised code examples.\n")
    print("=" * 60)

    # Example queries
    example_queries = [
        "Generate a Spring Boot REST controller for managing products",
        "Show me how to configure Gradle dependencies",
        "Create a service class following the repository pattern",
        "What is the project structure?",
    ]

    print("\n📝 Example queries you can try:")
    for i, query in enumerate(example_queries, 1):
        print(f"  {i}. {query}")

    print("\n" + "=" * 60)

    # Interactive mode
    while True:
        try:
            user_query = input("\n💬 Your question (or 'quit' to exit): ")

            if user_query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            if not user_query.strip():
                print("⚠️  Please enter a question")
                continue

            print("\n🤖 Agent is thinking...\n")

            # Agent processes query and uses retrieval tool automatically
            response = agent(user_query)

            print(f"\n{'='*60}")
            print("🤖 Agent Response:")
            print(f"{'='*60}\n")
            print(response)
            print(f"\n{'='*60}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
