# standard_facile

## Objectif du module

Ce module Odoo permet aux utilisateurs internes d'importer facilement des données à partir d'un fichier CSV via une page web privée accessible à l'URL `/standard_facile`. Après l'envoi du fichier, le module traite le fichier CSV pour créer de nouveaux enregistrements dans le système. Une page de succès s'affiche si l'import est réussi, sinon les erreurs détectées sont affichées à l'utilisateur.

### Fonctionnalités principales
- Page web privée réservée aux utilisateurs internes
- Formulaire d'upload de fichier CSV
- Traitement automatique du fichier et création d'enregistrements
- Affichage d'une page de succès ou des erreurs rencontrées

### Accès
Seuls les utilisateurs internes (groupe "Utilisateur interne") peuvent accéder à la page d'import.
