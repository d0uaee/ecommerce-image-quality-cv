# Rapport d'evaluation consolide

## 1. Echantillon pour evaluation humaine

- Nombre d'images dans le template : 50
- CSV template : `C:\Users\ahadj\OneDrive\ecommerce-image-quality\output\reports\human_evaluation_template.csv`
- CSV 2e annotateur : `C:\Users\ahadj\OneDrive\ecommerce-image-quality\output\reports\human_evaluation_template_annotator2.csv`
- Colonne `score_humain` a remplir avec `1`, `0.5` ou `0`.

## 2. Correlation Spearman

- Statut : ok
- Message : Correlation calculee avec succes.
- Nombre d'annotations humaines exploitables : 50
- Spearman rho : 0.7122
- p-value : 0.000000
- Graphe : `C:\Users\ahadj\OneDrive\ecommerce-image-quality\output\reports\spearman_correlation.png`

## 3. Sensibilite par critere

- Statut : ok
- Message : Sensibilite par critere rechargee depuis les CSV existants.
- CSV cible : `C:\Users\ahadj\OneDrive\ecommerce-image-quality\output\reports\full_eval_sensitivity_target.csv`
- CSV matrice complete : `C:\Users\ahadj\OneDrive\ecommerce-image-quality\output\reports\full_eval_sensitivity_matrix.csv`

### Tableau cible

```text
type_degradation    primary_criterion   n  clean_mean  degraded_mean  avg_drop  median_drop  success_rate
        bad_crop effective_resolution 540       52.79          38.59     14.20        10.50         92.96
            blur            sharpness 540       70.99           5.70     65.30        69.22         99.63
            jpeg            sharpness 540       70.99          65.04      5.95         0.00         47.96
          lowres effective_resolution 540       52.79          31.85     20.95        18.80        100.00
    overexposure             exposure 540       35.08          20.73     14.35         4.68         55.56
   underexposure             exposure 540       35.08          42.07     -6.99        -5.91         47.59
```

## 4. Lecture par categorie

```text
            category  n  score_auto_mean  score_humain_mean  spearman_rho  p_value
            clothing 16           0.6344             0.5281      0.670612 0.004465
portable_electronics 18           0.7027             0.5661      0.715907 0.000834
               shoes 16           0.6838             0.6025      0.765028 0.000555
```

### Forces par categorie

- La categorie la plus robuste est `shoes` avec `rho = 0.7650`.
- Les meilleurs cas sont ceux ou le produit principal est bien centre, net et clairement isole du fond.

### Faiblesses par categorie

- La categorie la plus fragile reste `clothing` avec `rho = 0.6706`.
- Les erreurs residuelles viennent surtout des cas ou le produit est grand mais visuellement lisse, ou quand le fond studio perturbe encore la perception de resolution utile.
## 5. Evaluation multi-annotateur

- Images annotees exploitables : 50
- Nombre d'annotateurs : 8
- Echelle detectee : 0..10
- Accord exact moyen : 0.1471
- Accord moyen a tolerance : 0.3754
- Spearman moyen inter-annotateurs : 0.434187
- Spearman score auto vs moyenne humaine : 0.675243

## 6. Test DINO conditionnel

- Statut : ok
- Cas difficiles testes : 8
- Cas ou DINO retourne au moins une region : 0
- CSV detaille : `C:\Users\ahadj\OneDrive\ecommerce-image-quality\output\reports\dino_fallback_cases.csv`
- Ce test compare la saliency par defaut avec DINO sur un petit echantillon de cas difficiles : prioritairement les `human_high_auto_low`, sinon les plus gros desaccords absolus.
- Il sert de preuve experimentale pour la soutenance : le fallback existe, il est testable, mais il n'est active par defaut que si son gain est juge utile.
- Sur cet echantillon, DINO n'apporte pas de region exploitable supplementaire.

## 7. Limites methodologiques

- Les annotations humaines restent subjectives, meme si la moyenne de plusieurs annotateurs reduit ce bruit.
- Le module de coherence utilise un texte neutre en evaluation globale quand la tache porte uniquement sur la qualite photo.
- Les performances restent dependantes du bon crop initial et de la categorie produit.
- Les resultats categories peuvent varier lorsque le nombre d'images annotees reste limite.
