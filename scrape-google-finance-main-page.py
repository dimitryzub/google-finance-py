import requests, json, re
from parsel import Selector


def scrape_google_finance_main_page():
    # https://docs.python-requests.org/en/master/user/quickstart/#custom-headers
    # https://www.whatismybrowser.com/detect/what-is-my-user-agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Safari/537.36"
        }

    html = requests.get(f"https://www.google.com/finance/", headers=headers, timeout=30)
    selector = Selector(text=html.text)

    # where all extracted data will be temporary located
    ticker_data = {
        "market_trends": {
            "top_position": [],
            "bottom_position": []
        },
        "interested_in": {
            "top_position": [],
            "bottom_position": []
        },
        "earning_calendar": [],
        "most_followed_on_google": [],
        "news": [],
    }

    # Market trends top results
    ticker_data["market_trends"]["top_position"] = selector.css(".gR2U6::text").getall()
    
    # Earnings calendar results
    for calendar_quote in selector.css(".d3fRjc"):
        ticker_data["earning_calendar"].append({
            "quote": calendar_quote.css(".yaubCc::text").get(),
            "quote_link": f'https://www.google.com/finance/quote{calendar_quote.css(".yaubCc::attr(href)").get().replace("./quote/", "/")}',
            "short_date": calendar_quote.css(".JiAI5b").xpath("normalize-space()").get(),
            "full_date": calendar_quote.css(".fVovwd::text").get()
        })

    # Most followed on Google results
    for google_most_followed in selector.css(".NaLFgc"):
        current_percent_change_raw_value = google_most_followed.css("[jsname=Fe7oBc]::attr(aria-label)").get()
        current_percent_change = re.search(r"by\s?(\d+\.\d+)%", google_most_followed.css("[jsname=Fe7oBc]::attr(aria-label)").get()).group(1)

        ticker_data["most_followed_on_google"].append({
            "title": google_most_followed.css(".TwnKPb::text").get(),
            "quote": re.search(r"\.\/quote\/(\w+):",google_most_followed.attrib["href"]).group(1),            # https://regex101.com/r/J3DDIX/1
            "following": re.search(r"(\d+\.\d+)M", google_most_followed.css(".Iap8Fc::text").get()).group(1), # https://regex101.com/r/7ptVha/1
            "percent_price_change": f"+{current_percent_change}" if "Up" in current_percent_change_raw_value else f"-{current_percent_change}"
        })

    # news results. If empty -> run once again. For some reason it could return [].
    for index, news in enumerate(selector.css(".yY3Lee"), start=1):
        ticker_data["news"].append({
            "position": index,
            "title": news.css(".Yfwt5::text").get(),
            "link": news.css(".z4rs2b a::attr(href)").get(),
            "source": news.css(".sfyJob::text").get(),
            "published": news.css(".Adak::text").get(),
            "thumbnail": news.css("img.Z4idke::attr(src)").get()
        })

    # "you may be interested in" at the top of the page results
    for index, interested_top in enumerate(selector.css(".sbnBtf:not(.xJvDsc) .SxcTic"), start=1):
        current_percent_change_raw_value = interested_top.css("[jsname=Fe7oBc]::attr(aria-label)").get()
        current_percent_change = re.search(r"\d{1}%|\d{1,10}\.\d{1,2}%", interested_top.css("[jsname=Fe7oBc]::attr(aria-label)").get()).group()

        ticker_data["interested_in"]["top_position"].append({
            "index": index,
            "title": interested_top.css(".ZvmM7::text").get(),
            "quote": interested_top.css(".COaKTb::text").get(),
            "price_change": interested_top.css(".SEGxAb .P2Luy::text").get(),
            "percent_price_change": f"+{current_percent_change}" if "Up" in current_percent_change_raw_value else f"-{current_percent_change}"
        })

    # market trends bottom
    for index, market_trend in enumerate(selector.css("[jscontroller=mBF9u]"), start=1):
        current_percent_change_raw_value = interested_top.css("[jsname=Fe7oBc]::attr(aria-label)").get()
        current_percent_change = re.search(r"\d{1}%|\d{1,10}\.\d{1,2}%", interested_top.css("[jsname=Fe7oBc]::attr(aria-label)").get()).group()

        ticker_data["market_trends"]["bottom_position"].append({
            "index": index,
            "title": market_trend.css(".ZvmM7::text").get(),
            "quote": market_trend.css(".COaKTb::text").get(),
            "price": market_trend.css(".YMlKec::text").get(),
            "price_percent_change": f"+{current_percent_change}" if "Up" in current_percent_change_raw_value else f"-{current_percent_change}"
        })

    # "you may be interested in" at the bottom of the page results
    for index, interested_bottom in enumerate(selector.css(".HDXgAf .tOzDHb"), start=1):
        # single function to handle both top and bottom 
        # "you may be interested results" as selectors is identical

        current_percent_change_raw_value = interested_bottom.css("[jsname=Fe7oBc]::attr(aria-label)").get()
        current_percent_change = re.search(r"\d{1}%|\d{1,10}\.\d{1,2}%", interested_bottom.css("[jsname=Fe7oBc]::attr(aria-label)").get()).group()

        ticker_data["interested_in"]["bottom_position"].append({
            "position": index,
            "ticker": interested_bottom.css(".COaKTb::text").get(),
            "ticker_link": f'https://www.google.com/finance{interested_bottom.attrib["href"].replace("./", "/")}',
            "title": interested_bottom.css(".RwFyvf::text").get(),
            "price": interested_bottom.css(".YMlKec::text").get(),
            "percent_price_change": f"+{current_percent_change}" if "Up" in current_percent_change_raw_value else f"-{current_percent_change}"
        })

    return ticker_data


# scrape_google_finance_main_page()
print(json.dumps(scrape_google_finance_main_page(), indent=2, ensure_ascii=False))
