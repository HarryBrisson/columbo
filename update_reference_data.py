import requests
from bs4 import BeautifulSoup
import json


# get all state ids
def get_state_id_numbers():
    stids = {}
    url = "https://www.broadcastify.com/listen/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text,"html.parser")
    
    for o in soup.find("form").find_all("option"):
        stids[o.getText().replace(" ","-")] = o['value']
    return stids


def get_county_id_numbers_for_state(stid):
    ctids = {}
    url = "https://www.broadcastify.com/listen/stid/{}".format(stid)
    r = requests.get(url)
    soup = BeautifulSoup(r.text,"html.parser")
    
    try:
        rows = soup.find_all("table",{"class":"btable"})[-1].find_all("tr")
    except:
        return
    
    for row in rows:
        try:
            ctid = row.find_all("td")[0].find("a")['href'].split("/")[-1]
            name = row.find_all("td")[0].find("a").getText()
            ctids[name.replace(" ","-").replace(".","")] = ctid
        except:
            pass
    return ctids


def get_county_id_numbers():
    ctids = {}
    stids = get_state_id_numbers()
    for k in stids:
        state_name = k
        stid = stids[k]
        print("getting county ids in {}".format(state_name))
        ctids[state_name.replace(" ","-").replace(".","")] = get_county_id_numbers_for_state(stid)
    return ctids
        
        
def update_ctid_json_file():
    ctid_ref = get_county_id_numbers()

    filename = 'reference-data/ctids_by_name.json'

    with open(filename, 'w') as f:
        json.dump(ctid_ref, f)

    print("{} updated".format(filename))


if __name__ == "__main__":
    update_ctid_json_file()