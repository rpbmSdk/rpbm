"""Rejoue l'authentification et le scraping des portails, hors Odoo.

Sert à déboguer les agents X'Glass / VSF sans passer par le widget : chaque
requête HTTP est tracée (voir `controllers/portal_trace.py`) et le corps des
réponses peut être écrit sur disque pour inspecter le HTML réellement reçu.

Usage (depuis le dossier `rpbm_agent/`) :
    python debug_portals.py                          # auth des deux portails
    python debug_portals.py --immat DS808DZ          # + recherche véhicule
    python debug_portals.py --portal vsf --eurocode 6539R
    python debug_portals.py --dump trace/            # + dump des réponses

Identifiants lus dans `.env` (mêmes clés que push_credentials.py).

ATTENTION : X'Glass n'autorise qu'une session par identifiant — lancer ce
script pendant qu'un utilisateur se sert du widget invalide sa session.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "controllers"))

import dotenv  # noqa: E402
import portal_trace  # noqa: E402
import vsf as vsf_mod  # noqa: E402
import xglass as xglass_mod  # noqa: E402


def run_xglass(args):
    agent = xglass_mod.XGLASS()
    try:
        agent.auth(os.environ["XGLASS_USER"], os.environ["XGLASS_PASS"])
        print("X'Glass : authentification OK")
        if args.immat:
            vehicules = agent.searchVehiculeImmat(args.immat)
            print(f"X'Glass : {len(vehicules)} véhicule(s) pour {args.immat}")
            for v in vehicules:
                print(f"  - {v.id} {v.libelleCourt}")
    except Exception as e:
        print(f"X'Glass : ÉCHEC — {type(e).__name__}: {e}")
    finally:
        if not args.keep_open:
            agent.close()


def run_vsf(args):
    agent = vsf_mod.VSFAgent()
    try:
        agent.auth(os.environ["VSF_LOGIN"], os.environ["VSF_PASSWORD"])
        print("VSF : authentification OK")
        if args.eurocode:
            articles = agent.searchEurocodeArticlesClient(args.eurocode)
            print(f"VSF : {len(articles)} article(s) pour {args.eurocode}")
            for a in articles:
                print(f"  - {a.code} {a.name} {a.prixVente} €")
    except Exception as e:
        print(f"VSF : ÉCHEC — {type(e).__name__}: {e}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--portal", choices=("xglass", "vsf", "both"), default="both")
    parser.add_argument("--immat", help="immatriculation à rechercher sur X'Glass")
    parser.add_argument("--eurocode", help="eurocode à rechercher sur VSF")
    parser.add_argument("--dump", help="dossier où écrire le corps des réponses")
    parser.add_argument("--keep-open", action="store_true", help="ne pas se déconnecter de X'Glass à la fin")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    dotenv.load_dotenv()
    portal_trace.configure(True, args.dump)

    if args.portal in ("xglass", "both"):
        run_xglass(args)
    if args.portal in ("vsf", "both"):
        run_vsf(args)


if __name__ == "__main__":
    main()
