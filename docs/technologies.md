# Technologies utilisées

## 1. Vue d'ensemble de la stack

J-Presence est une application de gestion des présences dans un laboratoire informatique. Elle combine une API web Python, une interface HTML rendue côté serveur, une base de données locale et un pipeline de reconnaissance faciale.

| Catégorie | Technologie | Rôle dans le projet |
| --- | --- | --- |
| Langage principal | Python 3.11 | Implémenter l'API, la logique métier, la vision, l'accès aux données, les scripts et les tests. |
| Langages web | HTML5, CSS3, JavaScript | Construire l'interface du journal, l'écran d'inscription et l'utilisation de la caméra du navigateur. |
| Framework web | FastAPI | Exposer l'application web et les endpoints REST de présence, d'inscription et de détection. |
| Serveur ASGI | Uvicorn | Lancer l'application FastAPI en développement ou en production légère. |
| Templates | Jinja2 | Générer les pages HTML à partir des données des étudiants et des présences. |
| Base de données | SQLite | Stocker localement les étudiants, les embeddings, les présences et les détections inconnues. |
| ORM | SQLAlchemy | Définir les modèles, créer les tables, gérer les sessions et exécuter les requêtes. |
| Validation | Pydantic et pydantic-settings | Valider les requêtes HTTP et charger la configuration depuis `.env`. |
| Vision par ordinateur | OpenCV (`opencv-python`) | Lire la webcam, décoder les images envoyées par le navigateur, dessiner les détections et encoder les images. |
| Reconnaissance faciale | InsightFace | Détecter les visages et produire leurs représentations numériques, appelées embeddings. |
| Runtime IA | ONNX Runtime | Exécuter les modèles utilisés par InsightFace. |
| Calcul scientifique | NumPy | Manipuler les images et les vecteurs d'embeddings, calculer les moyennes et les similarités. |
| Visualisation et notebooks | Jupyter, JupyterLab, Matplotlib, IPykernel | Explorer et tester progressivement la caméra, la détection, l'embedding et le pipeline complet. |
| Tests | pytest | Vérifier l'inscription faciale, la reconnaissance et les règles de présence. |
| Gestion d'environnement | Conda | Reproduire l'environnement Python défini dans `environment.yml`. |
| Configuration | fichier `.env` | Personnaliser la base, le seuil de reconnaissance, la caméra, le cooldown et le modèle. |

Les dépendances installables sont déclarées dans [environment.yml](../environment.yml).

## 2. Langages de programmation

### Python

Python est le langage principal. Il est utilisé pour :

- démarrer l'application dans [app/main.py](../app/main.py) ;
- définir les routes FastAPI dans [app/routes](../app/routes) ;
- gérer la reconnaissance et les présences dans [src](../src) ;
- manipuler la base de données avec SQLAlchemy ;
- exécuter les scripts de création et d'enregistrement dans [scripts](../scripts) ;
- écrire les tests dans [tests/test_face_attendance.py](../tests/test_face_attendance.py).

### HTML et Jinja2

Les templates HTML sont dans [app/templates](../app/templates). Jinja2 insère les informations fournies par les routes Python : étudiants, présences du jour, historique et visages inconnus.

### CSS

Le fichier [app/static/css/style.css](../app/static/css/style.css) définit la mise en page, les couleurs, les tableaux, les formulaires, les panneaux caméra et le comportement responsive de l'interface.

### JavaScript

Le fichier [app/static/js/main.js](../app/static/js/main.js) fournit les interactions côté navigateur :

- demander l'accès à la webcam avec `getUserMedia` ;
- choisir un périphérique vidéo ;
- capturer périodiquement une image ;
- envoyer cette image à `/attendance/detect` avec `fetch` ;
- afficher les rectangles et les noms sur un canvas ;
- envoyer plusieurs captures pour l'inscription d'un étudiant.

## 3. Framework web et serveur

### FastAPI

FastAPI constitue la couche HTTP. Il fournit notamment :

- les routes HTML du tableau de bord ;
- les endpoints JSON de présence ;
- la validation des données avec les modèles Pydantic ;
- la documentation interactive disponible via `/docs` ;
- l'injection de dépendances pour ouvrir et fermer les sessions SQLAlchemy.

Le point d'entrée est [app/main.py](../app/main.py). Les routes sont regroupées par domaine :

- [app/routes/dashboard.py](../app/routes/dashboard.py) : pages HTML ;
- [app/routes/attendance.py](../app/routes/attendance.py) : détection et présence ;
- [app/routes/students.py](../app/routes/students.py) : gestion des étudiants.

