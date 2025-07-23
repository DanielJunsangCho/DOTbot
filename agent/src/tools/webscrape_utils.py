from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup

@tool
def url_handler(url: str) -> str:
    """
    Pulls the HTML content from the URL
    Args: 
        url: url string.
    Returns:
        the content of the HTML in string.
    """

    r = requests.get(url)
    r = r.text
    soup = BeautifulSoup(r, 'html.parser')

    return str(soup)

