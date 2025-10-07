#!/usr/bin/env python3
"""
LangGraph-based Mock Server Generator
Migrated from n8n pipeline to create mock servers from API documentation
"""

import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, TypedDict

import litellm
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Load environment variables
load_dotenv()

class MockServerState(TypedDict):
    """State for the mock server generation workflow"""
    messages: list[BaseMessage]
    tech_spec: str
    ai_response: str
    parsed_response: Dict[str, Any]
    server_js: str
    package_json: str
    info: str
    project_path: str
    server_process: Any


class MockServerGenerator:
    """LangGraph workflow for generating mock servers from API documentation"""

    def __init__(self, output_path: str = None):
        """
        Initialize the mock server generator

        Args:
            output_path: Directory where the mock server will be created
        """
        self.output_path = output_path or os.getcwd()
        self.api_base = os.getenv("BASE_URL")
        self.api_key =  os.getenv("API_KEY")
        self.model = os.getenv("MODEL")

        # Configure LiteLLM
        litellm.api_base = self.api_base
        litellm.api_key = self.api_key

        # Build the workflow graph
        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(MockServerState)

        # Add nodes
        workflow.add_node("ai_agent", self._ai_agent_node)
        workflow.add_node("parse_response", self._parse_response_node)
        workflow.add_node("create_project", self._create_project_node)
        workflow.add_node("start_server", self._start_server_node)

        # Define the flow
        workflow.add_edge(START, "ai_agent")
        workflow.add_edge("ai_agent", "parse_response")
        workflow.add_edge("parse_response", "create_project")
        workflow.add_edge("create_project", "start_server")
        workflow.add_edge("start_server", END)

        return workflow.compile()

    async def _ai_agent_node(self, state: MockServerState) -> MockServerState:
        """Generate server code using AI agent"""
        print(" Generating mock server code with AI...")

        prompt = f"""Create an express server which mocks all the api calls mentioned here. If encryption is required use crypto or some popular libraries to handle it. Print all endpoints created after server starts running.

Format your response exactly like the JSON given below and don't respond with any subscript like "of course" or "here you go":

{{
  "server_js": "// Your server.js code here",
  "package_json": "// Your package.json content here",
  "info": "// Simple Markdown text providing all generated curls"
}}

{state['tech_spec']}"""

        try:
            model_name = self.model

            response = await litellm.acompletion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                api_base=self.api_base,
                api_key=self.api_key
            )

            ai_response = response.choices[0].message.content

            return {
                **state,
                "ai_response": ai_response,
                "messages": state.get("messages", []) + [
                    HumanMessage(content=prompt),
                    AIMessage(content=ai_response)
                ]
            }
        except Exception as e:
            print(f"❌ Error calling AI agent: {e}")
            raise

    def _parse_response_node(self, state: MockServerState) -> MockServerState:
        """Parse AI response to extract JSON"""
        print("📝 Parsing AI response...")

        ai_response = state["ai_response"]

        # Remove markdown code block markers
        clean_json = re.sub(r'```json\n?', '', ai_response)
        clean_json = re.sub(r'\n?```$', '', clean_json).strip()

        try:
            parsed_data = json.loads(clean_json)

            return {
                **state,
                "parsed_response": parsed_data,
                "server_js": parsed_data.get("server_js", ""),
                "package_json": parsed_data.get("package_json", ""),
                "info": parsed_data.get("info", "")
            }
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON response: {e}")
            print(f"Raw response: {clean_json}")
            raise

    def _create_project_node(self, state: MockServerState) -> MockServerState:
        """Create project directory and files"""
        print("📁 Creating project directory and files...")

        project_path = os.path.join(self.output_path, "mock-server")

        try:
            # Create directory
            Path(project_path).mkdir(parents=True, exist_ok=True)

            # Write files
            files = {
                "server.js": state["server_js"],
                "package.json": state["package_json"],
                "api_docs.md": state["info"]
            }

            for filename, content in files.items():
                file_path = Path(project_path) / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Created {filename}")

            # Install dependencies
            print("📦 Installing npm dependencies...")
            result = subprocess.run(
                ["npm", "install"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
            else:
                print(f"⚠️  npm install warnings: {result.stderr}")

            return {
                **state,
                "project_path": project_path
            }

        except Exception as e:
            print(f"❌ Error creating project: {e}")
            raise

    def _start_server_node(self, state: MockServerState) -> MockServerState:
        """Start the mock server"""
        print("🚀 Starting mock server...")

        project_path = state["project_path"]

        try:
            # Start server in background
            process = subprocess.Popen(
                ["node", "server.js"],
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            print(f"✅ Mock server started with PID: {process.pid}")
            print(f"📂 Project location: {project_path}")
            print(f"📖 API documentation: {project_path}/api_docs.md")

            # Try to open VS Code (optional)
            try:
                subprocess.run(["code", project_path], timeout=5)
                print("💻 Opened project in VS Code")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("💻 VS Code not available or failed to open")

            return {
                **state,
                "server_process": process
            }

        except Exception as e:
            print(f"❌ Error starting server: {e}")
            raise

    async def generate_mock_server(self, tech_spec: str) -> MockServerState:
        """
        Generate a mock server from technical specification

        Args:
            tech_spec: The API technical documentation/specification

        Returns:
            Final state with all generated artifacts
        """
        print(" Starting mock server generation workflow...")

        initial_state = MockServerState(
            messages=[],
            tech_spec=tech_spec,
            ai_response="",
            parsed_response={},
            server_js="",
            package_json="",
            info="",
            project_path="",
            server_process=None
        )

        try:
            final_state = await self.workflow.ainvoke(initial_state)
            print("🎉 Mock server generation completed successfully!")
            return final_state
        except Exception as e:
            print(f"❌ Workflow failed: {e}")
            raise


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate mock servers from API documentation")
    parser.add_argument("--spec-file", "-f", help="Path to API specification file")
    parser.add_argument("--output-path", "-o", help="Output directory path (default: current directory)")

    args = parser.parse_args()

    # Get tech spec
    if args.spec_file:
        with open(args.spec_file, 'r', encoding='utf-8') as f:
            tech_spec = f.read()
    else:
        print("❌ Please provide --spec-file")
        sys.exit(1)

    # Determine output path
    output_path = args.output_path if args.output_path else os.getcwd()

    # Create generator
    generator = MockServerGenerator(output_path)

    # Run the workflow
    try:
        final_state = asyncio.run(generator.generate_mock_server(tech_spec))

        print("\n" + "="*50)
        print("🎉 MOCK SERVER READY!")
        print("="*50)
        print(f"📂 Project: {final_state['project_path']}")
        print(f"🔧 Server PID: {final_state['server_process'].pid if final_state.get('server_process') else 'N/A'}")
        print(f"📖 Docs: {final_state['project_path']}/api_docs.md")
        print("="*50)

        # Keep the script running if server is started
        if final_state.get('server_process'):
            print("Press Ctrl+C to stop the server...")
            try:
                final_state['server_process'].wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping server...")
                final_state['server_process'].terminate()
                final_state['server_process'].wait()
                print("✅ Server stopped")

    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()