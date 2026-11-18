# SoftDesk API

API REST sécurisée de suivi de projets techniques, développée avec Django et
Django REST Framework.

## Fonctionnalités

- inscription conforme aux règles du projet : âge minimal de 15 ans et choix de
  consentement ;
- authentification par jetons JWT d'accès et de renouvellement ;
- consultation, rectification et suppression de son propre profil ;
- création et gestion de projets ;
- ajout et retrait de contributeurs par l'auteur du projet ;
- création et gestion d'issues et de commentaires ;
- accès aux ressources réservé aux contributeurs du projet ;
- modification et suppression d'une ressource réservées à son auteur ;
- pagination de toutes les listes ;
- requêtes optimisées avec `select_related` ;
- tests automatisés des fonctionnalités, rôles et accès interdits.

## Technologies

- Python 3.11 ;
- Django 5.2 ;
- Django REST Framework 3.18 ;
- Simple JWT 5.5 ;
- SQLite ;
- Poetry ;
- Ruff.

## Installation locale

### 1. Récupérer le projet

```bash
git clone https://github.com/peytoureaukevin-cloud/SoftDesk.git
cd SoftDesk
```

### 2. Vérifier Python et Poetry

Le projet nécessite Python 3.11 ou une version ultérieure compatible, ainsi que
Poetry. Vérifiez que les deux commandes sont accessibles :

```bash
python3 --version
poetry --version
```

Sous macOS, si le terminal répond `poetry: command not found` alors que Poetry
est déjà installé dans `~/.local/bin`, ajoutez ce dossier au `PATH` de la session :

```bash
export PATH="$HOME/.local/bin:$PATH"
poetry --version
```

Pour conserver cette configuration, ajoutez la ligne suivante au fichier
`~/.zshrc`, puis ouvrez un nouveau terminal :

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Si Poetry n'est pas encore installé, installez-le avant de poursuivre.

### 3. Installer les dépendances

```bash
poetry install --with dev
```

Sur un Mac où Poetry est installé mais absent du `PATH`, la même commande peut
être lancée avec son chemin complet :

```bash
$HOME/.local/bin/poetry install --with dev
```

### 4. Configurer les variables facultatives

Le projet possède des valeurs locales par défaut. Pour les remplacer :

```bash
export DJANGO_SECRET_KEY="une-cle-locale-longue-et-imprevisible"
export DJANGO_DEBUG="True"
export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
```

Le fichier `.env.example` récapitule ces variables. Aucun secret réel ne doit
être ajouté au dépôt Git.

### 5. Préparer la base et démarrer l'API

```bash
poetry run python manage.py migrate
poetry run python manage.py runserver
```

Une fois l'environnement `.venv` créé, ces commandes équivalentes permettent de
lancer Django directement, même si la commande `poetry` n'est pas accessible :

```bash
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py runserver
```

L'API est disponible sur `http://127.0.0.1:8000/`.

## Authentification

### Inscription

```http
POST /api/signup/
Content-Type: application/json

{
  "username": "alice",
  "password": "MotDePasseSolide2026!",
  "age": 30,
  "can_be_contacted": true,
  "can_data_be_shared": false
}
```

### Obtenir les jetons JWT

```http
POST /api/token/
Content-Type: application/json

{
  "username": "alice",
  "password": "MotDePasseSolide2026!"
}
```

La réponse contient un jeton `access` et un jeton `refresh`. Toutes les routes
protégées utilisent l'en-tête suivant :

```http
Authorization: Bearer JETON_ACCESS
```

Le jeton d'accès peut être renouvelé avec `POST /api/token/refresh/`.

## Points de terminaison

### Utilisateur connecté

| Méthode | Adresse | Action |
|---|---|---|
| `POST` | `/api/signup/` | Créer un compte, sans authentification |
| `POST` | `/api/token/` | Obtenir les jetons JWT |
| `POST` | `/api/token/refresh/` | Renouveler le jeton d'accès |
| `GET` | `/api/users/` | Récupérer son profil dans une liste paginée |
| `GET` | `/api/users/{id}/` | Consulter son profil |
| `PATCH` ou `PUT` | `/api/users/{id}/` | Rectifier son profil |
| `DELETE` | `/api/users/{id}/` | Supprimer son compte et ses données liées |

Un utilisateur ne peut ni lister ni consulter les profils des autres.

### Projets

| Méthode | Adresse | Action |
|---|---|---|
| `GET`, `POST` | `/api/projects/` | Lister ses projets ou en créer un |
| `GET` | `/api/projects/{id}/` | Consulter un projet auquel on contribue |
| `PUT`, `PATCH`, `DELETE` | `/api/projects/{id}/` | Gérer un projet dont on est l'auteur |

L'utilisateur connecté devient automatiquement auteur et premier contributeur
du projet qu'il crée.

