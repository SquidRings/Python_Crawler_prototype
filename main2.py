import os
import requests
from bs4 import BeautifulSoup
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser

def crawl_and_index(url, index_dir):
    # Define the schema for the index
    schema = Schema(title=TEXT(stored=True), content=TEXT, path=ID(stored=True))

    # Create the index directory if it doesn't exist
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    # Create the index
    ix = create_in(index_dir, schema)

    # Open a writer for the index
    writer = ix.writer()

    # Crawl the website and index the pages
    visited_urls = set()
    urls_to_visit = [url]
    while urls_to_visit:
        current_url = urls_to_visit.pop(0)
        if current_url in visited_urls:
            continue

        print(f"Crawling {current_url}...")
        response = requests.get(current_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string.strip() if soup.title and soup.title.string else ''
            content = soup.get_text().strip()

            # Add the page to the index
            writer.add_document(title=title, content=content, path=current_url)

            # Find all the links in the page
            links = soup.find_all('a')
        
            # Add the links to the list of URLs to visit
            for link in links:
                url = link.get('href')
                if url and url.startswith('http') and url not in visited_urls:
                    urls_to_visit.append(url)
                    visited_urls.add(current_url)

    # Commit the changes and close the writer
    writer.commit()

    # Test the index by searching for a query
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse("python")
        results = searcher.search(query)
        print(f"Found {len(results)} results:")
        for result in results:
            print(result['title'], result.score, result['path'])

if __name__ == '__main__':
    url = input("Enter the URL to crawl: ")
    index_dir = input("Enter the directory to store the index: ")
    crawl_and_index(url, index_dir)
