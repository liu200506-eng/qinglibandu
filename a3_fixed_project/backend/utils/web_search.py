import re
import html
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       'Chrome/125.0 Safari/537.36')

_HEADERS = {
    'User-Agent': _UA,
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def bing_search(query: str, max_results: int = 6, timeout: int = 12) -> List[Dict[str, str]]:
    try:
        r = requests.get(
            'https://cn.bing.com/search',
            params={'q': query, 'setmkt': 'zh-CN', 'FORM': 'HDRSC1'},
            headers=_HEADERS,
            timeout=timeout,
        )
        if r.status_code != 200:
            return []
        text = r.text
    except Exception as e:
        logger.warning('bing_search request failed: %s', e)
        return []

    results: List[Dict[str, str]] = []
    seen = set()
    for m in re.finditer(r'<li class="b_algo"(.*?)</li>', text, re.S):
        block = m.group(1)
        hm = re.search(r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not hm:
            continue
        url = html.unescape(hm.group(1))
        if 'bing.com' in url or url in seen:
            continue
        title = re.sub(r'<.*?>', '', hm.group(2))
        title = html.unescape(title).strip()
        if not title or len(title) < 2:
            continue
        sm = re.search(r'<p[^>]*>(.*?)</p>', block, re.S)
        snippet = ''
        if sm:
            snippet = re.sub(r'<.*?>', ' ', sm.group(1))
            snippet = re.sub(r'\s+', ' ', html.unescape(snippet)).strip()
        seen.add(url)
        results.append({'title': title, 'url': url, 'snippet': snippet})
        if len(results) >= max_results:
            break
    return results


_STRIP_TAGS = re.compile(r'<script.*?</script>', flags=re.S | re.I)
_STRIP_STYLE = re.compile(r'<style.*?</style>', flags=re.S | re.I)
_STRIP_ANY = re.compile(r'<[^>]+>')


def scrape_page(url: str, max_chars: int = 4000, timeout: int = 10) -> Optional[str]:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=timeout, stream=True)
        r.encoding = r.apparent_encoding or r.encoding
        raw = r.text[:200_000]
    except Exception as e:
        logger.warning('scrape_page failed %s: %s', url, e)
        return None

    raw = _STRIP_TAGS.sub(' ', raw)
    raw = _STRIP_STYLE.sub(' ', raw)
    raw = _STRIP_ANY.sub(' ', raw)
    raw = html.unescape(raw)
    raw = re.sub(r'\s+', ' ', raw)

    if len(raw) > max_chars:
        raw = raw[:max_chars] + '…'
    return raw.strip()


def search_and_collect(query: str, max_sources: int = 3) -> List[Dict[str, str]]:
    hits = bing_search(query, max_results=max_sources + 3)
    collected = []
    for h in hits[:max_sources]:
        text = scrape_page(h['url'])
        if not text:
            continue
        collected.append({
            'title': h['title'],
            'url': h['url'],
            'snippet': h['snippet'],
            'content': text,
        })
    return collected
