# J-Presence AI

Systeme intelligent de gestion des entrees et sorties des etudiants dans un laboratoire informatique de l'UPL.

Cette version fournit un premier flux fonctionnel : enregistrement d'un étudiant, reconnaissance d'un visage connu, journalisation de l'entrée et de la sortie, API FastAPI et journal HTML.

## 1. Presentation du projet

Le projet remplace le journal papier du laboratoire par un journal numerique. A terme, une camera placee a l'entree detectera les visages, reconnaitra les etudiants deja enregistres, recuperera leurs informations depuis SQLite, puis enregistrera automatiquement les passages.

Important : la camera ne doit pas deviner la promotion, le laboratoire, le telephone ou le type de machine. Ces informations viennent de la base de donnees associee a l'etudiant.

## 2. Fonctionnalites de cette version

- Structure de projet Python professionnelle.
- Fichier `environment.yml` pour creer l'environnement Conda.
- Fichier `.env.example` pour documenter la configuration.
- Configuration centralisee dans `src/config/settings.py`.
- Sept notebooks progressifs de test et d'integration.
- Connexion SQLAlchemy vers SQLite.
- Modeles `students` et `attendance`.
- Script de creation des tables.
- API FastAPI CRUD pour les étudiants et les présences.
- Interface Jinja2 alimentée par le journal SQLite.
- Détection faciale depuis la caméra du navigateur sur le tableau de bord.
- Tests automatisés du cœur de reconnaissance et de présence.

## 3. Architecture

```text
.
├── app/                  # FastAPI, routes, templates Jinja2, fichiers statiques
├── data/                 # Donnees locales de test, non versionnees
├── models/               # Modeles ou artefacts locaux, non versionnes
├── notebooks/            # Experimentations Jupyter progressives
├── scripts/              # Commandes utiles
├── src/                  # Logique reutilisable de production
└── tests/                # Tests futurs
```

Les notebooks servent a apprendre et tester. La logique reutilisable doit vivre dans `src/`.

## 4. Prerequis

- Python 3.11 recommande et requis par le fichier `environment.yml`.
- SQLite, inclus avec Python.
- Une webcam.
- Windows, macOS ou Linux.
- PowerShell ou Anaconda Prompt sur Windows.

> Important : ce projet cible Python 3.11. Les versions plus récentes comme 3.13 peuvent provoquer des incompatibilités de dépendances ou d’imports, notamment pour des bibliothèques comme `insightface` et `onnxruntime`.

## 5. Installation d'Anaconda ou Miniconda

Installer Miniconda si vous voulez une installation legere :

https://docs.conda.io/en/latest/miniconda.html

Apres installation, ouvrir un terminal Anaconda Prompt, PowerShell ou un terminal compatible Conda.

### 5.1. Cas Windows avec Conda

```powershell
# si conda n'est pas reconnu dans PowerShell
& "$env:USERPROFILE\miniconda3\Scripts\conda.exe" init powershell
```

Puis fermer et rouvrir PowerShell, ou exécuter directement :

```powershell
conda env create -f environment.yml
conda activate lab-attendance-ai
python -m ipykernel install --user --name lab-attendance-ai --display-name "lab-attendance-ai"
```

