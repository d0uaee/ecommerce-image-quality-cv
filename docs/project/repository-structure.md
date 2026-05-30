# Structure du depot

## Vue generale

Le depot est organise pour separer clairement :

- le code applicatif
- la logique du pipeline
- les donnees finales
- les scripts experimentaux
- les rapports
- les livrables academiques
- la documentation Read the Docs

Cette separation facilite la lecture par un developpeur, un professeur ou un jury.

## Arborescence simplifiee

```text
ecommerce-image-quality/
├── app.py
├── config.py
├── README.md
├── DOCUMENTATION.md
├── LIVRABLE_PROF.md
├── src/
├── scripts/
├── dataset/
├── output/
│   └── reports/
├── deliverables/
├── docs/
├── tests/
└── requirements.txt
```

## Fichiers racine

| Fichier | Role |
| --- | --- |
| `app.py` | Application Streamlit principale. |
| `config.py` | Configuration centrale du projet. |
| `README.md` | Presentation rapide et instructions principales. |
| `DOCUMENTATION.md` | Documentation projet historique et synthese. |
| `LIVRABLE_PROF.md` | Indications pour la copie de remise. |
| `requirements.txt` | Dependances Python principales. |

## Dossier `src/`

Le dossier `src/` contient le coeur technique :

- traitement du texte
- generation de regions candidates
- selection du produit
- analyse de qualite
- coherence image / texte
- recommandations
- assistant annonce

Le code applicatif Streamlit appelle ces modules, mais la logique metier reste separee de l'interface.

## Dossier `scripts/`

Le dossier `scripts/` contient les commandes reproductibles :

- construction du dataset final
- generation des degradations
- evaluation globale
- evaluation par categorie
- validation multi-annotateurs
- calibration des poids
- tests experimentaux comme le fallback DINO

Ce dossier est important pour montrer que le projet n'est pas seulement une interface, mais un protocole complet.

## Dossier `dataset/`

Le dossier `dataset/` contient :

- les images originales finales
- les images degradees controlees
- les annotations
- les fichiers de metadonnees

La structure est detaillee dans la page [Dataset final](../data/dataset-overview.md).

## Dossier `output/reports/`

Ce dossier contient les resultats experimentaux. Il doit etre conserve dans la copie de remise car il permet au professeur de verifier les chiffres finaux sans relancer tous les scripts.

## Dossier `deliverables/`

Ce dossier regroupe les supports de presentation, guides et fichiers prets a etre consultes lors de la soutenance.

## Dossier `docs/`

Le dossier `docs/` contient la documentation Read the Docs :

- pages Markdown source
- configuration Sphinx
- requirements de documentation
- build HTML local dans `docs/_build/html/`

La documentation peut etre lue localement ou publiee sur Read the Docs via `.readthedocs.yaml`.

## Principe de nettoyage

Les fichiers anciens, brouillons, caches et dossiers temporaires ne font pas partie du coeur du projet. La version livrable doit privilegier :

- code source utile
- dataset final
- rapports finaux
- documentation
- presentation
- scripts reproductibles

Cette regle evite d'envoyer au professeur un projet lourd, ambigu ou rempli de versions intermediaires.
