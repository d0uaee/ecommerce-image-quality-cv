# Limites du projet

## Pourquoi documenter les limites ?

Une documentation serieuse ne doit pas presenter le projet comme parfait. Les limites montrent que le scope est compris, que les resultats sont interpretes correctement et que les perspectives futures sont realistes.

## Limites de scope

Le projet couvre trois categories :

- `shoes`
- `clothing`
- `portable_electronics`

Les conclusions ne doivent pas etre generalisees automatiquement a d'autres categories comme meubles, alimentation, bijoux, cosmetiques ou pieces automobiles.

Chaque categorie possede ses propres difficultes visuelles. Par exemple, un vetement peut etre plat, porte par un mannequin ou photographie sur cintre, alors qu'un produit electronique peut contenir beaucoup de texte, reflets ou petits details.

## Limites du zero-shot

Le systeme n'apprend pas directement a partir des annotations humaines. Cela rend la methode plus explicable, mais limite sa capacite a capturer des preferences complexes.

Un modele supervise pourrait potentiellement obtenir de meilleurs resultats si un grand dataset annote etait disponible. En revanche, il serait moins simple a expliquer et plus difficile a reproduire dans le cadre du projet.

## Dependance au texte

Le texte de l'annonce est une source de verite centrale. Si le titre ou la description sont faux, trop courts ou hors sujet, la coherence image / texte peut etre penalisee.

Exemple :

- image : chaussures
- titre : bateau gonflable
- consequence : le systeme peut detecter une incoherence ou generer une assistance annonce prudente

Cette dependance est logique dans un systeme e-commerce, car une annonce doit aligner image et texte.

## Dependance au crop selectionne

Le score final depend de la region produit retenue. Si le selector choisit une zone secondaire, trop petite ou mal centree, certains criteres peuvent etre affectes.

Les ameliorations effectuees ont reduit ce risque, mais il reste important de l'expliquer car le crop est au coeur du pipeline.

## Limites de l'exposition

L'exposition est l'un des criteres les plus difficiles. Une photo sur fond blanc peut sembler surexposee statistiquement tout en restant acceptable visuellement. A l'inverse, une photo sombre peut rester exploitable si le produit est bien visible.

Le projet a donc choisi une interpretation prudente de l'exposition au lieu d'une penalite trop brutale.

## Limites de la coherence image / texte

La coherence image / texte depend de la disponibilite du modele multimodal et de la qualite du texte. Lorsque le modele n'est pas disponible, l'application indique clairement le fallback dans l'interface.

Le fallback local est utile pour garder l'application fonctionnelle, mais il ne doit pas etre presente comme equivalent a un vrai modele vision-langage externe.

## Limites de l'assistant annonce

L'assistant annonce est une extension produit. Il peut fonctionner :

- avec un webhook n8n et un LLM externe
- en fallback local si le webhook n'est pas configure

Le fallback local est volontairement prudent. Il ne peut pas deviner parfaitement un produit complexe. Sa sortie doit etre lue comme une aide a la redaction, pas comme une verite automatique.

## Limites experimentales

Le protocole est solide pour un PFE, mais il reste limite par :

- la taille de l'echantillon humain
- la subjectivite des annotations
- le nombre de categories
- le caractere controle des degradations
- l'absence de test industriel a grande echelle

## Conclusion sur les limites

Ces limites ne diminuent pas l'interet du projet. Elles definissent clairement ce que le systeme fait bien, ce qu'il fait avec prudence et ce qui meriterait une version future plus large.
