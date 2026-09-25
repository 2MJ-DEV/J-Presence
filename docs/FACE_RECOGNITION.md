# Detection, enregistrement et reconnaissance des visages

Ce document décrit le fonctionnement réel du pipeline J-Presence.

## 1. Les deux seuils a ne pas confondre

Le projet utilise deux decisions differentes :

### Seuil de detection du visage

Dans `src/face/detector.py`, `InsightFaceDetector` prepare InsightFace avec :

```python
self.app.prepare(ctx_id=0, det_size=(640, 640))
```

Le parametre `det_thresh` n'est pas fourni, donc InsightFace utilise sa valeur par defaut :

```text
det_thresh = 0.50
```

Ce seuil repond a la question :

> « Le modele voit-il un visage suffisamment probable dans cette image ? »

Un score de detection inferieur a `0.50` est ignore par InsightFace. Le modele renvoie ensuite, pour chaque visage conserve :

- `bbox` : rectangle du visage `(x1, y1, x2, y2)` ;
- `det_score` : confiance de detection ;
- `embedding` : representation numerique du visage.

`det_thresh` n'est pas le seuil d'identification d'un etudiant.

### Seuil de reconnaissance d'un etudiant

Dans `.env` :

```env
FACE_RECOGNITION_THRESHOLD=0.55
```

Ce seuil est utilise par `src/face/recognition.py` apres comparaison avec les embeddings de la base.

Il repond a la question :

> « Le visage detecte ressemble-t-il suffisamment a l'un des etudiants enregistres ? »

Le score est une similarite cosinus comprise entre `-1` et `1`, normalement proche de `1` pour deux embeddings du meme visage.

- score `>= 0.55` : etudiant reconnu ;
- score `< 0.55` : visage detecte mais inconnu ;
- aucun visage : aucune comparaison n'est possible.

Les deux seuils ont donc des roles differents :

```text
image -> detection >= 0.50 -> embedding -> comparaison cosinus >= 0.55 -> etudiant connu
```

## 2. Comment le modele detecte un visage

1. La camera du navigateur fournit une image JPEG, ou une photo est envoyee depuis le formulaire d'inscription.
2. FastAPI decode l'image en tableau BGR OpenCV.
3. `FaceAnalysis` du modele `buffalo_l` recherche les visages dans une image preparee avec une taille de detection de `640 x 640`.
4. Pour chaque visage retenu, InsightFace calcule une boite et un score de detection.
5. Le modele de reconnaissance produit un vecteur numerique appele embedding.
6. Le code compare ce vecteur avec les embeddings stockes dans SQLite.

Le modele ne compare donc pas directement les pixels et ne compare pas les noms. Le nom, la promotion, le laboratoire, la machine et le telephone viennent uniquement de la ligne etudiante retrouvee en base.

## 3. Enregistrement d'un etudiant

Le formulaire `/students` accepte une a trois photos. Une photo externe peut etre prise avec un telephone ou une camera adaptee, puis transferee sur le PC.

Pour chaque photo :

1. l'image est decodee ;
2. InsightFace doit trouver exactement un visage ;
3. l'embedding du visage est extrait ;
4. l'embedding est normalise ;
5. les embeddings valides sont moyennes ;
6. la moyenne est normalisee une seconde fois ;
7. le vecteur final est stocke dans `students.face_embedding`.

La table `students` stocke notamment :

```text
id
full_name
promotion
laboratory
machine
phone
face_embedding
```

`face_embedding` est un tableau JSON de nombres. Avec le modele utilise actuellement, il contient generalement 512 valeurs.

Une image avec zero visage ou plusieurs visages est ignoree pour l'inscription. L'etudiant est enregistre si au moins une photo contient exactement un visage valide.

### Conseils pour les photos

- un seul visage par image ;
- visage net et assez grand ;
- lumiere reguliere, sans contre-jour ;
- pas de photo entierement verte, noire ou floue ;
- retirer autant que possible les lunettes tres sombres et les masques ;
- utiliser deux ou trois angles proches plutot qu'une seule photo degradee.

## 4. Reconnaissance depuis la camera

A chaque image envoyee par `/attendance/detect` :

1. le detecteur cherche les visages ;
2. chaque visage recoit un embedding ;
3. le service charge les embeddings des etudiants qui en possedent un ;
4. le code calcule la similarite cosinus avec chaque etudiant ;
5. il conserve le meilleur score ;
6. si le meilleur score atteint `FACE_RECOGNITION_THRESHOLD`, l'etudiant est connu ;
7. le service enregistre alors l'evenement de presence.

Un visage detecte mais inconnu est affiche comme inconnu et ne cree aucune presence.

## 5. Regles de presence

`AttendanceService.record_detection` applique les regles suivantes pour la date du jour :

- aucune ligne pour l'etudiant : creation d'un `check-in` et statut `present` ;
- ligne ouverte depuis moins d'une heure : `already_present` ;
- ligne ouverte depuis au moins une heure : creation du `check-out` et statut `completed` ;
- ligne deja fermee : `already_closed` ;
- detection repetee pendant le delai anti-repetition : `ignored_cooldown`.

Le delai anti-repetition est configure par :

```env
COOLDOWN_SECONDS=10
```

La reconnaissance et l'enregistrement sont donc deux etapes liees mais distinctes :

```text
visage detecte
  -> etudiant reconnu au-dessus de 0.55
  -> AttendanceService
  -> SQLite attendance
  -> affichage dans le journal
```

## 6. Ajuster les seuils

### Rendre la detection plus sensible

Le seuil InsightFace est actuellement implicite (`0.50`) dans `src/face/detector.py`. Pour le rendre explicite et configurable, il faudrait ajouter un parametre `FACE_DETECTION_THRESHOLD` dans la configuration puis le transmettre a `FaceAnalysis.prepare`.

Baisser ce seuil peut detecter davantage de visages, mais augmente les faux positifs et les detections de mauvaise qualite.

### Rendre la reconnaissance plus stricte ou plus tolerante

Modifier `.env` :

```env
FACE_RECOGNITION_THRESHOLD=0.55
```

- augmenter vers `0.60` ou `0.65` : moins de faux matchs, mais davantage de visages inconnus ;
- baisser vers `0.50` : reconnaissance plus tolerante, mais risque accru de confondre deux personnes.

Toute modification du seuil de reconnaissance doit etre testee avec plusieurs photos reelles des etudiants enregistres et des photos d'autres personnes.

## 7. Diagnostic rapide

| Symptome | Cause probable | Verification |
| --- | --- | --- |
| Aucun visage | Image verte, noire, floue ou visage trop petit | Tester une photo nette dans `/students` |
| Visage detecte mais inconnu | Embedding absent ou score sous `0.55` | Verifier `face_embedding` et le score affiche |
| Etudiant reconnu mais journal inchangé | Page non rafraichie ou ancien serveur | Redemarrer Uvicorn et faire `Ctrl + F5` |
| 400 a l'inscription | Aucune photo ne contient exactement un visage | Utiliser une photo nette avec un seul visage |
| Presence deja existante | Regle anti-doublon normale | Consulter `attendance` pour le statut |

Pour verifier la base utilisee par l'application :

```powershell
.\.venv\Scripts\python.exe -c "from src.database.connection import SessionLocal; from src.database.repository import list_students; db=SessionLocal(); print([(s.id, s.full_name, len(s.face_embedding or [])) for s in list_students(db)]); db.close()"
```
