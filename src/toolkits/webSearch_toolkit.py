# src/toolkits/websearch_toolkit.py
from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional

import requests

import urllib.request
import urllib.error

from dotenv import load_dotenv
load_dotenv()

from src.toolkits import FunctionTool
from src.toolkits import BaseToolkit


class WebSearchToolkit(BaseToolkit):
    """
    Toolkit exposing web search and open-url capabilities via Exa API.
    Methods are wrapped by BaseToolkit with timeouts (ensure your `with_timeout`
    decorator preserves sync functions, or the wrapper will still be async).

    Environment variables (if `exa_api_key` not provided):
        - EXA_API_KEY
    """

    def __init__(
        self,
        exa_api_key: Optional[str] = None,
        *,
        timeout: Optional[float] = None,
        filter_keywords: Optional[List[str]] = None,
    ) -> None:
        """
        Args:
            exa_api_key (Optional[str]): Exa API key. If None, read from EXA_API_KEY.
            timeout (Optional[float]): Timeout in seconds for requests.
            filter_keywords (Optional[list[str]]): Case-insensitive keywords to filter out.
        """
        super().__init__(timeout=timeout)

        self.exa_api_key = exa_api_key or os.getenv("EXA_API_KEY")
        if not self.exa_api_key:
            raise ValueError(
                "Exa API key is required. Provide `exa_api_key` or set EXA_API_KEY in the environment."
            )

        default_filters = [
            "huggingface", "hugging face","gymnasium"
            "BYTESIZED32", "cwm benchmark","text2world"
            "github.com/openai/gym",
        ]
        self._filter_keywords = [k.lower() for k in (filter_keywords or default_filters)]

    # --------------------------- HTTP helpers ---------------------------

    def _post_json(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous POST with JSON body, returning parsed JSON or raising."""
        timeout = float(self.timeout) if self.timeout is not None else 30.0

        if requests is not None:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}")
            return resp.json()

        # Fallback to urllib
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}") from e

    # --------------------------- Tools (introspected) ---------------------------

    def browser_search(self, query: str, topn: int = 10) -> str:
        r"""Search for information on the web and return filtered results.

        Args:
            query (str): The search query to find information on the web.
            topn (int, optional): Number of search results to return. Defaults to 10.

        Returns:
            str: A JSON-encoded string whose top-level object contains a "data" field.
                 "data.results" is a list of result objects, each with:
                 - title (str): Page title.
                 - url (str): Page URL.
                 - publishedDate (str): Publish time (ISO-like) or empty if unknown.
                 - text (str): Short text snippet (~up to 300 characters).
                 On failure, returns a brief error message string.
        """
        headers = {
            "x-api-key": self.exa_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "type": "keyword",
            "numResults": int(topn),
            "contents": {"text": {"maxCharacters": 300}},
        }

        try:
            result = self._post_json("https://api.exa.ai/search", headers, payload)
        except Exception as e:
            return f"Error searching web: {e!s}"

        formatted_results: List[Dict[str, Any]] = []
        for item in result.get("results", []):
            title = (item.get("title") or "").lower()
            text = (item.get("text") or "").lower()
            if any(k in title or k in text for k in self._filter_keywords):
                continue
            formatted_results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "publishedDate": item.get("publishedDate", ""),
                "text": item.get("text", ""),
            })

        return json.dumps({"data": {"results": formatted_results}}, indent=2)

    def browser_open(self, url: str) -> str:
        r"""Open the URL and fetch its textual content.

        Args:
            url (str): The URL to open and fetch content from.

        Returns:
            str: A JSON-encoded string whose top-level object contains a "data" field.
                 "data.results" is a list where each item has:
                 - text (str): Extracted textual content of the page.
                 On failure, returns a brief error message string.
        """
        headers = {
            "x-api-key": self.exa_api_key,
            "Content-Type": "application/json",
        }
        payload = {"ids": [url], "text": True}

        try:
            result = self._post_json("https://api.exa.ai/contents", headers, payload)
        except Exception as e:
            return f"Error fetching URL: {e!s}"

        formatted_results = [{"text": item.get("text", "")} for item in result.get("results", [])]
        return json.dumps({"data": {"results": formatted_results}}, indent=2)

    # --------------------------- Registration ---------------------------

    def get_tools(self) -> List[FunctionTool]:
        # Runtime will introspect function signature + docstring to build schema.
        return [
            FunctionTool(self.browser_search),
            FunctionTool(self.browser_open),
        ]