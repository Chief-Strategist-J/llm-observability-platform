import logging
import requests
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import os
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DuckDuckGoSearch:
    
    @staticmethod
    def search(query: str, count: int = 10) -> Dict[str, Any]:
        logger.info("event=duckduckgo_search_start query=%s count=%s", query[:50], count)
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            params = {
                "q": query,
                "format": "json",
                "no_redirect": 1,
                "max_results": min(count, 30)
            }
            
            response = requests.get(
                "https://api.duckduckgo.com/",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error("event=duckduckgo_search_failed status=%s", response.status_code)
                return {"success": False, "error": f"API returned status {response.status_code}"}
            
            data = response.json()
            results = []
            
            for result in data.get("Results", [])[:count]:
                results.append({
                    "title": result.get("Text", ""),
                    "url": result.get("FirstURL", ""),
                    "description": result.get("Result", ""),
                    "type": "web"
                })
            
            logger.info("event=duckduckgo_search_success query=%s results=%s", query[:50], len(results))
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
            
        except requests.exceptions.Timeout:
            logger.error("event=duckduckgo_search_timeout query=%s", query[:50])
            return {"success": False, "error": "Search request timed out"}
        except Exception as e:
            logger.error("event=duckduckgo_search_exception error=%s", str(e))
            return {"success": False, "error": str(e)}

class WikipediaSearch:
    
    @staticmethod
    def search(query: str, count: int = 5) -> Dict[str, Any]:
        logger.info("event=wikipedia_search_start query=%s count=%s", query[:50], count)
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": min(count, 50)
            }
            
            response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error("event=wikipedia_search_failed status=%s", response.status_code)
                return {"success": False, "error": f"API returned status {response.status_code}"}
            
            data = response.json()
            results = []
            
            for result in data.get("query", {}).get("search", [])[:count]:
                results.append({
                    "title": result.get("title", ""),
                    "url": f"https://en.wikipedia.org/wiki/{result.get('title', '').replace(' ', '_')}",
                    "description": result.get("snippet", ""),
                    "type": "wikipedia"
                })
            
            logger.info("event=wikipedia_search_success query=%s results=%s", query[:50], len(results))
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
            
        except requests.exceptions.Timeout:
            logger.error("event=wikipedia_search_timeout query=%s", query[:50])
            return {"success": False, "error": "Search request timed out"}
        except Exception as e:
            logger.error("event=wikipedia_search_exception error=%s", str(e))
            return {"success": False, "error": str(e)}