### Uvicorn

Uvicorn sert de serveur ASGI pour exécuter FastAPI. La commande habituelle est :

```powershell
uvicorn app.main:app --reload
```

## 4. Vision par ordinateur et IA

### OpenCV

OpenCV reçoit les images de la webcam et convertit les images encodées par le navigateur en matrices BGR. Il est aussi utilisé par les scripts de caméra et pour produire les images JPEG des visages inconnus.

Les fonctions principales sont regroupées dans [src/camera/webcam.py](../src/camera/webcam.py) et utilisées par [app/routes/attendance.py](../app/routes/attendance.py).

### InsightFace

InsightFace est encapsulé par [src/face/detector.py](../src/face/detector.py). Le composant :

1. charge le modèle configuré, par défaut `buffalo_l` ;
2. prépare le modèle avec un fournisseur d'exécution CPU ;
3. reçoit une image BGR ;
4. retourne les coordonnées du visage, le score de détection et l'embedding.

### Embeddings et similarité cosinus

Un embedding représente un visage sous la forme d'un vecteur numérique. Lors de l'inscription, plusieurs embeddings sont normalisés puis moyennés dans [src/face/registration.py](../src/face/registration.py).

Lors d'une détection, [src/face/recognition.py](../src/face/recognition.py) compare l'embedding observé aux embeddings enregistrés avec une similarité cosinus. Le visage est reconnu seulement si le meilleur score atteint `FACE_RECOGNITION_THRESHOLD`, fixé par défaut à `0.55`.

### ONNX Runtime

ONNX Runtime exécute les modèles machine learning utilisés indirectement par InsightFace. Le projet configure actuellement `CPUExecutionProvider`, donc le pipeline ne dépend pas d'un GPU.

## 5. Données et persistance

### SQLite

La base par défaut est créée dans `data/processed/lab_attendance.db`. Elle contient notamment :

- `students` : identité, promotion, laboratoire, machine, téléphone et embedding ;
- `attendance` : date, heure d'entrée, heure de sortie et statut ;
- `unknown_detections` : date, confiance, zone du visage et image éventuellement conservée.

### SQLAlchemy

Les modèles sont définis dans [src/database/models.py](../src/database/models.py). La connexion, le moteur et les sessions sont centralisés dans [src/database/connection.py](../src/database/connection.py). Les opérations courantes sont regroupées dans [src/database/repository.py](../src/database/repository.py).

SQLAlchemy permet aussi de garantir une seule ligne de présence par étudiant et par jour grâce à la contrainte unique du modèle `Attendance`.

### Pydantic

Les modèles de [app/schemas.py](../app/schemas.py) contrôlent les données entrantes et sortantes :

- champs obligatoires et longueurs maximales d'un étudiant ;
- identifiants positifs pour les actions de présence ;
- images de caméra non vides ;
- embeddings composés de valeurs finies et non nulles.

## 6. Configuration et outils de développement

La configuration runtime se trouve dans [src/config/settings.py](../src/config/settings.py). Les variables principales sont :

| Variable | Valeur par défaut | Fonction |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./data/processed/lab_attendance.db` | URL de connexion à la base. |
| `FACE_RECOGNITION_THRESHOLD` | `0.55` | Score minimal de reconnaissance. |
| `CAMERA_INDEX` | `0` | Index de la webcam utilisée par les scripts OpenCV. |
| `COOLDOWN_SECONDS` | `10` | Délai anti-répétition entre deux détections. |
| `MODEL_NAME` | `buffalo_l` | Modèle InsightFace chargé. |
| `LOG_LEVEL` | `INFO` | Niveau de journalisation prévu par la configuration. |

Les notebooks de [notebooks](../notebooks) servent à expérimenter étape par étape. Les tests automatisés se lancent avec :

```powershell
python -m pytest -q
```

La configuration pytest ajoute la racine du projet au chemin d'import via [pytest.ini](../pytest.ini).

## 7. Résumé des responsabilités

- **Navigateur** : caméra, formulaire, affichage et envoi des images.
- **FastAPI** : HTTP, validation et orchestration des cas d'utilisation.
- **InsightFace/OpenCV/NumPy** : détection, embeddings et traitement d'image.
- **Service de présence** : règles d'entrée, de sortie et de cooldown dans [src/attendance/service.py](../src/attendance/service.py).
- **SQLAlchemy/SQLite** : persistance locale.
- **Jinja2/CSS/JavaScript** : interface du journal et de l'inscription.
- **pytest** : vérification du comportement métier.
