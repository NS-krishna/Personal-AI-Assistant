from ddgs import DDGS

def search_web(query: str, max_results: int = 5) -> str:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return "No results found."
        
        # Format results
        formatted = []
        for i, r in enumerate(results):
            formatted.append(
                f"Result {i+1}: {r.get('title','')}\n"
                f"URL: {r.get('href','')}\n"
                f"Summary: {r.get('body','')[:500]}"
            )
        
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Search error: {str(e)}"

def search_and_answer(query: str, router_llm) -> str:
    raw_results = search_web(query)
    
    prompt = f"""
User asked: "{query}"

Here are real web search results with actual content snippets:
{raw_results}

Instructions:
- Answer the question directly using the content in the snippets above
- DO NOT say "check this website" or "visit this URL"
- DO NOT list websites — extract and summarize the actual information
- Give a direct, informative answer in 3-5 sentences
- If the snippets contain the answer, state it clearly
"""
    return router_llm.generate(prompt, task_type="general")
