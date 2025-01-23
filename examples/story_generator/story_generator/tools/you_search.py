import os
from typing import Dict

import httpx
from litellm import acompletion
from pydantic import BaseModel, Field

from autoplan import tool, trace

# using a global client is better than making one for each request
# see https://www.python-httpx.org/async/
client = httpx.AsyncClient()


@trace
async def _get_search_results(query: str) -> Dict:
    api_key = os.getenv("YDC_API_KEY")
    if not api_key:
        raise ValueError("YDC_API_KEY is not set")
    headers = {"X-API-Key": api_key}

    """Execute You.com search asynchronously"""
    try:
        params = {"query": query}
        response = await client.get(
            "https://api.ydc-index.io/search",
            params=params,
            headers=headers,
        )
        return response.json()
    except Exception as e:
        print(f"Error executing search: {e}")
        return {}


class YouSearchResult(BaseModel):
    summary: str = Field(
        ...,
        description="The summary of the search results within the context of the search objective.",
    )
    sources: list[str] = Field(..., description="The links to the search results.")


@tool
async def you_search(objective: str) -> YouSearchResult:
    """
    Use this tool to search the web for grounding information snippets that can be used in an LLM-prompt.
    """
    result = await _get_search_results(objective)

    response = await acompletion(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """
You will receive a JSON object returned by a search engine. 
Your task is to analyze the search results and generate a focused summary that highlights content specifically relevant to the provided search objective. 
Only include information that directly relates to or helps address the objective.
Follow these steps:
# Steps

1. **Assess the sesarch output:** Evaluate the provided search output against the objective.
2. **Summarize Key Findings:** Craft a highly concise summary that highlights the information or findings of greatest relevance.
3. **Extract Verbatim Details:** Identify any key statements that warrant direct quotes and include them verbatim.
4. **Provide Links:** Mention any given URLs or links that are referenced in the output where relevant, ensuring they can be used for further investigation.

# Output Format

- **Summary**: Provide a 1-2 sentence summary of the search result tailored to the objective.
- **Findings**: List verbatim excerpts that add significant context or details, marked with quotation marks.
- **Links**: If applicable, provide URLs from the search results. Make sure to provide the most specific search results. 

Format the response in paragraph form, but clearly label different elements as follows:
  
**Summary**: [brief, pertinent summary]

**Notable Findings**:
- "[Direct quote or excerpt #1]"  [URL excerpt 1]
- "[Direct quote or excerpt #2]" [URL excerpt 2]

# Example

**Summary**: The search identified credible sources that refute the claim that water is not composed of oxygen .

**Notable Findings**: 
- "Water is composed of oxygen and hydrogen molecules" [http://wikipedia.org/water]
- "Water can be decomposed to oxygen and hydrogen molecules" [http://wikipedia.org/how_to_create_hydrogen]

# Notes

- Ensure all summaries are customized strictly for the step's objective.
- Only include verbatim excerpts that are crucial or contain specific details.
- Keep the focus on brevity; avoid adding unnecessary context or commentary.

                """,
            },
            {
                "role": "user",
                "content": f"Search objective: {objective}\n\nSearch results: {result}",
            },
        ],
        response_format=YouSearchResult,
    )
    return YouSearchResult.model_validate_json(response.choices[0].message.content)
