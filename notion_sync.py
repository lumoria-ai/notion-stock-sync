import requests
import os
import time

# Read API keys from environment variables
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_notion_database_entries():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    data = response.json()

    companies = []
    for page in data.get("results", []):
        properties = page["properties"]
        company_name = properties.get("Company Name", {}).get("title", [])
        
        if company_name:
            company_text = company_name[0]["text"]["content"]
            companies.append((page["id"], company_text, properties))

    return companies

def get_stock_symbol_all_countries(company_name):
    url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={company_name}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    matches = data.get("bestMatches", [])
    results = {}

    for match in matches:
        symbol = match["1. symbol"]
        market = match.get("4. region", "")
        results[market] = symbol  

    return results

def update_notion_entry(page_id, stock_symbols, existing_properties):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    update_data = {"properties": {}}
    
    for exchange, symbol in stock_symbols.items():
        if exchange in existing_properties:
            update_data["properties"][exchange] = {"rich_text": [{"text": {"content": symbol}}]}
        else:
            add_new_column_to_notion_database(exchange)
            update_data["properties"][exchange] = {"rich_text": [{"text": {"content": symbol}}]}

    requests.patch(url, headers=HEADERS, json=update_data)

def add_new_column_to_notion_database(column_name):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
    data = {"properties": {column_name: {"type": "rich_text", "rich_text": {}}}}
    requests.patch(url, headers=HEADERS, json=data)

def main():
    print("Fetching Notion entries...")
    companies = get_notion_database_entries()

    for page_id, company_name, properties in companies:
        print(f"Processing: {company_name}")
        stock_symbols = get_stock_symbol_all_countries(company_name)

        if stock_symbols:
            print(f"Updating Notion with symbols: {stock_symbols}")
            update_notion_entry(page_id, stock_symbols, properties)
        else:
            print(f"No symbols found for {company_name}")

        time.sleep(1)

if __name__ == "__main__":
    main()
