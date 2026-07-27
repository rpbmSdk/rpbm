import logging
import os
import requests
import bs4 as bs
import json
import re
import unicodedata
from urllib.parse import parse_qs, urljoin, urlparse

import dotenv

try:
    from . import portal_trace
except ImportError:
    import portal_trace

_logger = logging.getLogger(__name__)

dotenv.load_dotenv()
VSF_LOGIN = os.getenv("VSF_LOGIN")
VSF_PASSWORD = os.getenv("VSF_PASSWORD")
VSF_BASE_URL = "https://client.myvsf.fr"
VSF_LOGIN_URL = f"{VSF_BASE_URL}/identification"
VSF_SEARCH_URL = f"{VSF_BASE_URL}/catalogue/vitrage"
VSF_SEARCH_ARTICLES_URL = f"{VSF_BASE_URL}/catalogue/articles-client"
REQUEST_TIMEOUT = 20  # secondes, appliqué à tous les appels vers le portail VSF
DEFAULT_RPBM_DISCOUNT = 0.2


def _absolute_url(url):
    """Normalise une URL VSF relative sans fabriquer de signature d'image."""
    return urljoin(f"{VSF_BASE_URL}/", url or "")


def _normalise_label(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .casefold()
        .split()
    )


def _text(node):
    return node.get_text(" ", strip=True) if node else ""


def _parse_dimension_mm(value):
    """Convertit une dimension VSF explicite en millimètres, sinon None."""
    match = re.search(r"(-?\d+(?:[\s,.]\d+)?)\s*(mm|cm|m)\b", value or "", re.I)
    if not match:
        return None
    number = float(match.group(1).replace(" ", "").replace(",", "."))
    unit = match.group(2).casefold()
    multiplier = {"mm": 1, "cm": 10, "m": 1000}[unit]
    return number * multiplier


def product_creation_values(article, description, image=False):
    """Valeurs Odoo déterministes dérivées d'une fiche VSF enrichie."""
    reference = str(getattr(article, "refConstructeur", None) or article.code).strip()
    return {
        "name": article.name,
        "default_code": reference,
        "x_studio_eurocode": article.code,
        "x_studio_largeur_mm": getattr(article, "largeurMm", None) or False,
        "x_studio_longueur_mm": getattr(article, "longueurMm", None) or False,
        "list_price": article.prixVente,
        "type": "product",
        "x_studio_reference_constructeur": getattr(article, "refConstructeur", None) or False,
        "image_1920": image or False,
        "description": description,
    }


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
    total_stock: str
    stock: int
    available: bool
    remiseRPBM:float
    prixVenteRPBM:float
    absoluteImgUrls: list
    fullImageUrls: list
    images: list
    imgUrls: list
    refConstructeur: str
    technicalDetails: list
    suggestedArticles: list
    largeurMm: float
    longueurMm: float
    # absoluteUrl:str

    def __init__(self, **kwargs):
        rpbm_discount = kwargs.pop('_rpbm_discount', DEFAULT_RPBM_DISCOUNT)
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.prixVente = self._parse_price(getattr(self, 'prix_vente', None))
        self.prixHT = self._parse_price(getattr(self, 'prix_ht', None))
        # VSF a renommé ses champs de stock : `stock`/`stock_groupe` ont disparu
        # de la réponse au profit de `total_stock` (chaîne) et `availability`
        # — vérifié contre le portail réel, voir `debug_portals.py`. On conserve
        # `stock`/`available`, consommés par ArticleComponent.xml.
        self.stock = int(getattr(self, 'total_stock', 0) or 0)
        self.available = self.stock > 0
        self.set_rpbm_discount(rpbm_discount)
        # imgUrls est absent quand l'article n'a pas de ligne correspondante
        # dans la page de résultats (voir searchEurocodeArticlesClient).
        self.absoluteImgUrls = [_absolute_url(url) for url in getattr(self, 'imgUrls', [])]
        self.fullImageUrls = list(getattr(self, 'fullImageUrls', []) or [])
        self.images = list(getattr(self, 'images', []) or [])
        if not self.images:
            self.images = [
                {"thumbnailUrl": url, "fullUrl": None}
                for url in self.absoluteImgUrls
            ]
        self.technicalDetails = list(getattr(self, 'technicalDetails', []) or [])
        self.suggestedArticles = list(getattr(self, 'suggestedArticles', []) or [])
        self.largeurMm = getattr(self, 'largeurMm', None)
        self.longueurMm = getattr(self, 'longueurMm', None)

    @staticmethod
    def _parse_price(value):
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        normalized = str(value).replace("&nbsp;", "").replace("€", "")
        normalized = normalized.replace(" ", "").replace(",", ".")
        try:
            return float(normalized)
        except ValueError:
            return None

    def set_rpbm_discount(self, discount):
        """Applique la remise RPBM configurée et valide sa plage."""
        try:
            discount = float(discount)
        except (TypeError, ValueError) as error:
            raise VSFError("La remise RPBM doit être un nombre décimal compris entre 0 et 1.") from error
        if not 0 <= discount <= 1:
            raise VSFError("La remise RPBM doit être comprise entre 0 et 1.")
        self.remiseRPBM = discount
        self.prixVenteRPBM = (
            self.prixVente * (1 - self.remiseRPBM)
            if self.prixVente is not None
            else None
        )