### 5.2. Cas Windows avec un environnement virtuel Python

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install fastapi uvicorn[standard] sqlalchemy pytest pydantic pydantic-settings python-dotenv jinja2 opencv-python numpy matplotlib insightface onnxruntime
```

> Si `py` n'est pas reconnu, installez Python 3.11 depuis python.org ou via Miniconda, puis relancez PowerShell.

## 6. Configuration de l'environnement

La base SQLite est un fichier local cree automatiquement dans `data/processed/`.

Copier le fichier d'exemple :

```powershell
Copy-Item .env.example .env
```

Vérifier le contenu :

```env
DATABASE_URL=sqlite:///./data/processed/lab_attendance.db
FACE_RECOGNITION_THRESHOLD=0.55
CAMERA_INDEX=0
COOLDOWN_SECONDS=10
MODEL_NAME=buffalo_l
LOG_LEVEL=INFO
```

## 7. Vérification de l’installation

```powershell
python -m compileall -q app src scripts tests
python -m pytest -q
```

Ces deux commandes doivent être exécutées depuis l’environnement activé (`conda activate lab-attendance-ai` ou `.venv` activé).

## 8. Creation des tables

Quand `.env` est configure :

```bash
python -m scripts.create_database
```

## 9. Problèmes connus et solutions

- `conda` non reconnu dans PowerShell : exécuter `conda init powershell` puis relancer le terminal.
- `python` non reconnu : installer Python 3.11 ou Miniconda puis réouvrir PowerShell.
- `pytest` absent : vérifier que l’environnement virtuel est activé ou relancer `conda activate lab-attendance-ai`.
- `insightface` ou `onnxruntime` non installés : utiliser Python 3.11 et installer les dépendances depuis `environment.yml` ou la commande `pip install ...` de cette section.
- Sur certains ordinateurs Windows, le téléchargement de modèles `InsightFace` peut être plus lent au premier lancement ; cela reste normal.

## 10. Lancement de Jupyter Notebook

```bash
jupyter notebook
```

Choisir le kernel `lab-attendance-ai`.

Ordre recommande :

1. `notebooks/01_camera_test.ipynb`
2. `notebooks/02_face_detection.ipynb`
3. `notebooks/03_face_embedding.ipynb`
4. `notebooks/04_face_registration.ipynb`
5. `notebooks/05_face_recognition.ipynb`
6. `notebooks/06_attendance_logic.ipynb`
7. `notebooks/07_full_pipeline.ipynb`

## 11. Notebook 01 : test camera

Ce qui est teste :

- ouverture de la webcam ;
- capture d'une image ;
- affichage avec Matplotlib ;
- fermeture propre de la camera.

Ce que vous devez observer :

- une image capturee depuis la webcam ;
- une taille d'image affichee, par exemple `(480, 640, 3)`.

Si la camera ne s'ouvre pas, verifier `CAMERA_INDEX` dans `.env`.

## 12. Notebook 02 : detection de visage

Ce qui est teste :

- chargement d'InsightFace ;
- detection de visages ;
- affichage des bounding boxes ;
- nombre de visages detectes.

Ce que vous devez observer :

- un rectangle autour du visage ;
- un score de confiance de detection ;
- le nombre de visages detectes.

La premiere execution peut etre lente, car InsightFace peut telecharger le modele pre-entraine.

## 13. Lancement de FastAPI

Apres configuration de `.env` :

```bash
uvicorn app.main:app --reload
```

Pages et routes disponibles :

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/students`
- `http://127.0.0.1:8000/attendance`
- `http://127.0.0.1:8000/docs`

API principale :

- `GET/POST /students`
- `GET/DELETE /students/{id}`
- `GET /attendance`
- `GET /attendance/today`
- `POST /attendance/detect` (image caméra encodée en base64)
- `POST /attendance/check-in`
- `POST /attendance/check-out`

## 14. Utilisation de la webcam

La webcam peut être testee dans les notebooks, puis utilisee dans le pipeline de production :

1. verifier que la camera fonctionne ;
2. verifier que la detection fonctionne ;
3. extraire les embeddings ;
4. comparer les embeddings ;
5. enregistrer les passages.

Pour enregistrer un étudiant :

```bash
python -m scripts.register_student --name "Nom Prenom" --promotion "BAC 4 IA" --laboratory IA --machine PERSO --captures 3
```

Pour lancer la reconnaissance :

```bash
python -m scripts.run_camera
```

## 15. Explication de l'architecture

- `src/config/settings.py` lit les variables d'environnement.
- `src/camera/webcam.py` ouvre, lit et ferme la webcam.
- `src/face/detector.py` encapsule InsightFace.
- `src/face/embedding.py` contient les fonctions de comparaison.
- `src/face/recognition.py` compare un visage avec des embeddings connus.
- `src/attendance/session.py` evite les doublons de detection avec un cooldown.
- `src/database/models.py` definit les tables SQLAlchemy.
- `src/face/registration.py` valide les captures et persiste un embedding moyen.
- `src/attendance/service.py` applique le cooldown et les transitions entrée/sortie.
- `app/main.py` monte les routers API et crée le schéma SQLite au démarrage.
- `app/routes/dashboard.py` rend le journal réel avec Jinja2.

## 16. Securite et fiabilite prevues

Les fonctionnalités suivantes restent prévues pour une version durcie :

- liveness detection ;
- anti-spoofing ;
- authentification administrateur ;
- logs applicatifs ;
- audit des modifications ;
- gestion des erreurs camera ;
- export Excel et PDF.

Ces fonctionnalites ne sont pas implementees maintenant pour garder le projet comprehensible.

