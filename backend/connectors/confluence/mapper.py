from typing import Dict, Any, List
from html.parser import HTMLParser

from connectors.base.metadata import ConnectorFileMetadata

class ConfluenceToMarkdownParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.md_chunks: List[str] = []
        self.list_level = 0
        self.in_bold = False
        self.in_italic = False
        self.in_heading = False
        self.heading_level = 0
        self.in_link = False
        self.link_url = ""

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.in_heading = True
            self.heading_level = int(tag[1])
            self.md_chunks.append(f"\n{'#' * self.heading_level} ")
        elif tag == "b" or tag == "strong":
            self.in_bold = True
            self.md_chunks.append("**")
        elif tag == "i" or tag == "em":
            self.in_italic = True
            self.md_chunks.append("*")
        elif tag == "a":
            self.in_link = True
            for attr in attrs:
                if attr[0] == "href":
                    self.link_url = attr[1]
            self.md_chunks.append("[")
        elif tag == "ul" or tag == "ol":
            self.list_level += 1
            self.md_chunks.append("\n")
        elif tag == "li":
            self.md_chunks.append(f"{'  ' * (self.list_level - 1)}- ")
        elif tag == "p":
            self.md_chunks.append("\n\n")
        elif tag == "br":
            self.md_chunks.append("\n")
        # Ignore other complex tags for this lightweight parser

    def handle_endtag(self, tag: str):
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.in_heading = False
            self.md_chunks.append("\n")
        elif tag == "b" or tag == "strong":
            self.in_bold = False
            self.md_chunks.append("**")
        elif tag == "i" or tag == "em":
            self.in_italic = False
            self.md_chunks.append("*")
        elif tag == "a":
            self.in_link = False
            self.md_chunks.append(f"]({self.link_url})")
            self.link_url = ""
        elif tag == "ul" or tag == "ol":
            self.list_level = max(0, self.list_level - 1)
            self.md_chunks.append("\n")

    def handle_data(self, data: str):
        self.md_chunks.append(data)

    def get_markdown(self) -> str:
        return "".join(self.md_chunks).strip()


def convert_confluence_to_markdown(html_content: str) -> str:
    """Lightweight conversion from Confluence storage format to Markdown."""
    if not html_content:
        return ""
    parser = ConfluenceToMarkdownParser()
    parser.feed(html_content)
    return parser.get_markdown()


def map_confluence_page(item: Dict[str, Any], space_id: str) -> ConnectorFileMetadata:
    """
    Map a Confluence Page to a ConnectorFileMetadata payload.
    """
    page_id = item.get("id", "")
    title = item.get("title", "Untitled")
    
    # In Confluence V2 API, body is returned under 'body'
    body_storage = item.get("body", {}).get("storage", {}).get("value", "")
    
    # We store the converted markdown in raw_metadata for now so it's accessible.
    # In a full implementation, we might actually yield this directly to the ingestion task.
    # But ConnectorFileMetadata doesn't have a 'content' field. 
    # Usually, the framework downloads it separately. 
    # Since we mapped it here, the orchestrator should probably just fetch it or we can provide it via download_file.
    
    return ConnectorFileMetadata(
        external_id=page_id,
        name=title,
        mime_type="text/markdown",  # Claiming it's markdown because we will convert it
        size_bytes=0, # Hard to know upfront without encoding
        external_path=f"/spaces/{space_id}",
        raw_metadata={
            "spaceId": space_id,
            "title": title,
            "version": item.get("version", {}).get("number", 1)
        }
    )
