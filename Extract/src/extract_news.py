import requests

def fetch_news_articles(api_key, query):
    """
    Fetch news articles based on a given query term from the News API.

    Args:
        api_key (str): Your News API key.
        query (str): The search term to query articles for.

    Returns:
        list: A list of article titles.
    """
    # Construct the API URL
    url = f'https://newsapi.org/v2/everything?q={query}&apiKey={api_key}'

    # Fetch articles
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return [article['title'] for article in data['articles']]
    else:
        print("Error fetching articles:", response.status_code, response.text)
        return []
