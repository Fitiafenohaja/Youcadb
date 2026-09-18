# Youcadb

**CLI de diagnostic et de configuration pour bases de données PostgreSQL et MySQL.**

Youcadb analyse votre projet, y détecte le langage et le framework, se connecte à votre
moteur de base de données, crée bases et utilisateurs, puis exécute un diagnostic complet
de l'environnement — le tout depuis une unique interface en ligne de commande.

---

## Pourquoi Youcadb ?

Mettre en place une base de données en développement est une tâche répétitive et source
d'erreurs : créer la base, créer l'utilisateur, accorder les droits, rester cohérent avec le
fichier `.env`, puis comprendre pourquoi une connexion échoue… Youcadb automatise tout cela :

- **Un seul outil** pour l'initialisation, la création et le diagnostic — fini le jonglage
  entre `psql`/`mysql`, Docker et les fichiers de configuration.
- **Des commandes sûres et idempotentes** — re-exécutables sans rien casser : la base et
  l'utilisateur ne sont créés que s'ils n'existent pas encore.
- **La détection plutôt que la configuration** — Youcadb lit votre projet (langage,
  framework, drivers) et recommande le moteur adapté (Python, Node.js, PHP, Ruby, Java,
  .NET ; FastAPI, Django, Express, Laravel, Rails, Spring Boot, ASP.NET Core…).
- **La sécurité par défaut** — aucun mot de passe dans l'historique du shell, aucun secret
  affiché sur la sortie standard, et alerte si votre base est exposée sur `0.0.0.0` ou si un
  secret est versionné dans Git.
- **Multiplateforme** — Linux, macOS et Windows, avec des guides d'installation et de
  démarrage natifs et une solution de repli Docker.

---

## Installation

```bash
pip install youcadb           # CLI de base (sans drivers)
pip install youcadb[postgres] # + psycopg (PostgreSQL)
pip install youcadb[mysql]    # + pymysql (MySQL)
pip install youcadb[all]      # les deux drivers
```

Via **pipx** :

```bash
pipx install youcadb          # installation
pipx upgrade youcadb          # mise à jour du paquet
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
```

Consultez `youcadb --help` pour la liste complète des commandes et options.

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

Les mots de passe ne sont jamais affichés sur la sortie standard : `config generate` et
`config show` les affichent masqués (`:***`).

---

## Configuration requise

| Exigence | Notes |
|---|---|
| Python ≥ 3.10 (testé jusqu'à 3.14) | |
| PostgreSQL **ou** MySQL | Installation locale ou via Docker |
| `psycopg[binary]` | Requis pour PostgreSQL (`pip install youcadb[postgres]`) |
| `pymysql` | Requis pour MySQL (`pip install youcadb[mysql]`) |

---

## Licence

MIT — voir [LICENSE](https://github.com/Fitiafenohaja/Youcadb/blob/main/LICENSE).