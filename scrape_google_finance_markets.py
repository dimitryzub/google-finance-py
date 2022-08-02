import requests
import json
import re
import argparse
from parsel import Selector

parser = argparse.ArgumentParser(prog="Google Finance Markets Options")
parser.add_argument('-i','--indexes', action="store_true")
parser.add_argument('-ma','--most-active', action="store_true")
parser.add_argument('-g','--gainers', action="store_true")
parser.add_argument('-l','--losers', action="store_true")
parser.add_argument('-cl','--climate-leaders', action="store_true")
parser.add_argument('-cc','--crypto', action="store_true")
parser.add_argument('-c','--currency', action="store_true")

args = parser.parse_args()

def main():

    # https://docs.python-requests.org/en/master/user/quickstart/#custom-headers
    # https://www.whatismybrowser.com/detect/what-is-my-user-agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Safari/537.36"
    }

    if args.indexes:
        html = requests.get("https://www.google.com/finance/markets/indexes", headers=headers, timeout=30)
        return parser(html=html)

    if args.most_active:
        html = requests.get("https://www.google.com/finance/markets/most-active", headers=headers, timeout=30)
        return parser(html=html)

    if args.gainers:
        html = requests.get("https://www.google.com/finance/markets/gainers", headers=headers, timeout=30)
        return parser(html=html)

    if args.losers:
        html = requests.get("https://www.google.com/finance/markets/losers", headers=headers, timeout=30)
        return parser(html=html)

    if args.climate_leaders:
        html = requests.get("https://www.google.com/finance/markets/climate-leaders", headers=headers, timeout=30)
        return parser(html=html)

    if args.crypto:
        html = requests.get("https://www.google.com/finance/markets/cryptocurrencies", headers=headers, timeout=30)
        return parser(html=html)

    if args.currency:
        html = requests.get("https://www.google.com/finance/markets/currencies", headers=headers, timeout=30)
        return parser(html=html)


def parser(html):
    selector = Selector(text=html.text)
    stock_topic = selector.css(".Mrksgc::text").get().split("on ")[1].replace(" ", "_")

    data = {
        f"{stock_topic}_trends": [],
        f"{stock_topic}_discover_more": [],
        f"{stock_topic}_news": []
    }

    # news ressults
    for index, news_results in enumerate(selector.css(".yY3Lee"), start=1):
        data[f"{stock_topic}_news"].append({
            "position": index,
            "title": news_results.css(".mRjSYb::text").get(),
            "source": news_results.css(".sfyJob::text").get(),
            "date": news_results.css(".Adak::text").get(),
            "image": news_results.css("img::attr(src)").get(),
        })

    # stocks table
    for index, stock_results in enumerate(selector.css("li a"), start=1):
        current_percent_change_raw_value = stock_results.css("[jsname=Fe7oBc]::attr(aria-label)").get()
        current_percent_change = re.search(r"\d+\.\d+%", stock_results.css("[jsname=Fe7oBc]::attr(aria-label)").get()).group()

        # ./quote/SNAP:NASDAQ -> SNAP:NASDAQ
        quote = stock_results.attrib["href"].replace("./quote/", "")

        data[f"{stock_topic}_trends"].append({
            "position": index,
            "title": stock_results.css(".ZvmM7::text").get(),
            "quote": stock_results.css(".COaKTb::text").get(),
            # "https://www.google.com/finance/MSFT:NASDAQ"
            "quote_link": f"https://www.google.com/finance/{quote}",
            "price_change": stock_results.css(".SEGxAb .P2Luy::text").get(),
            "percent_price_change": f"+{current_percent_change}" if "Up" in current_percent_change_raw_value else f"-{current_percent_change}"
        })

    # "you may be interested in" at the bottom of the page
    for index, interested_bottom in enumerate(selector.css(".HDXgAf .tOzDHb"), start=1):
        current_percent_change_raw_value = interested_bottom.css("[jsname=Fe7oBc]::attr(aria-label)").get()
        current_percent_change = re.search(r"\d+\.\d+%", interested_bottom.css("[jsname=Fe7oBc]::attr(aria-label)").get()).group()

        quote = stock_results.attrib["href"].replace("./quote/", "")

        data[f"{stock_topic}_discover_more"].append({
            "position": index,
            "quote": interested_bottom.css(".COaKTb::text").get(),
            "quote_link": f"https://www.google.com/finance{quote}",
            "title": interested_bottom.css(".RwFyvf::text").get(),
            "price": interested_bottom.css(".YMlKec::text").get(),
            "percent_price_change": f"+{current_percent_change}" if "Up" in current_percent_change_raw_value else f"-{current_percent_change}"
        })

    return data


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, ensure_ascii=False))