### Contributeurs

| Méthode | Adresse | Action |
|---|---|---|
| `GET` | `/api/projects/{project_id}/contributors/` | Lister les contributeurs |
| `POST` | `/api/projects/{project_id}/contributors/` | Ajouter un contributeur |
| `GET` | `/api/projects/{project_id}/contributors/{contribution_id}/` | Consulter une participation |
| `DELETE` | `/api/projects/{project_id}/contributors/{contribution_id}/` | Retirer un contributeur |

Seul l'auteur du projet peut ajouter ou retirer des contributeurs. Il ne peut
pas retirer sa propre participation.

### Issues

| Méthode | Adresse | Action |
|---|---|---|
| `GET`, `POST` | `/api/projects/{project_id}/issues/` | Lister ou créer les issues |
| `GET` | `/api/projects/{project_id}/issues/{issue_id}/` | Consulter une issue |
| `PUT`, `PATCH`, `DELETE` | `/api/projects/{project_id}/issues/{issue_id}/` | Gérer une issue dont on est l'auteur |

L'auteur est automatiquement l'utilisateur connecté. La personne assignée doit
être contributrice du projet.

### Commentaires

| Méthode | Adresse | Action |
|---|---|---|
| `GET`, `POST` | `/api/projects/{project_id}/issues/{issue_id}/comments/` | Lister ou créer les commentaires |
| `GET` | `/api/projects/{project_id}/issues/{issue_id}/comments/{uuid}/` | Consulter un commentaire |
| `PUT`, `PATCH`, `DELETE` | `/api/projects/{project_id}/issues/{issue_id}/comments/{uuid}/` | Gérer son commentaire |

## Permissions

| Action | Utilisateur authentifié | Contributeur | Auteur de la ressource |
|---|---:|---:|---:|
| Créer un projet | Oui | Sans objet | Devient auteur |
| Lire un projet, une issue ou un commentaire | Non | Oui | Oui |
| Créer une issue ou un commentaire | Non | Oui | Devient auteur |
| Modifier ou supprimer une ressource | Non | Lecture seule | Oui |
| Ajouter ou retirer un contributeur | Non | Non | Auteur du projet uniquement |

Les listes sont également filtrées : un utilisateur extérieur ne reçoit pas les
projets auxquels il ne contribue pas.

## Pagination

Toutes les listes renvoient au maximum 10 éléments par défaut :

```text
GET /api/projects/?page=2&page_size=5
```

La taille peut être choisie avec `page_size`, dans la limite de 100 éléments. La
réponse contient `count`, `next`, `previous` et `results`.

## Vérification de la qualité

```bash
poetry run python manage.py check
poetry run python manage.py makemigrations --check
poetry run python manage.py test
poetry run ruff check .
poetry run ruff format --check .
```

Les tests couvrent notamment :

- l'âge minimal et le hachage du mot de passe ;
- l'obtention et le renouvellement des JWT ;
- la confidentialité du profil ;
- l'isolation des projets ;
- les droits des contributeurs et des auteurs ;
- les accès refusés aux utilisateurs extérieurs ;
- les règles d'assignation ;
- les UUID des commentaires ;
- la pagination.

La suite actuelle contient 29 tests automatisés.

## Démonstration avec Postman

Importer `postman/SoftDesk_API_complete.postman_collection.json`, démarrer le
serveur, puis exécuter les requêtes dans l'ordre. La collection :

1. crée deux comptes ;
2. obtient et renouvelle les jetons JWT ;
3. crée un projet et ajoute un contributeur ;
4. démontre une lecture autorisée et une modification refusée ;
5. crée une issue et un commentaire ;
6. vérifie qu'un autre utilisateur ne peut pas modifier ce commentaire.

Les anciennes collections des étapes 2 à 4 sont conservées comme historique de
développement, mais elles précèdent l'ajout de JWT et des permissions.

## Structure du projet

```text
config/          configuration, routes principales et pagination
docs/            cadrage et documents officiels
postman/         collections de démonstration
tracker/         projets, contributeurs, issues, commentaires et permissions
users/           modèle utilisateur, inscription et gestion du profil
manage.py        commandes Django
pyproject.toml   dépendances et configuration de Ruff
poetry.lock      versions exactes des dépendances
```

## Sécurité

- les mots de passe sont hachés par Django et ne figurent jamais dans les
  réponses JSON ;
- le client ne choisit pas l'auteur d'une ressource : l'API utilise l'identité
  portée par le JWT ;
- les ressources privées sont filtrées avant leur sérialisation ;
- les secrets sont récupérés depuis les variables d'environnement ;
- les protections HTTPS, HSTS et cookies sécurisés sont activées quand
  `DJANGO_DEBUG=False` ;
- Dependabot peut contrôler régulièrement les dépendances du dépôt GitHub.