## 17. Prochaines etapes

1. Ajouter l'authentification administrateur.
2. Ajouter liveness detection et anti-spoofing.
3. Ajouter les migrations et l'audit des modifications.
4. Ajouter les exports Excel et PDF.

Chaque etape devra rester testable separement avant integration.

Resultat attendu :

```text
Database tables created successfully.
```

Les tables creees sont :

- `students`
- `attendance`

La table `attendance.student_id` reference `students.id`.

## 9. Lancement de Jupyter Notebook

```bash
jupyter notebook
```

Choisir le kernel `lab-attendance-ai`.

Ordre recommande :

1. `notebooks/01_camera_test.ipynb`
2. `notebooks/02_face_detection.ipynb`
3. `notebooks/03_face_embedding.ipynb`
4. `notebooks/04_face_registration.ipynb`
5. `notebooks/05_face_recognition.ipynb`
6. `notebooks/06_attendance_logic.ipynb`
7. `notebooks/07_full_pipeline.ipynb`

## 10. Notebook 01 : test camera

Ce qui est teste :

- ouverture de la webcam ;
- capture d'une image ;
- affichage avec Matplotlib ;
- fermeture propre de la camera.

Ce que vous devez observer :

- une image capturee depuis la webcam ;
- une taille d'image affichee, par exemple `(480, 640, 3)`.

Si la camera ne s'ouvre pas, verifier `CAMERA_INDEX` dans `.env`.

## 11. Notebook 02 : detection de visage

Ce qui est teste :

- chargement d'InsightFace ;
- detection de visages ;
- affichage des bounding boxes ;
- nombre de visages detectes.

Ce que vous devez observer :

- un rectangle autour du visage ;
- un score de confiance de detection ;
- le nombre de visages detectes.

La premiere execution peut etre lente, car InsightFace peut telecharger le modele pre-entraine.

## 12. Lancement de FastAPI

Apres configuration de `.env` :

```bash
uvicorn app.main:app --reload
```

Pages et routes disponibles :

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/students`
- `http://127.0.0.1:8000/attendance`
- `http://127.0.0.1:8000/docs`

API principale :

- `GET/POST /students`
- `GET/DELETE /students/{id}`
- `GET /attendance`
- `GET /attendance/today`
- `POST /attendance/check-in`
- `POST /attendance/check-out`

## 13. Utilisation de la webcam

La webcam peut être testee dans les notebooks, puis utilisee dans le pipeline de production :

1. verifier que la camera fonctionne ;
2. verifier que la detection fonctionne ;
3. extraire les embeddings ;
4. comparer les embeddings ;
5. enregistrer les passages.

Pour enregistrer un étudiant :

```bash
python -m scripts.register_student --name "Nom Prenom" --promotion "BAC 4 IA" --laboratory IA --machine PERSO --captures 3
```

Pour lancer la reconnaissance :

```bash
python -m scripts.run_camera
```

## 14. Explication de l'architecture

- `src/config/settings.py` lit les variables d'environnement.
- `src/camera/webcam.py` ouvre, lit et ferme la webcam.
- `src/face/detector.py` encapsule InsightFace.
- `src/face/embedding.py` contient les fonctions de comparaison.
- `src/face/recognition.py` compare un visage avec des embeddings connus.
- `src/attendance/session.py` evite les doublons de detection avec un cooldown.
- `src/database/models.py` definit les tables SQLAlchemy.
- `src/face/registration.py` valide les captures et persiste un embedding moyen.
- `src/attendance/service.py` applique le cooldown et les transitions entrée/sortie.
- `app/main.py` monte les routers API et crée le schéma SQLite au démarrage.
- `app/routes/dashboard.py` rend le journal réel avec Jinja2.

## 15. Securite et fiabilite prevues

Les fonctionnalités suivantes restent prévues pour une version durcie :

- liveness detection ;
- anti-spoofing ;
- authentification administrateur ;
- logs applicatifs ;
- audit des modifications ;
- gestion des erreurs camera ;
- export Excel et PDF.

Ces fonctionnalites ne sont pas implementees maintenant pour garder le projet comprehensible.

## 16. Prochaines etapes

1. Ajouter l'authentification administrateur.
2. Ajouter liveness detection et anti-spoofing.
3. Ajouter les migrations et l'audit des modifications.
4. Ajouter les exports Excel et PDF.

Chaque etape devra rester testable separement avant integration.
