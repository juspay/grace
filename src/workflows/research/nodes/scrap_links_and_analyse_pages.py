import asyncio

from src.ai.ai_service import AIService
from src.utils.transformations import sanitize_filename
from ..states.research_state import WorkflowState
from src.tools.browser import ScrappingService
from rich.console import Console
from src.tools.filemanager.filemanager import FileManager
from src.utils.research.research_utils import validate_page_content
console = Console()


def save_file(result: dict, fileManager: FileManager):
    filename = sanitize_filename(result["url"])
    content = f"""
        # Documentation for {result.get('title', 'No Title')}
        **Source URL:** {result['url']}
        ---
        {result['html_content']}
    """
    fileManager.write_file(filename, content)
    console.print(f"Stored {result['url']} to {filename}")

def validate_page(llm_client, connector_name: str, query: str, result: dict):
    result = validate_page_content(llm_client, connector_name, query, result["html_content"], result["url"])
    return result

def scrap_links_and_analyse_pages(state: WorkflowState) -> WorkflowState:
      try:
         scrapping_service = ScrappingService()
         llm_client = AIService(state["config"].getAiConfig())
         urls = state["search_results"]
         query = state["query"]
         connector_name = state["connector_name"]
         fileManager = state["file_manager"]
         fileManager.update_base_path(".grace/research/scraped_pages/" + connector_name)
         def callback(result):
            try:
                if result and result["status"] == "success":
                    analysis = validate_page(llm_client, connector_name, query, result)
                    if analysis.get("is_relevant", True):
                        state["visited_urls"].append(result["url"])
                        save_file(result, fileManager)
                elif result and result["status"] == "error":
                    state["scrapping_failed_pages"].append(result["url"])
            except Exception as e:
                console.print(f"Error occurred while processing {result['url']}: {e}")
         asyncio.run(scrapping_service.scrape_multiple_pages(urls, callback=callback))

      except Exception as e:
          console.print(f"Error occurred while scraping: {e}")
      return state