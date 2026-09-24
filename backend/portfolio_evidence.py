"""Safe, deterministic evidence extraction from candidate-owned public portfolios."""

import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


class PortfolioVerificationError(Exception):
    pass


class _PageText(HTMLParser):
    def __init__(self):
        super().__init__(); self.title = []; self.text = []; self.links = []; self._in_title = False
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "title": self._in_title = True
        if tag == "a" and values.get("href"): self.links.append(values["href"])
    def handle_endtag(self, tag):
        if tag == "title": self._in_title = False
    def handle_data(self, data):
        value = " ".join(data.split())
        if value:
            self.text.append(value)
            if self._in_title: self.title.append(value)


def _public_host(hostname):
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, None)}
    except socket.gaierror as exc:
        raise PortfolioVerificationError("Portfolio domain could not be resolved.") from exc
    if not addresses:
        return False
    return all(not (ipaddress.ip_address(address).is_private or ipaddress.ip_address(address).is_loopback
                    or ipaddress.ip_address(address).is_link_local or ipaddress.ip_address(address).is_reserved)
               for address in addresses)


def verify_portfolio(url, claimed_skills):
    parsed = urlparse(str(url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or not _public_host(parsed.hostname):
        raise PortfolioVerificationError("Enter a publicly reachable HTTP or HTTPS portfolio URL.")
    request = Request(url, headers={"User-Agent": "TalentVerify/2.0", "Accept": "text/html,application/xhtml+xml"})
    try:
        with urlopen(request, timeout=8) as response:
            final_url = response.geturl(); final = urlparse(final_url)
            if not final.hostname or not _public_host(final.hostname):
                raise PortfolioVerificationError("Portfolio redirected to a private or unsafe address.")
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "application/xhtml+xml"}:
                raise PortfolioVerificationError("Portfolio URL must return an HTML page.")
            body = response.read(1_000_001)
            if len(body) > 1_000_000: raise PortfolioVerificationError("Portfolio page is too large to inspect safely.")
    except HTTPError as exc:
        raise PortfolioVerificationError(f"Portfolio returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise PortfolioVerificationError("Portfolio could not be reached.") from exc
    parser = _PageText(); parser.feed(body.decode("utf-8", errors="replace"))
    page_text = " ".join(parser.text)[:200_000]
    folded = page_text.casefold()
    matches = []
    for skill in dict.fromkeys(str(item).strip() for item in claimed_skills if str(item).strip()):
        if re.search(rf"(?<![\w]){re.escape(skill.casefold())}(?![\w])", folded):
            matches.append({"skill": skill, "evidence": f"'{skill}' appears in the public portfolio page content.", "source_url": final_url})
    external_links = list(dict.fromkeys(urljoin(final_url, link) for link in parser.links if link.startswith(("http://", "https://"))))[:25]
    return {"portfolio_url": final_url, "verification_status": "verified_content", "page_title": " ".join(parser.title)[:300],
            "matched_skills": matches, "external_links": external_links, "content_length": len(body)}
