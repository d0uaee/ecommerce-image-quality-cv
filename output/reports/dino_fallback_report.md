# Test DINO fallback

- Statut : ok
- Cas difficiles testes : 8
- Cas ou DINO retourne au moins une region : 0
- CSV detaille : `C:\Users\ahadj\OneDrive\ecommerce-image-quality\output\reports\dino_fallback_cases.csv`

## Lecture

- Ce test compare la saliency par defaut avec DINO sur un petit echantillon de cas difficiles : prioritairement les `human_high_auto_low`, sinon les plus gros desaccords absolus.
- Il sert de preuve experimentale pour la soutenance : le fallback existe, il est testable, mais il n'est active par defaut que si son gain est juge utile.
- Sur cet echantillon, DINO n'apporte pas de region exploitable supplementaire.