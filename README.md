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

- Python 3.11 via Anaconda ou Miniconda.
- SQLite, inclus avec Python.
- Une webcam.
- Windows, macOS ou Linux.

## 5. Installation d'Anaconda ou Miniconda

Installer Miniconda si vous voulez une installation legere :

https://docs.conda.io/en/latest/miniconda.html

Apres installation, ouvrir un terminal Anaconda Prompt, PowerShell ou un terminal compatible Conda.

## 6. Creation de l'environnement

```bash
conda env create -f environment.yml
conda activate lab-attendance-ai
python -m ipykernel install --user --name lab-attendance-ai --display-name "lab-attendance-ai"
```

## 7. Configuration SQLite

La base SQLite est un fichier local cree automatiquement dans `data/processed/`.

Puis copier le fichier d'exemple :

```bash
cp .env.example .env
```

Sur Windows PowerShell :

```powershell
Copy-Item .env.example .env
```

Modifier ensuite `DATABASE_URL` dans `.env` si necessaire :

```env
DATABASE_URL=sqlite:///./data/processed/lab_attendance.db
```

## 8. Creation des tables

Quand `.env` est configure :

```bash
python -m scripts.create_database
```

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