class VSFAgent:
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }

    def __init__(self):
        self.session = requests.Session()
        portal_trace.attach(self.session, "vsf")
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
        # Vérifié contre le portail réel (voir `debug_portals.py`) : en cas de
        # succès VSF redirige vers l'accueil, en cas d'échec il réaffiche
        # /identification. Ne pas se fier à la présence d'un champ `_token` :
        # les pages authentifiées en contiennent un aussi (formulaire de
        # déconnexion), ce qui faisait échouer une connexion pourtant réussie.
        if r.status_code != 200 or r.url.rstrip("/") == VSF_LOGIN_URL:
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

    def getArticleDetails(self, article_info):
        """Enrichit un article à partir de sa fiche VSF authentifiée."""
        code = str(article_info.get("code") or "").strip()
        url = _absolute_url(article_info.get("url") or f"/catalogue/article/{code}")
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != urlparse(VSF_BASE_URL).netloc:
            raise VSFError("URL de fiche article VSF invalide.")
        response = self.get(url)
        if response.status_code != 200:
            raise VSFError(f"Réponse HTTP {response.status_code} inattendue pour l'article VSF {code}.")
        if getattr(response, "url", "").rstrip("/") == VSF_LOGIN_URL:
            raise VSFAuthError("Session VSF expirée lors de la lecture de la fiche article.")
        page = bs.BeautifulSoup(response.text, "html.parser")
        return self.extractArticleDetails(page, article_info, url)

    def extractArticleDetails(self, page, article_info, url):
        """Extrait le contrat utile d'une fiche article VSF déjà téléchargée."""
        details = dict(article_info)
        details["url"] = url
        technical_details = self._extractTechnicalDetails(page)
        details["technicalDetails"] = technical_details

        by_label = {
            _normalise_label(item["label"]): item["value"]
            for item in technical_details
        }
        details["largeurMm"] = _parse_dimension_mm(by_label.get("largeur"))
        details["longueurMm"] = _parse_dimension_mm(by_label.get("longueur"))
        if not details.get("prix_vente"):
            details["prix_vente"] = (
                by_label.get("prix de vente")
                or by_label.get("prix ttc")
                or by_label.get("prix")
            )
        if not details.get("prix_ht"):
            details["prix_ht"] = by_label.get("prix ht")
        if not details.get("total_stock"):
            details["total_stock"] = by_label.get("stock") or 0
        details["refConstructeur"] = (
            details.get("refConstructeur")
            or by_label.get("reference constructeur")
            or by_label.get("reference")
            or ""
        )

        title = _text(page.select_one("h1"))
        if title and not details.get("name"):
            details["name"] = title

        thumbnails = [_absolute_url(value) for value in details.get("imgUrls", [])]
        full_images = self._extractFullImageUrls(page)
        details["fullImageUrls"] = full_images
        details["absoluteImgUrls"] = thumbnails
        details["images"] = [
            {
                "thumbnailUrl": thumbnail,
                "fullUrl": full_images[index] if index < len(full_images) else None,
            }
            for index, thumbnail in enumerate(thumbnails)
        ]
        for index, full_url in enumerate(full_images):
            if index >= len(thumbnails):
                details["images"].append({"thumbnailUrl": full_url, "fullUrl": full_url})

        details["suggestedArticles"] = self._extractSuggestedArticles(page, details.get("code"))
        return details

    @staticmethod
    def _extractTechnicalDetails(page):
        details = []
        seen = set()

        def add(label, value):
            label, value = (label or "").strip(), (value or "").strip()
            key = _normalise_label(label)
            if not key or not value or (key, value) in seen:
                return
            seen.add((key, value))
            details.append({"label": label.rstrip(":"), "value": value})

        for row in page.select("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            if len(cells) >= 2:
                add(_text(cells[0]), _text(cells[1]))
        for term in page.select("dl dt"):
            definition = term.find_next_sibling("dd")
            add(_text(term), _text(definition))
        for node in page.select("[data-label]"):
            add(node.get("data-label"), _text(node))
        for node in page.select("li, p"):
            text = _text(node)
            if ":" in text:
                label, value = text.split(":", 1)
                if len(label) <= 80:
                    add(label, value)
        return details

    @staticmethod
    def _extractFullImageUrls(page):
        urls = []
        seen = set()

        def add(candidate):
            if not candidate:
                return
            for value in str(candidate).split(","):
                url = _absolute_url(value.strip().split(" ")[0])
                query = parse_qs(urlparse(url).query)
                if query.get("p") != ["xlg"] or url in seen:
                    continue
                seen.add(url)
                urls.append(url)

        for node in page.select("[data-zoom-image], [data-large-image], [data-src], a[href], img[src], img[srcset]"):
            for attribute in ("data-zoom-image", "data-large-image", "data-src", "href", "src", "srcset"):
                add(node.get(attribute))
        return urls

    @staticmethod
    def _extractSuggestedArticles(page, current_code):
        carousel = page.find(id="article-reference-complementaires-carousel")
        if not carousel:
            return []
        suggestions = []
        seen = set()
        for link in carousel.select("a[href]"):
            url = _absolute_url(link.get("href"))
            match = re.search(r"/catalogue/article/([^/?#]+)", url)
            if not match:
                continue
            code = match.group(1)
            if code == current_code or code in seen:
                continue
            seen.add(code)
            card = link.find_parent(["article", "li", "div"]) or link
            image = card.find("img")
            name = _text(link) or (image.get("alt") if image else "") or code
            suggestions.append({
                "code": code,
                "name": name,
                "url": url,
                "refConstructeur": "",
                "imgUrls": [image.get("src")] if image and image.get("src") else [],
            })
        return suggestions
