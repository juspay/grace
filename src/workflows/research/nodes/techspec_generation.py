from ..states.research_state import WorkflowState

<<<<<<< HEAD

def load_visited_pages(
    file_manager: FileManager, visited_urls: list[str]
) -> list[dict[str, str]]:
    pages = []
    for url in visited_urls:
        filename = sanitize_filename(url)
        content = file_manager.read_file(filename)
        pages.append({"url": url, "content": content})
    return pages


def generate_techspec_content(llm_client: AIService, pages) -> str:
    try:
        # Placeholder implementation for techspec content generation
        prompt = prompt_config().get_with_values(
            "techspecPrompt",
            {
                "content": "provide a detailed technical specification based on the following documentation pages."
            },
        )
        messages = [
            {"role": "system", "content": prompt},
            *[{"role": "user", "content": page["content"]} for page in pages],
        ]
        techspec_content, success, error = llm_client.generate(messages=messages)
        if success:
            return techspec_content
        return ""
    except Exception as e:
        return "", False, str(e)
=======
>>>>>>> parent of 2971795 (feat: research flow (#31))


def techspec_generation(state: WorkflowState) -> WorkflowState:
   return state
