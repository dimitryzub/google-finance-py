from itertools import zip_longest   # https://docs.python.org/3/library/itertools.html#itertools.zip_longest
import nasdaqdatalink               # https://docs.data.nasdaq.com/docs/python-installation
import requests, json, re
from parsel import Selector


def nasdaq_get_timeseries_data():
    nasdaqdatalink.read_key(filename=".nasdaq_api_key") # create .env (.your_file_name) file locally and paste your Nasdaq API key.
    # print(nasdaqdatalink.ApiConfig.api_key) # prints api key from the .nasdaq_api_key

    timeseries_data = nasdaqdatalink.get("WIKI/GOOGL", collapse="monthly") # not sure what "WIKI" stands for
    print(timeseries_data)

# nasdaq_get_timeseries_data()

def scrape_google_finance(ticker: str):
    # https://docs.python-requests.org/en/master/user/quickstart/#passing-parameters-in-urls
    params = {
        "hl": "en" # language
        }

    # https://docs.python-requests.org/en/master/user/quickstart/#custom-headers
    # https://www.whatismybrowser.com/detect/what-is-my-user-agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36",
        }

    html = requests.get(f"https://www.google.com/finance/quote/{ticker}", params=params, headers=headers, timeout=30)
    selector = Selector(text=html.text)
    
    # where all extracted data will be temporary located
    ticker_data = {
        "ticker_data": {},
        "about_panel": {},
        "news": {"items": []},
        "finance_perfomance": {"table": []}, 
        "people_also_search_for": {"items": []},
        "interested_in": {"items": []}
    }
    
    # current price, quote, title extraction
    ticker_data["ticker_data"]["current_price"] = selector.css(".AHmHk .fxKbKc::text").get()
    ticker_data["ticker_data"]["quote"] = selector.css(".PdOqHc::text").get().replace(" • ",":")
    ticker_data["ticker_data"]["title"] = selector.css(".zzDege::text").get()
    
    # about panel extraction
    about_panel_keys = selector.css(".gyFHrc .mfs7Fc::text").getall()
    about_panel_values = selector.css(".gyFHrc .P6K39c").xpath("normalize-space()").getall()
    
    for key, value in zip_longest(about_panel_keys, about_panel_values):
        key_value = key.lower().replace(" ", "_")
        ticker_data["about_panel"][key_value] = value
    
    # description "about" extraction
    ticker_data["about_panel"]["description"] = selector.css(".bLLb2d::text").get()
    ticker_data["about_panel"]["extensions"] = selector.css(".w2tnNd::text").getall()
    
    # news extarction
    if selector.css(".yY3Lee").get():
        for index, news in enumerate(selector.css(".yY3Lee"), start=1):
            ticker_data["news"]["items"].append({
                "position": index,
                "title": news.css(".Yfwt5::text").get(),
                "link": news.css(".z4rs2b a::attr(href)").get(),
                "source": news.css(".sfyJob::text").get(),
                "published": news.css(".Adak::text").get(),
                "thumbnail": news.css("img.Z4idke::attr(src)").get()
            })
    else: 
        ticker_data["news"]["error"] = f"No news result from a {ticker}."

    # finance perfomance table
    if selector.css(".slpEwd .roXhBd").get():
        fin_perf_col_2 = selector.css(".PFjsMe+ .yNnsfe::text").get()           # e.g. Dec 2021
        fin_perf_col_3 = selector.css(".PFjsMe~ .yNnsfe+ .yNnsfe::text").get()  # e.g. Year/year change
        
        for fin_perf in selector.css(".slpEwd .roXhBd"):
            if fin_perf.css(".J9Jhg::text , .jU4VAc::text").get():
                
                """
                if fin_perf.css().get() statement is needed, otherwise first value in a dict would be None:
                
                "finance_perfomance": {
                "table": [
                    {
                    "null": {
                        "Dec 2021": null,
                        "Year/year change": null
                    }
                }
                """             
                
                perf_key = fin_perf.css(".J9Jhg::text , .jU4VAc::text").get()   # e.g. Revenue, Net Income, Operating Income..
                perf_value_col_1 = fin_perf.css(".QXDnM::text").get()           # 60.3B, 26.40%..   
                perf_value_col_2 = fin_perf.css(".gEUVJe .JwB6zf::text").get()  # 2.39%, -21.22%..
                
                ticker_data["finance_perfomance"]["table"].append({
                    perf_key: {
                        fin_perf_col_2: perf_value_col_1, # dynamically add key and value from the second (2) column
                        fin_perf_col_3: perf_value_col_2  # dynamically add key and value from the third (3) column
                    }
                })
    else:
        ticker_data["finance_perfomance"]["error"] = f"No 'finence perfomance table' for {ticker}."
    
    # "you may be interested in" results
    if selector.css(".HDXgAf .tOzDHb").get():
        for index, other_interests in enumerate(selector.css(".HDXgAf .tOzDHb"), start=1):
            ticker_data["interested_in"]["items"].append(discover_more_tickers(index, other_interests))
    else:
        ticker_data["interested_in"]["error"] = f"No 'you may be interested in` results for {ticker}"
    
    
    # "people also search for" results
    if selector.css(".HDXgAf+ div .tOzDHb").get():
        for index, other_tickers in enumerate(selector.css(".HDXgAf+ div .tOzDHb"), start=1):
            ticker_data["people_also_search_for"]["items"].append(discover_more_tickers(index, other_tickers))
    else:
        ticker_data["people_also_search_for"]["error"] = f"No 'people_also_search_for` in results for {ticker}"
        

    return ticker_data


def discover_more_tickers(index: int, other_data: str):
    """
    if price_change_formatted will start complaining,
    check beforehand for None values with try/except and set it to 0, in this function.
    
    however, re.search(r"\d{1}%|\d{1,10}\.\d{1,2}%" should make the job done.
    """
    return {
            "position": index,
            "ticker": other_data.css(".COaKTb::text").get(),
            "ticker_link": f'https://www.google.com/finance{other_data.attrib["href"].replace("./", "/")}',
            "title": other_data.css(".RwFyvf::text").get(),
            "price": other_data.css(".YMlKec::text").get(),
            "price_change": other_data.css("[jsname=Fe7oBc]::attr(aria-label)").get(),
            # https://regex101.com/r/BOFBlt/1
            # Up by 100.99% -> 100.99%
            "price_change_formatted": re.search(r"\d{1}%|\d{1,10}\.\d{1,2}%", other_data.css("[jsname=Fe7oBc]::attr(aria-label)").get()).group()
        }
    

data = scrape_google_finance(ticker="GOOGL:NASDAQ")
print(json.dumps(data, indent=2, ensure_ascii=False))

# iterate over multiple tickers
# for ticker in ["DAX:INDEXDB", "GOOGL:NASDAQ", "MSFT:NASDAQ"]:
#     data = scrape_google_finance(ticker=ticker)
#     print(json.dumps(data["ticker_data"], indent=2, ensure_ascii=False))
