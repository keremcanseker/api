import os
from dotenv import load_dotenv
from supabase import create_client, Client
from fastapi import FastAPI , Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup

import requests 
import json

load_dotenv()
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")


supabase: Client = create_client(url, key)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("api is running")
def scrape_page(url: str, page: int):
    url_with_page = f"{url}&search_result={page}"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch, br",
            "Accept-Language": "en-US,en;q=0.8",
            
        }
        request = requests.get(url_with_page, headers=headers)
     
        # print(request.content)
        soup = BeautifulSoup(request.content, 'html.parser')

        div_elements = soup.find_all('div', {'data-test-id': 'search-result-item'})

        # Extract the href URLs from the div elements and transform them
        href_urls = []
        for div in div_elements:
            a = div.find('a', {'data-test-id': 'object-image-link'})
            if a:
                href_url = a['href']
                # Remove the "/detail" part from the URL
                href_url = href_url.replace('/detail', '')
                parts = href_url.split("/")
                # Find the street name and house number
                street_name_house_number_elem = div.find('h2', {'data-test-id': 'street-name-house-number'})
                if street_name_house_number_elem:
                    street_name_house_number = street_name_house_number_elem.text.strip()
                    street_name, house_number = street_name_house_number.rsplit(' ', 1)
                    # Format street name to lowercase and replace spaces with hyphens
                    street_name = street_name.lower().replace(' ', '-')
                    # Construct the modified URL
                    transformed_url = f"https://www.funda.nl/{parts[3]}/{parts[4]}/huis-{parts[-2]}-{street_name}-{house_number}/reageer/"
                    href_urls.append(transformed_url)
        print(href_urls)
        return href_urls
        # print(request.headers)
        # print(request.cookies)
        # print(request.request.headers)
        # print(request.request._cookies)
        # print(request.request.body)
    


    except Exception as e:
        print("patladi")
        print(e)
        return {"error": str(e)}


@app.get("/",response_class=HTMLResponse)
async def root():
    html_content = """
                <!DOCTYPE html>
            <html>
            <head>
                <title>Scrape Website</title>
                <style>
                body {
                    background-color: #2b384b;
                    font-family: Arial, sans-serif;

                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    width: 100vw;
                }
                h1 {
                    color: white;
                    font-size: 2em;
                    text-align: center;
                }
                </style>
            </head>
            <body>
                <h1>Welcome to rental house api</h1>
            </body>
            </html>
    """
    return HTMLResponse(content=html_content, status_code=200)  
  

@app.post("/send-request")
async def scrape_website(request: Request):
    # Get the URL from the request body
    body = await request.body()
    
    url = body.decode("utf-8")  # Decode bytes to string
    data = json.loads(url)

    if not isinstance(data, dict):
        # Convert data to a dictionary if it's not already
        data = dict(data)

    url_value = data.get("url")
    user_value = data.get("user")
    email_value = data.get("email")
    print(url_value)
    print(user_value)
    print(email_value)
    # urls that are successfully send
    sent_urls = []
    # Scrape the first and second pages
    for page_number in range(1, 3):
        href_urls = scrape_page(url_value, page_number)

        # Send post req uest to each link
        for href_url in href_urls:
            try:
                # Check if the URL has already been processed for the current user
                existing_urls = supabase.table("urls").select("url").eq("user", user_value).execute()
              

                #  if existing urls is empty
                if not existing_urls.data:
                    print("No existing URLs found for the user.")
                else:
                    existing_urls = [entry["url"] for entry in existing_urls.data if entry.get("url")]
                

                if href_url in existing_urls:
                    print(f"URL {href_url} already processed for user {user_value}. Skipping...")
                    continue

                get_headers ={
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br, zstd',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                    'X-Requested-With': 'XMLHttpRequest',
                }
                print(href_url)
                initial_response = requests.get(href_url,headers=get_headers)

                initial_cookies = initial_response.cookies
                cookies_dict = requests.utils.dict_from_cookiejar(initial_cookies)

                soup = BeautifulSoup(initial_response.text, 'html.parser')
                verification_token_input = soup.find('input', attrs={'name': '__RequestVerificationToken'})
                verification_token = verification_token_input['value']

                path = href_url.split("funda.nl")[1]
                post_headers = {
                    "Authority": "www.funda.nl",
                    "Method": "POST",
                    "Path": path,
                    "Scheme": "https",
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br, zstd',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Cookie': '; '.join([f'{k}={v}' for k, v in cookies_dict.items()]),
                    'Origin': 'https://www.funda.nl',
                    'Referer': href_url,
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Gpc': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/',
                    'X-Requested-With': 'XMLHttpRequest',
                }
                payload = {
                    "__RequestVerificationToken": verification_token,
                   "Opmerking": "Hello, i want to see this properity.",
                    "Email": email_value,
                    "Telefoon": "+905306423444",
                    "Aanhef": "Dhr",
                    "Voornaam": "Kemal",
                    "Achternaam": "Sezen",
                }

                post_url = href_url
                request = requests.post(post_url,headers=post_headers,data=payload)
                
                # if request is successful,save url to database
                if request.status_code == 200:
                    print("request is successful")
                    print(request)
                    sent_urls.append(href_url)
                    data = {
                        "url": href_url,
                        "user": user_value
                    }
                    supabase.table("urls").insert(data).execute()
                else:
                    print("a request failed")
                    print(request)

            except Exception as e:
                print(f"An error occurred while sending request to {href_url}: {e}")
                continue

    return {"message": "success", "sent_urls": sent_urls}
