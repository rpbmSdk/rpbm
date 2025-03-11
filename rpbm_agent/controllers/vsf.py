import os
import requests
import bs4 as bs
import json

import dotenv

dotenv.load_dotenv()
VSF_LOGIN = os.getenv("VSF_LOGIN")
VSF_PASSWORD = os.getenv("VSF_PASSWORD")
VSF_BASE_URL = "https://client.myvsf.fr"
VSF_LOGIN_URL = f"{VSF_BASE_URL}/identification"
VSF_SEARCH_URL = f"{VSF_BASE_URL}/catalogue/vitrage"
VSF_SEARCH_ARTICLES_URL = f"{VSF_BASE_URL}/catalogue/articles-client"


class VSFArticle:
    code: str
    code_marque: str
    type_piece: str
    prix_vente: str
    prixVente:float
    remise: str
    prix_ht: str
    prixHT: float
    promo: bool
    stock_groupe: int
    stock: int
    available: bool
    remiseRPBM:float

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.prixVente = float(self.prix_vente.removesuffix("&nbsp;€").replace(",", "."))
        self.prixHT = float(self.prix_ht.removesuffix("&nbsp;€").replace(",", "."))
        self.stock_groupe = int(self.stock_groupe)
        self.stock = int(self.stock)
        self.remiseRPBM = 0.2
        # TODO : recalculer le prix de vente avec la remise RPBM
        
        pass


class VSFAgent:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # self.auth_r = self.auth()

    def auth(self, login:str, password:str):
        r = self.session.get(VSF_LOGIN_URL, headers=self.headers)
        page = bs.BeautifulSoup(r.text, "html.parser")
        _token = page.find("input", {"name": "_token"})["value"]
        r = self.session.post(
            VSF_LOGIN_URL,
            data={
                "login": login,
                "password": password,
                "_token": _token,
                "customer_id": None,
            },
        )
        return r

    def searchEurocodePage(self, eurocode: str = "6539RGSH5RD"):
        r = self.session.get(VSF_SEARCH_URL, params={"search": eurocode})
        page = bs.BeautifulSoup(r.text, "html.parser")
        return page

    def searchEurocodeArticlesClient(self, eurocode: str = "6539RGSH5RD"):
        page = self.searchEurocodePage(eurocode)
        div = page.find("div", id="articles-list-container")
        csrf_token = page.find("meta", {"name": "csrf-token"})["content"]
        rawList = div.attrs["data-articles-ids"]
        articlesIds = json.loads(rawList)
        r = self.session.post(
            VSF_SEARCH_ARTICLES_URL,
            params={"articlesIds[]": articlesIds},
            headers={"x-requested-with": "XMLHttpRequest", "X-CSRF-TOKEN": csrf_token},
        )
        if r.status_code == 200:
            data = r.json()
            if data['response']:
                data = data['data']
                return [VSFArticle(**article) for article in data]
        print(r.status_code)
        return []
        
