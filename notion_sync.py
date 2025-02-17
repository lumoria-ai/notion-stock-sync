import requests
import os
import time

NOTION_API_KEY = "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"
DATABASE_ID = "19db72583bf18038b925e277ed74ac76"
ALPHA_VANTAGE_API_KEY = "UW1MQZEWJFAJ986P"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_notion_database_entries():
    """Fetch all entries from Notion database."""
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
    """Fetch stock symbols from Alpha Vantage for all available countries."""
    url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={company_name}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    matches = data.get("bestMatches", [])
    results = {}

    for match in matches:
        symbol = match["1. symbol"]
        market = match.get("4. region", "")  # Country/Region
        exchange = match.get("3. type", "Stock")  # Could be ETF, Crypto, etc.

        # Example: "TSXV" or "NASDAQ"
        results[market] = symbol  

    return results  # Returns a dictionary { "TSXV": "SHOP.V", "NASDAQ": "SHOP" }

def update_notion_entry(page_id, stock_symbols, existing_properties):
    """Update Notion database with stock symbols, adding columns if needed."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    # Prepare the properties dictionary
    update_data = {"properties": {}}
    
    for exchange, symbol in stock_symbols.items():
        # Check if the column already exists
        if exchange in existing_properties:
            # Update existing column
            update_data["properties"][exchange] = {
                "rich_text": [{"text": {"content": symbol}}]
            }
        else:
            # Create a new column dynamically
            add_new_column_to_notion_database(exchange)
            update_data["properties"][exchange] = {
                "rich_text": [{"text": {"content": symbol}}]
            }

    response = requests.patch(url, headers=HEADERS, json=update_data)
    return response.status_code == 200

def add_new_column_to_notion_database(column_name):
    """Dynamically add a new column to the Notion database."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
    
    data = {
        "properties": {
            column_name: {
                "type": "rich_text",
                "rich_text": {}
            }
        }
    }

    response = requests.patch(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        print(f"Added new column: {column_name}")
    else:
        print(f"Failed to add column: {column_name}, Response: {response.text}")

def main():
    """Main function to fetch, process, and update Notion database."""
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

        time.sleep(1)  # Avoid hitting API rate limits

if __name__ == "__main__":
    main()