class WebSearchTools:
    
    @staticmethod
    def web_search(query: str, count: int = 10) -> Dict[str, Any]:
        logger.info("event=web_search_start query=%s count=%s", query[:50], count)
        
        if not query or not isinstance(query, str):
            return {"success": False, "error": "Invalid query"}
        
        try:
            duckduckgo_result = DuckDuckGoSearch.search(query, count)
            wikipedia_result = WikipediaSearch.search(query, count // 2)
            
            combined_results = []
            
            if duckduckgo_result.get("success"):
                combined_results.extend(duckduckgo_result.get("results", []))
            
            if wikipedia_result.get("success"):
                combined_results.extend(wikipedia_result.get("results", []))
            
            if not combined_results:
                logger.warning("event=web_search_no_results query=%s", query[:50])
                return {"success": False, "error": "No results found"}
            
            logger.info("event=web_search_success query=%s total_results=%s", query[:50], len(combined_results))
            
            return {
                "success": True,
                "query": query,
                "results": combined_results[:count],
                "count": len(combined_results[:count])
            }
            
        except Exception as e:
            logger.error("event=web_search_exception error=%s", str(e))
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def visit_url(url: str) -> Dict[str, Any]:
        logger.info("event=visit_url_start url=%s", url[:80])
        
        if not url or not isinstance(url, str):
            return {"success": False, "error": "Invalid URL"}
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            title = soup.title.string if soup.title else "No title"
            text = text[:5000]
            
            logger.info("event=visit_url_success url=%s text_len=%s", url[:80], len(text))
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "content": text,
                "length": len(text)
            }
            
        except requests.exceptions.Timeout:
            logger.error("event=visit_url_timeout url=%s", url[:80])
            return {"success": False, "error": "Request timed out", "url": url}
        except Exception as e:
            logger.error("event=visit_url_exception url=%s error=%s", url[:80], str(e))
            return {"success": False, "error": str(e), "url": url}
    
    @staticmethod
    def extract_text(url: str, selector: Optional[str] = None) -> Dict[str, Any]:
        logger.info("event=extract_text_start url=%s selector=%s", url[:80], selector)
        
        if not url or not isinstance(url, str):
            return {"success": False, "error": "Invalid URL"}
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if selector:
                elements = soup.select(selector)
                text = "\n".join([elem.get_text(strip=True) for elem in elements])
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            text = text[:3000]
            
            logger.info("event=extract_text_success url=%s text_len=%s", url[:80], len(text))
            
            return {
                "success": True,
                "url": url,
                "selector": selector,
                "content": text,
                "length": len(text)
            }
            
        except Exception as e:
            logger.error("event=extract_text_exception error=%s", str(e))
            return {"success": False, "error": str(e), "url": url}
    
    @staticmethod
    def crawl_site(domain: str, max_pages: int = 5) -> Dict[str, Any]:
        logger.info("event=crawl_site_start domain=%s max_pages=%s", domain, max_pages)
        
        if not domain or not isinstance(domain, str):
            return {"success": False, "error": "Invalid domain"}
        
        try:
            visited = set()
            to_visit = [domain if domain.startswith("http") else f"https://{domain}"]
            results = []
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            while to_visit and len(visited) < max_pages:
                url = to_visit.pop(0)
                
                if url in visited:
                    continue
                
                visited.add(url)
                
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(url, href)
                        
                        if domain in full_url and full_url not in visited:
                            to_visit.append(full_url)
                    
                    results.append({
                        "url": url,
                        "title": soup.title.string if soup.title else "No title",
                        "links_found": len(soup.find_all('a', href=True))
                    })
                    
                except Exception as e:
                    logger.debug("event=crawl_page_failed url=%s error=%s", url, str(e))
                    continue
            
            logger.info("event=crawl_site_complete domain=%s pages=%s", domain, len(results))
            
            return {
                "success": True,
                "domain": domain,
                "pages_crawled": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error("event=crawl_site_exception error=%s", str(e))
            return {"success": False, "error": str(e), "domain": domain}
    
    @staticmethod
    def get_news(topic: str, count: int = 10) -> Dict[str, Any]:
        logger.info("event=get_news_start topic=%s count=%s", topic, count)
        
        if not topic or not isinstance(topic, str):
            return {"success": False, "error": "Invalid topic"}
        
        try:
            duckduckgo_result = DuckDuckGoSearch.search(f"{topic} news", count)
            
            if not duckduckgo_result.get("success"):
                return {"success": False, "error": "Failed to fetch news"}
            
            results = duckduckgo_result.get("results", [])
            
            for result in results:
                result["type"] = "news"
            
            logger.info("event=get_news_success topic=%s results=%s", topic, len(results))
            
            return {
                "success": True,
                "topic": topic,
                "results": results[:count],
                "count": len(results[:count])
            }
            
        except Exception as e:
            logger.error("event=get_news_exception error=%s", str(e))
            return {"success": False, "error": str(e)}

AVAILABLE_TOOLS = {
    "web_search": {
        "func": WebSearchTools.web_search,
        "description": "Search web using DuckDuckGo and Wikipedia",
        "params": {
            "query": "str - search query",
            "count": "int - number of results"
        }
    },
    "visit_url": {
        "func": WebSearchTools.visit_url,
        "description": "Visit URL and extract text",
        "params": {
            "url": "str - URL to visit"
        }
    },
    "extract_text": {
        "func": WebSearchTools.extract_text,
        "description": "Extract text from URL with selector",
        "params": {
            "url": "str - URL to extract from",
            "selector": "str - CSS selector (optional)"
        }
    },
    "crawl_site": {
        "func": WebSearchTools.crawl_site,
        "description": "Crawl website and extract links",
        "params": {
            "domain": "str - domain to crawl",
            "max_pages": "int - maximum pages"
        }
    },
    "get_news": {
        "func": WebSearchTools.get_news,
        "description": "Get news articles about topic",
        "params": {
            "topic": "str - topic to search",
            "count": "int - number of results"
        }
    }
}
