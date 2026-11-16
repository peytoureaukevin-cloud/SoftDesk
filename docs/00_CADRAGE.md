# SoftDesk - cadrage avant développement

Ce document traduit la mission OpenClassrooms en mots simples. Il doit être relu avant de modifier le code.

## 1. But du projet

SoftDesk permet à des équipes de suivre les problèmes techniques rencontrés sur leurs projets.

Nous ne construisons pas une interface graphique. Nous construisons une **API REST** : un programme qui reçoit des requêtes HTTP et renvoie principalement des données JSON.

Exemple :

1. un utilisateur envoie une demande de création de projet ;
2. l'API vérifie son identité et ses droits ;
3. Django enregistre le projet dans la base de données ;
4. l'API renvoie une réponse JSON et un code HTTP.

## 2. Les cinq ressources principales

### User

Une personne qui utilise l'application.

Informations prévues :

- identifiant et mot de passe gérés par Django ;
- âge ;
- consentement pour être contacté ;
- consentement pour partager ses données ;
- date de création.

Règle RGPD : une personne de moins de 15 ans ne peut pas terminer son inscription.

### Project

Un projet suivi dans SoftDesk.

Informations prévues :

- titre ;
- description ;
- type : back-end, front-end, iOS ou Android ;
- auteur ;
- date de création.

À la création, l'auteur devient automatiquement contributeur de son projet.

### Contributor

Le lien entre un utilisateur et un projet.

Ce modèle est nécessaire parce que :

- un utilisateur peut participer à plusieurs projets ;
- un projet peut avoir plusieurs utilisateurs.

Le couple utilisateur/projet doit être unique : une même personne ne doit pas être ajoutée deux fois au même projet.

### Issue

Une tâche ou un problème appartenant à un projet.

Informations prévues :

- titre et description ;
- balise : BUG, FEATURE ou TASK ;
- priorité : LOW, MEDIUM ou HIGH ;
- statut : TO_DO, IN_PROGRESS ou FINISHED ;
- projet concerné ;
- auteur ;
- personne assignée, facultative ;
- date de création.

La personne assignée doit obligatoirement être contributrice du projet concerné.

### Comment

Un message rattaché à une issue.

Informations prévues :

- identifiant UUID généré automatiquement ;
- description ;
- issue concernée ;
- auteur ;
- date de création.

## 3. Relations entre les données

```text
User 1 -------- N Project       (un auteur peut créer plusieurs projets)
User 1 -------- N Contributor
Project 1 ----- N Contributor   (Contributor réalise le plusieurs-à-plusieurs)
Project 1 ----- N Issue
User 1 -------- N Issue         (auteur)
User 1 -------- N Issue         (personne assignée, relation facultative)
Issue 1 ------- N Comment
User 1 -------- N Comment       (auteur)
```

Dans Django, les relations marquées `1 ---- N` seront principalement représentées par des `ForeignKey`.

## 4. Parcours d'une requête

```text
Postman
   |
   | requête HTTP + jeton JWT
   v
urls.py -> ViewSet -> permissions -> serializer -> modèle -> base SQLite
   ^                                                        |
   |---------------- réponse JSON + code HTTP --------------|
```

- `urls.py` dirige la requête vers le bon traitement.
- le ViewSet organise les actions : lister, créer, lire, modifier et supprimer.
- les permissions vérifient qui a le droit d'agir.
- le serializer valide les données et transforme Python en JSON, ou JSON en Python.
- le modèle décrit la donnée et dialogue avec la base grâce à l'ORM Django.

## 5. Règles d'accès

| Situation | Lecture | Création | Modification/suppression |
| --- | --- | --- | --- |
| Utilisateur non connecté | Non | Inscription uniquement | Non |
| Utilisateur connecté mais non contributeur | Seulement ses ressources autorisées | Projet | Seulement ses propres ressources autorisées |
| Contributeur du projet | Projet, issues et commentaires du projet | Issue et commentaire | Uniquement les ressources dont il est l'auteur |
| Auteur d'une ressource | Oui | Oui si les autres règles sont respectées | Oui |

Les tests devront vérifier ces rôles séparément. Tester seulement qu'une URL fonctionne ne suffit pas.

## 6. Sécurité et conformité

- **Authentification** : un utilisateur obtient un jeton JWT après connexion.
- **Autorisation** : chaque requête protégée vérifie le jeton et les permissions.
- **Isolation** : un non-contributeur ne voit pas les données privées d'un projet.
- **Propriété** : seul l'auteur peut modifier ou supprimer sa ressource.
- **RGPD** : âge minimal, consentements, rectification et suppression du compte.
- **Dépendances** : elles seront gérées et verrouillées avec Poetry.
- **Dependabot** : il signalera les dépendances vulnérables ou dépassées sur GitHub.

## 7. Green code

- paginer les listes afin de ne pas renvoyer toutes les données en une fois ;
- limiter l'imbrication des serializers à un seul niveau ;
- éviter les requêtes répétées grâce à `select_related` et `prefetch_related` lorsqu'elles sont utiles ;
- mesurer les requêtes avant d'ajouter une optimisation complexe.

## 8. Points de terminaison prévus

Les noms exacts seront validés pendant l'implémentation, mais la structure sera proche de celle-ci :

```text
POST   /api/signup/
POST   /api/token/
POST   /api/token/refresh/

GET    /api/projects/
POST   /api/projects/
GET    /api/projects/{project_id}/
PUT    /api/projects/{project_id}/
DELETE /api/projects/{project_id}/

POST   /api/projects/{project_id}/contributors/
DELETE /api/projects/{project_id}/contributors/{user_id}/

GET    /api/projects/{project_id}/issues/
POST   /api/projects/{project_id}/issues/
GET    /api/projects/{project_id}/issues/{issue_id}/
PUT    /api/projects/{project_id}/issues/{issue_id}/
DELETE /api/projects/{project_id}/issues/{issue_id}/

GET    /api/projects/{project_id}/issues/{issue_id}/comments/
POST   /api/projects/{project_id}/issues/{issue_id}/comments/
GET    /api/projects/{project_id}/issues/{issue_id}/comments/{comment_id}/
PUT    /api/projects/{project_id}/issues/{issue_id}/comments/{comment_id}/
DELETE /api/projects/{project_id}/issues/{issue_id}/comments/{comment_id}/
```

## 9. Ordre de réalisation

1. Initialiser Django, Django REST Framework, Poetry et Git.
2. Créer le modèle utilisateur personnalisé avant les premières migrations.
3. Implémenter Project puis Contributor.
4. Implémenter Issue puis Comment.
5. Ajouter JWT et les permissions.
6. Ajouter pagination et optimisation des requêtes.
7. Tester chaque fonctionnalité et chaque rôle.
8. Documenter, nettoyer et préparer Postman et la soutenance.

## 10. Définition de « terminé »

Le projet ne sera considéré comme terminé que si :

- chaque point de terminaison attendu fonctionne ;
- les réponses utilisent les bons codes HTTP ;
- les accès interdits renvoient une erreur correcte ;
- les tests automatisés passent ;
- les scénarios Postman sont reproductibles ;
- le README permet une installation locale complète ;
- aucune donnée sensible n'est publiée ;
- chaque fichier important peut être expliqué simplement.
