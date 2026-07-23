import logging
import os
import requests
import bs4 as bs
import json

import dotenv

_logger = logging.getLogger(__name__)

dotenv.load_dotenv()
VSF_LOGIN = os.getenv("VSF_LOGIN")
VSF_PASSWORD = os.getenv("VSF_PASSWORD")
VSF_BASE_URL = "https://client.myvsf.fr"
VSF_LOGIN_URL = f"{VSF_BASE_URL}/identification"
VSF_SEARCH_URL = f"{VSF_BASE_URL}/catalogue/vitrage"
VSF_SEARCH_ARTICLES_URL = f"{VSF_BASE_URL}/catalogue/articles-client"
REQUEST_TIMEOUT = 20  # secondes, appliqué à tous les appels vers le portail VSF


class VSFError(Exception):
    """Erreur générique lors d'un échange avec le portail VSF."""


class VSFAuthError(VSFError):
    """Authentification VSF refusée ou impossible à vérifier."""


class VSFArticle:
    name:str
    code: str
    url:str
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
    prixVenteRPBM:float
    absoluteImgUrls: list
    imgUrls: list
    refConstructeur: str
    # absoluteUrl:str

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.prixVente = float(self.prix_vente.removesuffix("&nbsp;€").replace(",", "."))
        self.prixHT = float(self.prix_ht.removesuffix("&nbsp;€").replace(",", "."))
        self.stock_groupe = int(self.stock_groupe)
        self.stock = int(self.stock)
        self.remiseRPBM = 0.2
        self.prixVenteRPBM = self.prixVente * (1 - self.remiseRPBM)
        # TODO : recalculer le prix de vente avec la remise RPBM
        self.absoluteImgUrls = []
        for imgUrl in self.imgUrls:
            self.absoluteImgUrls.append(f"{VSF_BASE_URL}{imgUrl}")
        
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

    def get(self, url, **kwargs):
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        try:
            return self.session.get(url, **kwargs)
        except requests.exceptions.RequestException as e:
            raise VSFError(f"Erreur réseau VSF (GET {url}) : {e}") from e

    def post(self, url, **kwargs):
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        try:
            return self.session.post(url, **kwargs)
        except requests.exceptions.RequestException as e:
            raise VSFError(f"Erreur réseau VSF (POST {url}) : {e}") from e

    def auth(self, login:str, password:str):
        r = self.get(VSF_LOGIN_URL, headers=self.headers)
        page = bs.BeautifulSoup(r.text, "html.parser")
        token_input = page.find("input", {"name": "_token"})
        if not token_input or "value" not in token_input.attrs:
            raise VSFError("Jeton CSRF introuvable sur la page de connexion VSF (structure de page changée ?).")
        _token = token_input["value"]
        r = self.post(
            VSF_LOGIN_URL,
            data={
                "login": login,
                "password": password,
                "_token": _token,
                "customer_id": None,
            },
        )
        # VSF réaffiche le formulaire de connexion (donc un champ _token à
        # nouveau présent) en cas d'échec ; à reconfirmer contre le portail réel.
        still_on_login_page = bs.BeautifulSoup(r.text, "html.parser").find("input", {"name": "_token"})
        if r.status_code != 200 or still_on_login_page:
            raise VSFAuthError("Échec de connexion à VSF : identifiants refusés ou page inattendue.")
        return r

    def searchEurocodePage(self, eurocode: str = "6539RGSH5RD"):
        r = self.get(VSF_SEARCH_URL, params={"search": eurocode})
        page = bs.BeautifulSoup(r.text, "html.parser")
        return page

    def searchEurocodeArticlesClient(self, eurocode: str = "6539RGSH5RD"):
        page = self.searchEurocodePage(eurocode)
        div = page.find("div", id="articles-list-container")
        if div is None:
            raise VSFError("Conteneur articles introuvable sur la page de résultats VSF (session expirée ?).")
        csrf_tag = page.find("meta", {"name": "csrf-token"})
        if not csrf_tag:
            raise VSFError("Jeton CSRF introuvable sur la page de résultats VSF.")
        articlesIds = json.loads(div.attrs["data-articles-ids"])
        if not articlesIds:
            return []  # recherche légitimement sans résultat
        r = self.post(
            VSF_SEARCH_ARTICLES_URL,
            params={"articlesIds[]": articlesIds},
            headers={"x-requested-with": "XMLHttpRequest", "X-CSRF-TOKEN": csrf_tag["content"]},
        )
        if r.status_code != 200:
            raise VSFError(f"Réponse HTTP {r.status_code} inattendue de VSF (eurocode={eurocode}).")
        data = r.json()
        if not data.get('response'):
            return []  # signal explicite du portail : pas de résultat, pas une erreur
        data = data['data']
        product_lines = page.find_all("tr", class_="product-line")
        product_lines_data = [self.extractProductInfo(product_line) for product_line in product_lines]
        for article in data:
            for product_line in product_lines_data:
                if article['code'] == product_line['eurocode']:
                    article['imgUrls'] = product_line['imgUrls']
                    article['url'] = product_line['url']
                    article['name'] = product_line['name']
                    article['refConstructeur'] = product_line['refConstructeur']
                    break
        return [VSFArticle(**article) for article in data]
        
    def extractProductInfo(self, product_line:bs.BeautifulSoup):
        product_line_tds = product_line.find_all("td")
        imgUrls = [img["src"] for img in product_line_tds[0].find_all("img")]
        url = product_line_tds[1].find("a")["href"]
        eurocode = product_line_tds[1].find('a').text.strip()
        refConstructeur = product_line_tds[2].text.strip()
        name = product_line_tds[3].text.strip()
        return {
            'imgUrls': imgUrls,
            'url': url,
            'eurocode': eurocode,
            'refConstructeur': refConstructeur,
            'name': name
        }
        