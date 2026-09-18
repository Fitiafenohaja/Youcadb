# Youcadb

[![CI](https://github.com/Fitiafenohaja/Youcadb/actions/workflows/ci.yml/badge.svg)](https://github.com/Fitiafenohaja/Youcadb/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/youcadb)](https://pypi.org/project/youcadb/)
[![Coverage](https://img.shields.io/codecov/c/github/Fitiafenohaja/Youcadb)](https://codecov.io/gh/Fitiafenohaja/Youcadb)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**CLI de diagnostic et de configuration pour bases de données PostgreSQL et MySQL.**

Youcadb analyse votre projet, y détecte le langage et le framework, se connecte à votre
moteur de base de données, crée bases et utilisateurs, puis exécute un diagnostic complet
de l'environnement — le tout depuis une unique interface en ligne de commande.

---

## Fonctionnalités

- **Détection automatique de projet** — analyse `pyproject.toml`, `package.json`,
  `composer.json`, `Gemfile`, `pom.xml`/`build.gradle`, `*.csproj`, `docker-compose.yml`,
  `.env` et en déduit le langage (Python, Node.js, PHP, Ruby, Java, .NET), le framework
  (FastAPI, Django, Express, Laravel, Rails, Spring Boot, ASP.NET Core…), le driver de base
  de données et le moteur recommandé. En présence de plusieurs manifests, les langages
  backend priment sur le front JavaScript ; les projets .NET imbriqués jusqu'à deux niveaux
  (ex. `src/App/App.csproj`) sont pris en compte.
- **Assistant interactif** — parcours guidés pour `init` et `create`, avec valeurs par défaut
  pertinentes et repli clavier pour les terminaux non interactifs.
- **Opérations moteur idempotentes** — crée les bases de données et utilisateurs uniquement
  s'ils n'existent pas encore ; met à jour les mots de passe en toute sécurité.
- **`youcadb doctor`** — vérifie la présence des drivers, la connectivité au serveur,
  l'exposition `0.0.0.0`, les secrets versionnés dans Git, et plus encore.
- **`youcadb config`** — génère un fichier `.env` depuis le `.youcadb.toml` ; inspecte la
  configuration effective.
- **Sécurisé par conception** — signale les mots de passe suivis par Git et les adresses
  d'écoute dangereuses ; n'écrit jamais les identifiants sur la sortie standard.
- **Multiplateforme** — Linux, macOS et Windows (guides d'installation et de démarrage
  natifs, avec repli Docker).

---

## Prérequis

| Exigence | Notes |
|---|---|
| Python ≥ 3.10 (testé jusqu'à 3.14) | |
| PostgreSQL **ou** MySQL | Installation locale ou via Docker |
| `psycopg[binary]` | Requis pour PostgreSQL (`pip install youcadb[postgres]`) |
| `pymysql` | Requis pour MySQL (`pip install youcadb[mysql]`) |

---

## Installation

```bash
pip install youcadb           # CLI de base (sans drivers)
pip install youcadb[postgres] # + psycopg (PostgreSQL)
pip install youcadb[mysql]    # + pymysql (MySQL)
pip install youcadb[all]      # les deux drivers
```

---

## Prise en main rapide

```bash
# Initialise la configuration à la racine du projet
youcadb init --no-interactive

# Crée la base de données de manière interactive (nom, utilisateur, mot de passe)
youcadb create postgres

# Non interactif : noms et hôtes via les options, secrets via variables d'environnement
YOUCADB_PASSWORD=s3cret \
YOUCADB_ADMIN_PASSWORD=postgres \
  youcadb create postgres \
    --name my_app_db \
    --user app_user \
    --no-interactive

# État de la connexion
youcadb status

# Diagnostic complet de l'environnement
youcadb doctor

# Génère .env depuis le .youcadb.toml courant
youcadb config generate

# Affiche la configuration effective
youcadb config show
```

---

## Commandes

| Commande | Description |
|---|---|
| `youcadb` | Affiche l'état du projet ou une invitation à l'initialiser |
| `youcadb init [--no-interactive]` | Détecte le projet et écrit `.youcadb.toml` |
| `youcadb create <engine> [--name ...] [--user ...]` | Crée la base, l'utilisateur et accorde les permissions |
| `youcadb status` | Affiche l'état de la connexion |
| `youcadb doctor` | Diagnostic complet (driver, serveur, config, sécurité) |
| `youcadb config generate [--force]` | Génère `.env` depuis `.youcadb.toml` |
| `youcadb config show` | Affiche la configuration active |

Consultez `youcadb <commande> --help` pour le détail des options.

---

## Configuration

Youcadb enregistre ses réglages dans `.youcadb.toml` à la racine du projet :

```toml
[project]
  name = "myproject"

[database]
  engine = "postgres"
  host   = "localhost"
  port   = 5432
  name   = "myproject"
  user   = "app_user"
  password = "s3cret"   # uniquement si stocké dans le fichier
```

Les fichiers `.env` générés sont ajoutés au `.gitignore` par défaut.

---

## Mots de passe & sécurité

Youcadb n'accepte jamais de secrets via les options de la ligne de commande : les mots de
passe ne peuvent pas fuiter dans l'historique du shell. Ils sont fournis de manière
interactive (saisie masquée) ou via les variables d'environnement en contexte non
interactif :

| Secret | Variable d'environnement |
|---|---|
| Mot de passe de l'utilisateur applicatif | `YOUCADB_PASSWORD` |
| Mot de passe administrateur | `YOUCADB_ADMIN_PASSWORD` |

Les fichiers `.env` générés par `youcadb config generate` sont ignorés par Git, et
`youcadb doctor` émet un avertissement lorsqu'un mot de passe est suivi par Git ou lorsque
la base est exposée sur `0.0.0.0`. Les mots de passe ne sont jamais affichés sur la sortie
standard : `config generate` et `config show` les affichent masqués (`:***`).

---

## Versions de Python

Le projet cible Python ≥ 3.10 et est testé en continu sur **3.10 à 3.14** (Linux), ainsi que
sur **macOS et Windows** (Python 3.14) dans la matrice CI.

- `.python-version` épingle la version de développement (3.14), lue par `uv` et `pyenv`.
- Le code reste rétro-compatible 3.10 (`requires-python = ">=3.10"`,
  `target-version = "py310"` pour `ruff`, `python_version = "3.10"` pour `mypy`).

---

## Développement

```bash
git clone https://github.com/Fitiafenohaja/Youcadb.git
cd Youcadb
uv venv .venv --python 3.14   # ou : python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Passerelles de qualité

```bash
ruff check src tests             # lint
ruff format --check src tests    # format
mypy src/youcadb                 # typage
pytest tests/unit --cov=youcadb  # tests (couverture ≥ 80 % requise)
```

### Tests d'intégration

Définissez les variables d'environnement d'une base réelle, puis lancez :

```bash
export POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
       POSTGRES_USER=postgres  POSTGRES_PASSWORD=postgres
pytest tests/integration/test_postgres.py -v
```

---

## Versions publiées

Pousser un tag `v*.*.*` (ou publier une Release GitHub) déclenche
`.github/workflows/release.yml` et publie sur PyPI via
[Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/) — aucune clé API
n'est stockée dans les secrets.

**Configuration unique (PyPI) :**
1. Ouvrez les [paramètres de publication PyPI](https://pypi.org/manage/account/publishing/)
   → **Add pending publisher**.
2. Renseignez : projet `youcadb`, propriétaire `Fitiafenohaja`, dépôt `Youcadb`,
   workflow `release.yml`, environnement `pypi`.

**Créer une version :**

```bash
git tag v0.2.0
git push origin v0.2.0
```

---

## Contribution

Les contributions sont les bienvenues — voir [CONTRIBUTING.md](CONTRIBUTING.md) pour la mise
en place et les directives.

## Licence

MIT — voir [LICENSE](LICENSE).