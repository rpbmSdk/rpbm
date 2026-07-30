"""Vérifie la logique d'authentification des agents, sans réseau.

    python test_portal_auth.py

Les portails sont simulés d'après le comportement réel observé via
`debug_portals.py` (voir les commentaires dans `controllers/xglass.py`).
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent / "controllers"))

import vsf  # noqa: E402
import xglass  # noqa: E402

MAIN = xglass.XGLASS_MAIN_URL
LOGIN_KO = "https://portail-xglass.com/login.html?error=password.mismatch"


class FakeXGlass:
    """X'Glass refuse tout login tant qu'une session est ouverte ailleurs ;
    la tentative refusée évince cette session, la suivante aboutit."""

    def __init__(self, session_open=False, good_password=True):
        self.session_open = session_open
        self.good_password = good_password
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("GET", url))
        return SimpleNamespace(url=url, text="<form/>")

    def post(self, url, data=None, **kwargs):
        self.calls.append(("POST", url))
        if not self.good_password:
            return SimpleNamespace(url=LOGIN_KO, text="<form/>")
        if self.session_open:
            self.session_open = False
            return SimpleNamespace(url=LOGIN_KO, text="<form/>")
        return SimpleNamespace(url=MAIN, text="<html/>")


def make_agent(portal):
    agent = xglass.XGLASS()
    agent.get, agent.post = portal.get, portal.post
    return agent


def test_xglass_nominal():
    portal = FakeXGlass()
    make_agent(portal).auth("u", "p")
    assert [c for c in portal.calls if c[0] == "POST"] == [("POST", xglass.XGLASS_LOGIN_URL)], portal.calls


def test_xglass_reprend_une_session_restee_ouverte():
    portal = FakeXGlass(session_open=True)
    make_agent(portal).auth("u", "p")
    posts = [c for c in portal.calls if c[0] == "POST"]
    assert len(posts) == 2, portal.calls
    # Régression : un GET /logout.html entre deux tentatives fait rejouer la
    # requête sauvegardée par Spring et déconnecte aussitôt le login réussi.
    assert not any("logout" in url for _, url in portal.calls), portal.calls


def test_xglass_mauvais_identifiants():
    portal = FakeXGlass(good_password=False)
    try:
        make_agent(portal).auth("u", "mauvais")
    except xglass.XGlassAuthError:
        pass
    else:
        raise AssertionError("XGlassAuthError attendue")
    assert len([c for c in portal.calls if c[0] == "POST"]) == 2, portal.calls


def test_xglass_releve_la_page_de_login_avant_le_json():
    agent = xglass.XGLASS()
    agent.initRecherche = True
    agent.post = lambda *args, **kwargs: SimpleNamespace(
        url=xglass.XGLASS_MAIN_URL, text="<form/>", json=lambda: {}
    )
    try:
        agent.searchImmat("DS808DZ")
    except xglass.XGlassAuthError:
        pass
    else:
        raise AssertionError("XGlassAuthError attendue pour une page de login expirée")


def test_xglass_releve_la_page_de_login_avant_les_pieces():
    agent = xglass.XGLASS()
    agent.get = lambda *args, **kwargs: SimpleNamespace(
        url=xglass.XGLASS_MAIN_URL, text="<form/>"
    )
    try:
        agent.getPiecesData(1, 2)
    except xglass.XGlassAuthError:
        pass
    else:
        raise AssertionError("XGlassAuthError attendue pour les pièces expirées")


class FakeVSF:
    """Laravel : `_token` est présent aussi bien sur la page de connexion que
    sur les pages authentifiées (formulaire de déconnexion)."""

    PAGE = '<input type="hidden" name="_token" value="tok">'

    def __init__(self, final_url):
        self.final_url = final_url

    def get(self, url, **kwargs):
        return SimpleNamespace(url=url, text=self.PAGE, status_code=200)

    def post(self, url, **kwargs):
        return SimpleNamespace(url=self.final_url, text=self.PAGE, status_code=200)


def make_vsf(final_url):
    agent = vsf.VSFAgent()
    portal = FakeVSF(final_url)
    agent.get, agent.post = portal.get, portal.post
    return agent


def test_vsf_succes_malgre_le_token_de_deconnexion():
    make_vsf(vsf.VSF_BASE_URL).auth("u", "p")  # ne doit pas lever


def test_vsf_echec_si_retour_sur_la_page_de_connexion():
    try:
        make_vsf(vsf.VSF_LOGIN_URL).auth("u", "mauvais")
    except vsf.VSFAuthError:
        pass
    else:
        raise AssertionError("VSFAuthError attendue")


def test_vsf_releve_la_redirection_login_avant_la_recherche():
    agent = vsf.VSFAgent()
    agent.get = lambda *args, **kwargs: SimpleNamespace(
        url=vsf.VSF_LOGIN_URL, text=FakeVSF.PAGE, status_code=200
    )
    try:
        agent.searchEurocodePage("6539R")
    except vsf.VSFAuthError:
        pass
    else:
        raise AssertionError("VSFAuthError attendue pour une session VSF expirée")


def test_vsf_releve_la_redirection_login_avant_la_fiche():
    agent = vsf.VSFAgent()
    agent.get = lambda *args, **kwargs: SimpleNamespace(
        url=vsf.VSF_LOGIN_URL, text=FakeVSF.PAGE, status_code=200
    )
    try:
        agent.getArticleDetails({"code": "6539RGSH5RD"})
    except vsf.VSFAuthError:
        pass
    else:
        raise AssertionError("VSFAuthError attendue pour une fiche VSF expirée")


def test_vsf_article_stock_renomme():
    article = vsf.VSFArticle(
        code="6539RGSH5RD", prix_vente="33,15&nbsp;€", prix_ht="29,84&nbsp;€",
        total_stock="58", availability=1,
    )
    assert article.stock == 58 and article.available
    assert article.absoluteImgUrls == []  # imgUrls absent : ne doit pas planter


def test_vsf_fiche_article_extrait_dimensions_images_et_suggestions():
    page = vsf.bs.BeautifulSoup(
        '''
        <html><body>
          <h1>Pare-brise vert</h1>
          <table>
            <tr><th>Largeur</th><td>124 cm</td></tr>
            <tr><th>Longueur</th><td>560 mm</td></tr>
            <tr><th>Information modèle</th><td>PEUGEOT 208</td></tr>
          </table>
          <a data-zoom-image="/articles-photos/PEUGEO/6571/6571AGRCHIMVZ/6571agrchimvz_emb.jpg?p=xlg&amp;s=signe"/>
          <div id="article-reference-complementaires-carousel">
            <a href="/catalogue/article/6571AGRCHIMVZ">Article courant</a>
            <article><a href="/catalogue/article/6571AGRCIMVZ"><img src="/thumb.jpg" alt="Suggestion"/></a></article>
          </div>
        </body></html>
        ''',
        "html.parser",
    )
    details = vsf.VSFAgent().extractArticleDetails(
        page,
        {
            "code": "6571AGRCHIMVZ",
            "name": "",
            "prix_vente": "100,00&nbsp;€",
            "prix_ht": "80,00&nbsp;€",
            "total_stock": "1",
            "imgUrls": ["/thumb.jpg"],
        },
        "https://client.myvsf.fr/catalogue/article/6571AGRCHIMVZ",
    )
    assert details["largeurMm"] == 1240
    assert details["longueurMm"] == 560
    assert details["fullImageUrls"] == [
        "https://client.myvsf.fr/articles-photos/PEUGEO/6571/6571AGRCHIMVZ/6571agrchimvz_emb.jpg?p=xlg&s=signe"
    ]
    assert details["images"][0]["fullUrl"] == details["fullImageUrls"][0]
    assert details["suggestedArticles"][0]["code"] == "6571AGRCIMVZ"


def test_vsf_dimension_invalide_ne_produit_pas_de_valeur():
    assert vsf._parse_dimension_mm("variable selon montage") is None
    assert vsf._parse_dimension_mm("12,5 cm") == 125


def test_vsf_fiche_bootstrap_extrait_dimensions_sans_unite_et_metadonnees():
    page = vsf.bs.BeautifulSoup(
        '''
        <div class="article-card">
          <div class="row">
            <div class="col-sm-9">
              <div class="row">
                <div class="col-xs-6">Dimensions :</div>
                <div class="col-xs-6">Largeur : 505<br/>Longueur : 666</div>
              </div>
              <div class="row">
                <div class="col-xs-6">Référence constructeur :</div>
                <div class="col-xs-6">9204H9</div>
              </div>
              <div class="row">
                <div class="col-xs-6">Temps main d’œuvre :</div>
                <div class="col-xs-6">0.40</div>
              </div>
            </div>
          </div>
        </div>
        <script>modules.catalogList.setupStockBadge($('#stock-dispo'), 1, "56", "6539RGSH5RD", {});</script>
        ''',
        "html.parser",
    )
    details = vsf.VSFAgent().extractArticleDetails(
        page,
        {"code": "6539RGSH5RD", "name": "Vitrage", "total_stock": "5"},
        "https://client.myvsf.fr/catalogue/article/6539RGSH5RD",
    )
    assert details["largeurMm"] == 505
    assert details["longueurMm"] == 666
    assert details["refConstructeur"] == "9204H9"
    assert details["total_stock"] == "56"
    assert {item["label"] for item in details["technicalDetails"]} >= {
        "Largeur",
        "Longueur",
        "Temps main d’œuvre",
    }


def test_vsf_suggestion_extrait_carte_complete_et_reste_creable():
    page = vsf.bs.BeautifulSoup(
        '''
        <div id="article-reference-complementaires-carousel">
          <div class="col-md-4 text-center">
            <img src="/articles-photos/COLLE/188/PP-COLLE310/photo.jpg?p=md-2&amp;s=signe"/>
            <div style="font-size: 1.2rem"><b>9,55 €</b></div>
            <button data-article='{"designation_translated":"CARTOUCHE COLLE","constructor_reference":"REF-310","base_price":"9.10"}'/>
            <a href="/catalogue/article/PP-COLLE310">PP-COLLE310</a>
          </div>
        </div>
        ''',
        "html.parser",
    )
    suggestion = vsf.VSFAgent._extractSuggestedArticles(page, "6539RGSH5RD")[0]
    article = vsf.VSFArticle(**suggestion)
    assert suggestion["name"] == "CARTOUCHE COLLE"
    assert suggestion["refConstructeur"] == "REF-310"
    assert article.prixVente == 9.55
    assert article.prixHT == 9.10
    assert article.images[0]["thumbnailUrl"].startswith("https://client.myvsf.fr/")


def test_vsf_suggestion_indisponible_reste_affichee():
    class FakeSuggestionAgent(vsf.VSFAgent):
        def __init__(self):
            pass

        def get(self, url, **kwargs):
            if url.endswith("/catalogue/article/PP-COLLE310"):
                raise vsf.VSFError("Fiche indisponible")
            return SimpleNamespace(
                status_code=200,
                url=url,
                text='''
                    <div id="article-reference-complementaires-carousel">
                      <div class="col-md-4">
                        <img src="/thumb.jpg"/>
                        <a href="/catalogue/article/PP-COLLE310">PP-COLLE310</a>
                      </div>
                    </div>
                ''',
            )

    details = FakeSuggestionAgent().getArticleDetails(
        {"code": "ARTICLE-PRINCIPAL"}, enrich_suggestions=True
    )
    suggestion = details["suggestedArticles"][0]
    assert suggestion["code"] == "PP-COLLE310"
    assert suggestion["detailsUnavailable"] is True


def test_vsf_valeurs_de_creation_produit():
    article = vsf.VSFArticle(
        code="6571AGRCHIMVZ",
        name="Pare-brise",
        refConstructeur="1617361980",
        prix_vente="100,00&nbsp;€",
        prix_ht="80,00&nbsp;€",
        total_stock="1",
        largeurMm=1240,
        longueurMm=560,
    )
    values = vsf.product_creation_values(article, "<p>Note VSF</p>", image=b"image")
    assert values["default_code"] == "1617361980"
    assert values["x_studio_eurocode"] == "6571AGRCHIMVZ"
    assert values["x_studio_largeur_mm"] == 1240
    assert values["x_studio_longueur_mm"] == 560
    assert values["description"] == "<p>Note VSF</p>"


def test_vsf_reference_constructeur_absente_utilise_le_code_vsf():
    article = vsf.VSFArticle(
        code="6571AGRCHIMVZ",
        name="Pare-brise",
        refConstructeur=" - ",
        prix_vente="100,00&nbsp;€",
        prix_ht="80,00&nbsp;€",
        total_stock="1",
    )
    values = vsf.product_creation_values(article, "<p>Note VSF</p>")
    assert values["default_code"] == "6571AGRCHIMVZ"
    assert values["x_studio_reference_constructeur"] is False
    assert vsf.constructor_reference_or_vsf_code("-", "6571AGRCHIMVZ") == "6571AGRCHIMVZ"


def test_vsf_valeurs_de_synchronisation_produit_preservent_identite_et_medias():
    article = vsf.VSFArticle(
        code="6571AGRCHIMVZ",
        name="Désignation VSF",
        prix_vente="100,00 €",
        total_stock="1",
        largeurMm=1240,
        longueurMm=560,
        url="https://client.myvsf.fr/catalogue/article/6571AGRCHIMVZ",
    )
    values = vsf.product_sync_values(article, vsf.product_description(article))
    assert values == {
        "x_studio_largeur_mm": 1240,
        "x_studio_longueur_mm": 560,
        "list_price": 100.0,
        "description": values["description"],
    }
    assert "name" not in values
    assert "x_studio_eurocode" not in values
    assert "image_1920" not in values
    assert "Informations VSF" in values["description"]


def test_vsf_valeurs_fournisseur_completes():
    article = vsf.VSFArticle(
        code="6571AGRCHIMVZ",
        name="Désignation VSF",
        prix_vente="100,00 €",
        total_stock="1",
    )
    values = vsf.product_supplierinfo_values(
        article,
        5708,
        product_tmpl_id=42,
        date_start="2026-07-30",
    )
    assert values == {
        "partner_id": 5708,
        "product_name": "Désignation VSF",
        "product_code": "6571AGRCHIMVZ",
        "delay": 1,
        "min_qty": 0,
        "price": 80.0,
        "product_tmpl_id": 42,
        "date_start": "2026-07-30",
    }


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("Tous les tests passent.")
