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


def test_vsf_article_stock_renomme():
    article = vsf.VSFArticle(
        code="6539RGSH5RD", prix_vente="33,15&nbsp;€", prix_ht="29,84&nbsp;€",
        total_stock="58", availability=1,
    )
    assert article.stock == 58 and article.available
    assert article.absoluteImgUrls == []  # imgUrls absent : ne doit pas planter


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("Tous les tests passent.")
