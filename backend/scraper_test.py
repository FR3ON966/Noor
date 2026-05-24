import requests
from bs4 import BeautifulSoup

def explore():
    url = "https://ustgate.ust.edu.sd/askust/"
    
    # Let's try to get the main page first
    try:
        session = requests.Session()
        # Verify=False because many university sites have bad certs
        r = session.get(url, verify=False, timeout=10)
        print(f"Status: {r.status_code}")
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Look for links
        links = soup.find_all('a')
        print(f"Found {len(links)} links:")
        for a in links[:20]:
            print(f"- {a.get('href')}: {a.text.strip()}")
            
        # Look for buttons or forms
        forms = soup.find_all('form')
        print(f"\nFound {len(forms)} forms.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    explore()
