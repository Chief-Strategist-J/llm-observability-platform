"""
Web Search Tools Integration with Brave Search API
Provides tools for intelligent agents to search the web and extract information
"""

import logging
import requests
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import os
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
BRAVE_API_BASE = "https://api.search.brave.com/res/v1"

class WebSearchTools:
    """Tools for web search and information extraction"""
    
    @staticmethod
    def web_search(query: str, count: int = 10) -> Dict[str, Any]:
        """
        Search the web using Brave Search API
        
        Args:
            query: Search query string
            count: Number of results to return (max 20)
            
        Returns:
            Dictionary with search results
        """
        if not BRAVE_API_KEY:
            logger.warning("event=web_search_no_api_key")
            return {"success": False, "error": "BRAVE_API_KEY not configured"}
        
        logger.info("event=web_search_start query=%s count=%s", query[:50], count)
        
        try:
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": BRAVE_API_KEY
            }
            
            params = {
                "q": query,
                "count": min(count, 20)
            }
            
            response = requests.get(
                f"{BRAVE_API_BASE}/web/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error("event=web_search_failed status=%s", response.status_code)
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}"
                }
            
            data = response.json()
            results = []
            
            # Extract web results
            for result in data.get("web", {}).get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "description": result.get("description", ""),
                    "type": "web"
                })
            
            logger.info("event=web_search_success query=%s results=%s", query[:50], len(results))
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
            
        except requests.exceptions.Timeout:
            logger.error("event=web_search_timeout query=%s", query[:50])
            return {"success": False, "error": "Search request timed out"}
        except Exception as e:
            logger.error("event=web_search_exception error=%s", str(e))
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def visit_url(url: str) -> Dict[str, Any]:
        """
        Visit a URL and extract text content
        
        Args:
            url: URL to visit
            
        Returns:
            Dictionary with extracted content
        """
        logger.info("event=visit_url_start url=%s", url[:80])
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Get title
            title = soup.title.string if soup.title else "No title"
            
            # Limit text length
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
        """
        Extract specific text from a URL using CSS selector
        
        Args:
            url: URL to extract from
            selector: CSS selector for specific content
            
        Returns:
            Dictionary with extracted text
        """
        logger.info("event=extract_text_start url=%s selector=%s", url[:80], selector)
        
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
        """
        Crawl a website and extract links
        
        Args:
            domain: Domain to crawl
            max_pages: Maximum pages to crawl
            
        Returns:
            Dictionary with crawled data
        """
        logger.info("event=crawl_site_start domain=%s max_pages=%s", domain, max_pages)
        
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
                    
                    # Extract links
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
        """
        Get news articles about a topic
        
        Args:
            topic: Topic to search news for
            count: Number of results
            
        Returns:
            Dictionary with news results
        """
        if not BRAVE_API_KEY:
            logger.warning("event=get_news_no_api_key")
            return {"success": False, "error": "BRAVE_API_KEY not configured"}
        
        logger.info("event=get_news_start topic=%s count=%s", topic, count)
        
        try:
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": BRAVE_API_KEY
            }
            
            params = {
                "q": topic,
                "count": min(count, 20)
            }
            
            response = requests.get(
                f"{BRAVE_API_BASE}/news/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error("event=get_news_failed status=%s", response.status_code)
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}"
                }
            
            data = response.json()
            results = []
            
            for article in data.get("results", []):
                results.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "description": article.get("description", ""),
                    "source": article.get("source", ""),
                    "published": article.get("published", ""),
                    "type": "news"
                })
            
            logger.info("event=get_news_success topic=%s results=%s", topic, len(results))
            
            return {
                "success": True,
                "topic": topic,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            logger.error("event=get_news_exception error=%s", str(e))
            return {"success": False, "error": str(e)}


# Tool registry for agent use
AVAILABLE_TOOLS = {
    "web_search": {
        "func": WebSearchTools.web_search,
        "description": "Search the web for information",
        "params": {
            "query": "str - search query",
            "count": "int - number of results (max 20)"
        }
    },
    "visit_url": {
        "func": WebSearchTools.visit_url,
        "description": "Visit a URL and extract text content",
        "params": {
            "url": "str - URL to visit"
        }
    },
    "extract_text": {
        "func": WebSearchTools.extract_text,
        "description": "Extract specific text from a URL",
        "params": {
            "url": "str - URL to extract from",
            "selector": "str - CSS selector (optional)"
        }
    },
    "crawl_site": {
        "func": WebSearchTools.crawl_site,
        "description": "Crawl a website and extract links",
        "params": {
            "domain": "str - domain to crawl",
            "max_pages": "int - maximum pages to crawl"
        }
    },
    "get_news": {
        "func": WebSearchTools.get_news,
        "description": "Get news articles about a topic",
        "params": {
            "topic": "str - topic to search",
            "count": "int - number of results"
        }
    }
}
