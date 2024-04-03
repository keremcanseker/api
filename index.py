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

        # Find all a elements with the specified data-test-id attribute
        a_elements = soup.find_all('a', {'data-test-id': 'object-image-link'})

        # Extract the href URLs from the a elements
        href_urls = [a['href'] for a in a_elements]

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

    url_value = data.get("url")
    user_value = data.get("user")
    print(url_value)
    print(user_value)


    
 

    # Scrape the first page
    href_urls_page1 = scrape_page(url_value, 1)
    href_urls_page2 = scrape_page(url_value, 2)

    ## send post request to each link

    for href_url in href_urls_page1:
        # payload = {
        #     "Opmerking": """ Geachte heer/mevrouw,
        #     Ik ben Miraç Kaçmaz en werk een jaar als Digital Marketing Manager bij Hairtec Haarkliniek. Samen met mijn werkgever hebben we besloten dat ik als expat in Nederland kom werken voor hem.
        #     Ik ben daarom nu op zoek naar een woning voor alleenstaand gebruik. Mijn werkgever staat volledig garant voor de huur en gaat de huurovereenkomst op hun bedrijf stellen.
        #     Ik verheug me op uw reactie.
        #     Met vriendelijke groet,
        #     Miraç Kaçmaz""",
        #     "Email": "me@mirackacmaz.com",
        #     "Telefoon": "+905527526544",
        #     "Aanhef": "Dhr",
        #     "Voornaam": "Mirac",
        #     "Achternaam": "Kacmaz",
        #     "HypotheekAdviesRequested": "false",
        # }
        payload = {
            "Opmerking": "test",
            "Email": "test@gmail.com",
            "Telefoon": "1234567890",
            "Aanhef": "Dhr",
            "Voornaam": "test",
            "Achternaam": "test",
            "HypotheekAdviesRequested": "false",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.6",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": href_url,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
        }
        try:
            # if url was sent before, do not send again
            existing_urls = supabase.table("urls").select("*").eq("url", href_url).execute()
            if len(existing_urls.data) > 0:
                print("this url exists")
                continue

            request = requests.post(href_url, data=payload, headers=headers)

            # if request is successful,save url to database
            if request.status_code == 200:
                print("request is successful")
                print(request)
                data = {
                    "url": href_url,
                    "user": user_value
                }
                supabase.table("urls").insert(data).execute()
            else:
                print("a request failed")
                print(request)
   


        except Exception as e:
            print("patladi href1")
            print(e)
            return {"error": str(e)}
    for href_url in href_urls_page2:
        payload = {
            "Opmerking": "test",
            "Email": "test@gmail.com",
            "Telefoon": "1234567890",
            "Aanhef": "Dhr",
            "Voornaam": "test",
            "Achternaam": "test",
            "HypotheekAdviesRequested": "false",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.6",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": href_url,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            request = requests.post(href_url, data=payload, headers=headers)
            # if request is successful,save url to database
            if request.status_code == 200:
                print("request is successful")
                print(request)
                data = {
                    "url": href_url,
                    "user": user_value
                }
                supabase.table("urls").insert(data).execute()
            else:
                print("a request failed")
                print(request)
        except Exception as e:
            print("patladi href2 ")
            print(e)
            return {"error": str(e)}
    return {"message": "success"}

     