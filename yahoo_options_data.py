import json
import re
from bs4 import BeautifulSoup

# Stipulations required for this program to work:
# dat file name and html file name must match the stock symbol. e.g. "aapl.dat", "aapl.html", "aapl"
def contractAsJson(filename):

    # change filename (str)'s extension to .html so it can be used to make a Beautiful Soup object. e.g. "aapl.dat" to "aapl.html"
    #with_html_extention = re.sub(".dat",".html",filename)
    #print(with_html_extention)

    # make soup object
    with open(filename) as f:
        soup = BeautifulSoup(f, "lxml")
    #print(soup.prettify()) #prints html text in nice format
    soup_string = str(soup)

    # getting current price
    without_extension = re.sub(".dat","",filename) #e.g. "aapl", "f", "xom"
    # in all test case dat and html files, the current price is written in a <span> group with the id "yfs_l84_stocksymbol"
    r1 = re.search("<span id=\"yfs_l84_"+without_extension+"\">", soup_string) #find the span with this id
    pattern = re.compile("\d+\.\d+") # this is the pattern used to looks for the current price that's in the span. Finds
    # digits left and right of a decimal, including the decimal. Note: compiling this pattern into a regex object allows
    # me to use a different search method which supports searching starting from a specific position
    r2 = pattern.search(soup_string, r1.end())
    current_price = float(r2.group()) #current price

    # getting URLs corresponding to expiration dates
    list_of_links = []
    list_of_URLs = []

    for link in soup.find_all("a"): # soup.find_all("a") returns a list of links found in the html; each element is a bs4.element.Tag object
        list_of_links.append(link.get("href")) #link.get("href") grabs the link as a string. Note "amp;" is gone. This must be added back in later

    # in all test case dat and html files, the URLs to the expiration dates not currently selected are written as "/q/op?s=STOCKSYMBOL&amp;m=YYYY-MM"
    for link in list_of_links:
        r3 = re.search("/q/op\?s="+without_extension.upper()+"&m=\d+-\d+", link)

        if r3 != None: #only call group() if match is made. Otherwise, will terminate run when match is not made in a link
        #and the rest of the links are not checked
            list_of_URLs.append("http://finance.yahoo.com"+r3.group())

    # now we want to append the url to the expiration date currently selected at the end of the list. The URL for this
    # one contains the date as well as the year and month. In all test case dat and html files, these URLs are written
    # as "/q/os?s=STOCKSYMBOL&amp;m=YYYY-MM-DD"
    for link in list_of_links:
        r4 = re.search("/q/os\?s="+without_extension.upper()+"&m=\d+-\d+-\d+", link)
        if r4 != None:
            list_of_URLs.append("http://finance.yahoo.com"+r4.group())

    # finally, add "amp;" back into each URL after the "STOCKSYMBOL"
    for i in range(0,len(list_of_URLs)):
        r5 = re.search("m=", list_of_URLs[i])
        first_chunk = list_of_URLs[i][:r5.start()]
        last_chunk = list_of_URLs[i][r5.start():]
        list_of_URLs[i] = first_chunk + "amp;" + last_chunk


    # getting list of detailed individual contracts, sorted in decreasing order of open interest.
    # to do this, first we'll make lists for each option's details (Ask, Bid, etc.) The order of the list will be the same
    # as the order that the options appear in the html file and the table. I.e. list_of_strikes[0] and list_of_bids[0]
    # is the strike and bid price respectively of the first option written in the html file (which is 50.00, 45.90 for AAPL)

    # get list of Strikes
    list_of_strikes = []

    # each call or put option's strike price is written after "/q/op?s=AAPL&amp;k="
    for link in list_of_links:
        r6 = re.search("/q/op\?s=" + without_extension.upper() + "&k=\d+\.\d+", link)

        if r6 != None:  # only call group() if match is made. Otherwise, will terminate run when match is not made in a link
            # and the rest of the links are not checked
            string_containing_strike_price = r6.group()
            r7 = re.search("\d+\.[0-9][0-9]", string_containing_strike_price)
            list_of_strikes.append(r7.group())

    list_of_symbols = []
    list_of_types = []
    list_of_dates = []
    list_of_lasts = []
    list_of_changes = []
    list_of_bids = []
    list_of_asks = []
    list_of_volumes = []
    list_of_open_interests = []

    #print(list_of_links)
    for link in list_of_links:
        r7 = re.search(without_extension.upper() + "\d+(C|P)\d+", link) #e.g. AAPL140920C00050000
        if r7 != None:
            r8 = re.search(without_extension.upper() + "(7|)", r7.group())
            list_of_symbols.append(r8.group()) #list of symbols constructed

            r9 = re.search("\d(C|P)\d", r7.group())
            r10 = re.search("(C|P)", r9.group())
            list_of_types.append(r10.group()) #list of types constructed

            r11 = re.search("([0-6]|[8-9])\d+", r7.group())
            list_of_dates.append(r11.group())#list_of_dates constructed

            r12 = re.search(r7.group(), soup_string) #e.g. finds AAPL140920C00050000 in html

            pattern = re.compile("((\d+\.\d+)|N/A)") #always has decimal. May be "N/A"
            r13 = pattern.search(soup_string, r12.end()) #finds lasts
            #print(r12.group())
            list_of_lasts.append(r13.group()) #list_of_lasts constructed

            r14 = pattern.search(soup_string, r13.end()) #finds changes (after last)
            pattern_color = re.compile("#\w+")
            r_color = pattern_color.search(soup_string, r13.end())
            if r_color.group() == "#000000": # black
                list_of_changes.append(" " + r14.group())
            elif r_color.group() == "#008800": # green
                list_of_changes.append("+" + r14.group())
            else: # red
                list_of_changes.append("-" + r14.group()) #list_of_changes constructed

            r15 = pattern.search(soup_string, r14.end()) #finds bids (after changes)
            list_of_bids.append(r15.group()) #list_of_bids constructed

            r16 = pattern.search(soup_string, r15.end())  # finds asks (after bids)
            list_of_asks.append(r16.group())  # list_of_asks constructed

            pattern = re.compile(">\d+(,|)\d*<")
            r17 = pattern.search(soup_string, r16.end())
            r18 = re.search("\d+(,|)\d*", r17.group())# finds volumes (after asks)
            list_of_volumes.append(r18.group())  # list_of_volumes constructed

            r19 = pattern.search(soup_string, r17.end())
            r20 = re.search("\d+(,|)\d*", r19.group()) # finds open interests (after volumes)
            list_of_open_interests.append(r20.group())  # list_of_open_interests constructed

    # all data has been scraped at this point.


    # list_of_open_interests currently contains strings with comma thousands separators. In order to sort, we need them
    # to be numbers. Turn them into floats
    for i in range(0, len(list_of_open_interests)):
        r19 = re.search(",", list_of_open_interests[i])
        if r19 != None:
            list_of_open_interests[i] = re.sub(",", "", list_of_open_interests[i])
        list_of_open_interests[i] = int(list_of_open_interests[i])


    # construct the list for the option details and then sort it by descending open interest
    option_quotes = []
    for i in range(0, len(list_of_strikes)):
        option = {"Ask": list_of_asks[i], "Bid": list_of_bids[i], "Change": list_of_changes[i], "Date": list_of_dates[i], "Last": list_of_lasts[i], "Open": list_of_open_interests[i], "Strike": list_of_strikes[i], "Symbol": list_of_symbols[i], "Type": list_of_types[i], "Vol": list_of_volumes[i]}
        option_quotes.append(option)

    option_quotes = sorted(option_quotes, key=lambda dict: dict["Open"], reverse=True)

    # add thousands comma back to open interests and turn it back into a string
    for i in range(0, len(option_quotes)):
        option_quotes[i]["Open"] = "{:,}".format(option_quotes[i]["Open"])

    #print(option_quotes)

    #for i in range(0, len(option_quotes)):
    #    print(option_quotes[i])

    """print(len(list_of_asks))
    print(len(list_of_bids))
    print(len(list_of_changes))
    print(len(list_of_dates))
    print(len(list_of_lasts))
    print(len(list_of_open_interests))
    print(len(list_of_strikes))
    print(len(list_of_symbols))
    print(len(list_of_types))
    print(len(list_of_volumes))"""

    """print(list_of_asks)
    print(list_of_bids)
    print(list_of_changes)
    print(list_of_dates)
    print(list_of_lasts)
    print(list_of_open_interests)
    print(list_of_strikes)
    print(list_of_symbols)
    print(list_of_types)
    print(list_of_volumes)"""

    myJson = {"currPrice": current_price, "dateUrls": list_of_URLs, "optionQuotes": option_quotes}  # build the dictionary that will hold the scraped data


    jsonQuoteData = json.dumps(myJson) #converts dictionary to string, then formats string to JSON format
    #jsonQuoteData = "[]"
    return jsonQuoteData

print(contractAsJson("aapl.html"))