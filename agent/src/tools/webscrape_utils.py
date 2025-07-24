from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup

@tool
def url_handler(url: str) -> str:
    """
    Extracts structured information from a website including headers, links, text, and other important content
    while preserving the website's structure.
    Args: 
        url: url string.
    Returns:
        A structured string containing all important website information.
    """
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Extract structured information
        structured_content = extract_structured_content(soup)
        print(structured_content)
        return structured_content
        
    except requests.RequestException as e:
        return f"Error fetching URL: {str(e)}"
    except Exception as e:
        return f"Error processing content: {str(e)}"

def extract_structured_content(soup):
    """
    Extracts content while preserving document structure and header-content relationships
    """
    content = []
    
    # Extract page title and meta
    title = soup.find('title')
    if title:
        content.append(f"TITLE: {title.get_text().strip()}")
    
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        content.append(f"DESCRIPTION: {meta_desc['content'].strip()}")
    
    content.append("\n" + "="*50)
    content.append("WEBSITE CONTENT (preserving structure)")
    content.append("="*50)
    
    # Remove script and style elements early
    for script in soup(["script", "style", "nav", "footer", "aside"]):
        script.decompose()
    
    # Find main content area
    main_content = soup.find('main') or soup.find('article') or soup.body or soup
    
    if main_content:
        content.extend(process_element_with_structure(main_content))
    
    return '\n'.join(content)

def process_element_with_structure(element, level=0, processed_elements=None):
    """
    Recursively process elements while preserving structure and header-content relationships
    """
    if processed_elements is None:
        processed_elements = set()
    
    # Avoid processing the same element twice
    if id(element) in processed_elements:
        return []
    processed_elements.add(id(element))
    
    content = []
    indent = "  " * level
    
    # Process direct children in document order
    for child in element.children:
        if hasattr(child, 'name') and child.name:
            tag_name = child.name.lower()
            
            # Handle headers with their content
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                header_level = int(tag_name[1])
                header_indent = "  " * (header_level - 1)
                header_text = child.get_text().strip()
                if header_text:
                    content.append(f"\n{header_indent}{'#' * header_level} {header_text}")
                    
                    # Find content that follows this header
                    following_content = get_content_after_header(child)
                    if following_content:
                        for line in following_content:
                            if line.strip():
                                content.append(f"{header_indent}  {line}")
            
            # Handle paragraphs
            elif tag_name == 'p':
                text = child.get_text().strip()
                if text:
                    content.append(f"{indent}{text}")
            
            # Handle lists
            elif tag_name in ['ul', 'ol']:
                list_items = child.find_all('li', recursive=False)
                if list_items:
                    content.append(f"{indent}[{tag_name.upper()} LIST]")
                    for i, item in enumerate(list_items):
                        marker = "•" if tag_name == 'ul' else f"{i+1}."
                        item_text = item.get_text().strip()
                        
                        # Look for links within the list items
                        links_in_item = item.find_all('a', href=True)
                        if item_text:
                            if links_in_item:
                                # Handle multiple links in a single list item
                                if len(links_in_item) == 1:
                                    # One link in the item
                                    href = links_in_item[0]['href']
                                    content.append(f"{indent}  {marker} {item_text} -> {href}")
                                else:
                                    # Multiple links in one item
                                    content.append(f"{indent}  {marker} {item_text}")
                                    for link in links_in_item:
                                        link_text = link.get_text().strip()
                                        content.append(f"{indent}    - {link_text} -> {link['href']}")
                            else:
                                # No links in this item
                                content.append(f"{indent}  {marker} {item_text}")
            
            # Handle tables
            elif tag_name == 'table':
                content.append(f"{indent}[TABLE]")
                rows = child.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_text = " | ".join([cell.get_text().strip() for cell in cells])
                        if row_text.strip():
                            content.append(f"{indent}  {row_text}")
            
            # Handle links
            elif tag_name == 'a' and child.get('href'):
                link_text = child.get_text().strip()
                if link_text:
                    content.append(f"{indent}[LINK] {link_text} -> {child['href']}")
            
            # Handle images
            elif tag_name == 'img':
                alt_text = child.get('alt', 'Image')
                src = child.get('src', 'No source')
                content.append(f"{indent}[IMAGE] {alt_text} ({src})")
            
            # Handle divs and sections by recursing
            elif tag_name in ['div', 'section', 'article', 'main']:
                child_content = process_element_with_structure(child, level, processed_elements)
                content.extend(child_content)
            
            # Handle other text-containing elements
            elif tag_name not in ['script', 'style', 'nav', 'footer', 'aside', 'header']:
                text = child.get_text().strip()
                if text and len(text) > 10:  # Only include substantial text
                    content.append(f"{indent}{text}")
        
        # Handle direct text nodes
        elif hasattr(child, 'strip'):
            text = child.strip()
            if text and len(text) > 5:
                content.append(f"{indent}{text}")
    
    return content

def get_content_after_header(header_element):
    """
    Get content that logically follows a header element
    """
    content = []
    current = header_element.next_sibling
    
    while current:
        if hasattr(current, 'name') and current.name:
            # Stop at next header of same or higher level
            if current.name.lower() in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                current_level = int(current.name[1])
                header_level = int(header_element.name[1])
                if current_level <= header_level:
                    break
            
            # Get text from paragraphs, divs, etc.
            if current.name.lower() in ['p', 'div', 'span']:
                text = current.get_text().strip()
                if text and len(text) > 10:
                    content.append(text)
        
        elif hasattr(current, 'strip'):
            text = current.strip()
            if text and len(text) > 5:
                content.append(text)
        
        current = current.next_sibling
    
    return content


url_handler("https://www.scrapethissite.com/pages/forms/")