# Sorties generees

## Objectif de cette page

Cette page explique ou trouver les resultats produits par le projet et comment les interpreter. Elle est utile pour un evaluateur qui veut verifier rapidement que le depot contient les elements finaux importants.

## Dossier `output/reports/`

Le dossier `output/reports/` contient les rapports experimentaux et les fichiers de synthese.

| Fichier | Role |
| --- | --- |
| `evaluation_report.md` | Rapport principal avec correlation humaine, sensibilite aux degradations et analyse par categorie. |
| `multi_annotator_report.md` | Rapport de validation multi-annotateurs. |
| `category_evaluation_summary.csv` | Tableau des resultats par categorie. |
| `spearman_correlation.png` | Visualisation de la relation score automatique / score humain. |
| `disagreements.csv` | Cas ou le score automatique et le score humain divergent fortement. |

Ces fichiers servent directement pour la soutenance et la discussion methodologique.

## Dossier `deliverables/`

Le dossier `deliverables/` contient les livrables lisibles par le professeur ou le jury.

| Fichier | Role |
| --- | --- |
| `presentation_soutenance_pfe_zero_shot_1h.pptx` | Presentation PowerPoint detaillee pour une soutenance longue. |
| `presentation_soutenance_1h_guide.md` | Guide oral associe a la presentation. |
| Documents de synthese | Notes et supports courts pour comprendre le projet sans lire tout le code. |

## Documentation HTML

La documentation Read the Docs locale est generee dans :

```text
docs/_build/html/
```

Le fichier principal est :

```text
docs/_build/html/index.html
```

Si le fichier manque, il faut reconstruire la documentation :

```powershell
.\.venv\Scripts\python -m sphinx -b html docs docs\_build\html
```

## Sorties de l'application Streamlit

L'application produit plusieurs informations dans l'interface :

- score global
- sous-scores par critere
- crop selectionne
- coherence image / texte
- recommandations en francais
- recommandations en darija
- debug des regions candidates
- historique de session
- export rapport utilisateur

Ces sorties ne sont pas toutes stockees automatiquement en fichier permanent. Elles sont principalement destinees a l'experience utilisateur et a la demonstration.

## Comment verifier rapidement le projet

Une verification de livraison peut suivre cet ordre :

1. ouvrir `README.md`
2. ouvrir `docs/_build/html/index.html`
3. verifier `output/reports/evaluation_report.md`
4. verifier `output/reports/multi_annotator_report.md`
5. lancer `streamlit run app.py`
6. tester une image de `dataset/originals/`

## Ce qu'il ne faut pas confondre

Les dossiers de build, cache et environnement virtuel ne sont pas des resultats scientifiques. Ils ne doivent pas etre utilises pour juger la methode. Les resultats importants sont les rapports, les metadonnees, la documentation et le code source.
