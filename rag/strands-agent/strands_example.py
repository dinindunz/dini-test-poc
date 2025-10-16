#!/usr/bin/env python3
"""
Simple example of using the Strands code retrieval tool

This demonstrates the basic pattern for using the @tool decorator
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strands import Agent
from tools.strands_retrieval_tool import retrieve_code_examples


# Create an agent with the code retrieval tool
agent = Agent(tools=[retrieve_code_examples])


# Example 1: Simple query
print("=" * 60)
print("Example 1: Generate a REST controller")
print("=" * 60)

message1 = """
I need to create a Spring Boot REST controller for managing users.
Can you show me an example and generate the code?
"""

response1 = agent(message1)
print(response1)


# Example 2: Multiple requests
print("\n" + "=" * 60)
print("Example 2: Multiple questions")
print("=" * 60)

message2 = """
I have 3 requests:

1. Show me how to structure a Spring Boot application
2. Give me an example of a service layer class
3. Generate a Gradle build configuration
"""

response2 = agent(message2)
print(response2)


# Example 3: Specific filters
print("\n" + "=" * 60)
print("Example 3: Using filters")
print("=" * 60)

message3 = """
Find me examples of Java controller classes only.
I want to see how REST controllers are structured.
"""

response3 = agent(message3)
print(response3)
