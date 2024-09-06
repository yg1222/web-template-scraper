import requests
import logging

def get_proxy_list():
    r = requests.get("https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt")
    proxies_list = r.text.splitlines()
    return proxies_list


def get_working_proxies(proxy_list, url):
    '''
    This function takes a url and a list of proxies,
    then returns a list of working proxies.
    
    :param list proxy_list: A list of proxies to check.
    :param string url: The url to check with.
    :return list: A list of working proxies with the url provided.
    '''
    print("\nGetting working proxies...")
    working_proxies = []

    for proxy in proxy_list:
        proxies = {
            'http': proxy,
            'https': proxy,
        }
        try:
            r = requests.get(url, proxies=proxies, timeout=2)
            if r.status_code == 200:
                working_proxies.append(proxy)
                print(f"Found one working proxy: {proxy}")
        except Exception as e:
            # logging.error(f"There was an error connecting to proxy {proxy}, {e}")
            pass
    print(f"{len(working_proxies)} proxie(s) out of {len(proxy_list)} worked.\n")
    logging.info(f"{len(working_proxies)} proxie(s) out of {len(proxy_list)} worked.")
    return working_proxies