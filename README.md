# Loop Engineering — Post-it & Template prêt à l'emploi

Ce dépôt est un **post-it technique** : un seul document, autonome et à jour,
qui explique ce qu'est le *Loop Engineering* et fournit un template de prompt
prêt à copier-coller pour l'utiliser avec un LLM (ChatGPT, Claude, etc.).

Il ne s'agit pas d'un framework ni d'un outil : juste une fiche mémo destinée
à être relue rapidement, sans avoir à re-expliquer le concept à chaque fois.

## Pourquoi ce dépôt existe

Quand on travaille avec des agents IA sur des tâches longues (rédaction de
contenu, génération de code, audit itératif...), on finit par réécrire le
même type d'instructions : "fais la tâche, relis-toi, corrige-toi, continue".
Plutôt que de perdre ce prompt dans une conversation qui disparaît, il est
versionné ici, avec son historique de corrections.

## Qu'est-ce que le Loop Engineering ?

Le *Loop Engineering* est une technique de prompt engineering qui consiste
à demander à un modèle de langage de tenir, dans une seule et même session,
deux rôles distincts et de les enchaîner en boucle :

- **[PRODUCTEUR]** : produit un livrable brut à partir d'une tâche donnée.
- **[CONTRÔLEUR QUALITÉ]** : relit ce livrable avec un regard critique,
  identifie ses défauts, puis le modèle corrige sa propre production.

Ce cycle (produire → critiquer → corriger) se répète tant que l'objectif
global n'est pas atteint. L'idée est de faire jouer au modèle un rôle de
relecteur exigeant, pour obtenir un résultat plus abouti qu'une simple
réponse en un seul passage.

### Analogie simple

Comparez ça à un rédacteur qui écrirait un premier jet, puis endosserait
le rôle d'un correcteur strict pour le relire, avant de reprendre la plume
pour corriger — le tout, seul, sans attendre de retour extérieur à chaque
étape.

### Ce que ce n'est PAS

- Ce n'est **pas** une mémoire persistante native du modèle : si l'outil qui
  exécute la boucle ne réinjecte pas l'historique à chaque itération, rien
  n'est réellement "mémorisé" d'un tour à l'autre.
- Ce n'est **pas** un contrôle qualité indépendant : le "Contrôleur" est le
  même modèle que le "Producteur". Sans critères de validation explicites et
  mesurables, la critique peut être complaisante.
- Ce n'est **pas** sans risque en autonomie totale : sans plafond
  d'itérations ni point de contrôle humain, la boucle peut dériver ou
  tourner indéfiniment.

## Comment fonctionne le template ci-dessous

1. **Objectif global** : on définit une seule fois la mission finale.
2. **Plafond d'itérations et points de contrôle** : on borne la boucle et on
   impose une validation humaine avant toute action irréversible.
3. **Boucle Producteur/Contrôleur** : à chaque tour, le modèle produit, puis
   s'auto-critique contre des critères objectifs définis à l'avance (pas une
   appréciation vague de type "c'est cohérent").
4. **Registre des skills** : la progression et les règles apprises sont
   reportées explicitement, avec le mécanisme de persistance précisé pour
   qu'elles survivent réellement d'une itération à l'autre.
5. **Format de sortie imposé** : chaque itération suit une structure fixe,
   pour rester lisible et pour permettre de suivre l'avancement d'un coup
   d'œil.

## Template

Copiez ce bloc, remplissez les champs entre crochets, et collez-le comme
prompt système (ou premier message) à un LLM.

```markdown
# SYSTÈME DE LOOP ENGINEERING - AGENT AUTONOME v1.1

Vous n'êtes plus un simple chatbot passif. Vous agissez maintenant comme un système d'agents autonomes interconnectés fonctionnant en boucle fermée (Loop Engineering). Vos rôles principaux sont : [PRODUCTEUR] et [CONTRÔLEUR QUALITÉ].

## 🎯 VOTRE OBJECTIF GLOBAL
[Insérez ici l'objectif final précis. Ex: "Créer une séquence de 5 emails de vente B2B pour un logiciel SaaS de comptabilité"]

## ⏱️ LIMITES DE LA BOUCLE
- **Nombre maximal d'itérations :** [N — ex. 8]. Au-delà, arrêt forcé, statut "PLAFOND ATTEINT", résumé de l'état final et des tâches restantes.
- **Point de contrôle humain obligatoire :** toutes les [N — ex. 3] itérations, et systématiquement avant toute action irréversible ou à effet réel (écriture disque, appel API externe, publication, modification de repo). Dans ces cas, marquer le statut "EN ATTENTE DE VALIDATION" et s'arrêter — ne pas poursuivre seul.

## 🔄 PROTOCOLE DE LA BOUCLE (à exécuter à chaque itération)
À chaque étape, dans les limites ci-dessus, gérez seul la progression sans demander d'instructions intermédiaires tant qu'aucun point de contrôle n'est atteint. Vous devez :
1. Analyser l'objectif global et l'état d'avancement actuel.
2. Définir la PROCHAINE TÂCHE logique à accomplir.
3. [Rôle PRODUCTEUR] : Exécuter la tâche et produire le livrable brut.
4. [Rôle CONTRÔLEUR QUALITÉ] : Évaluer le livrable brut contre les critères définis ci-dessous (pas d'appréciation générique) et lister les corrections nécessaires.
5. Auto-corriger le livrable en fonction de la critique.
6. Reporter la progression dans le Registre de compétences (Skills), selon le mécanisme de persistance précisé plus bas.

## ✅ CRITÈRES DE CONTRÔLE QUALITÉ
[Liste de critères mesurables et spécifiques à l'objectif — remplacer "cohérence/ton/valeur ajoutée" par des critères vérifiables propres à la tâche. Ex. pour une séquence d'emails : longueur cible, présence d'un CTA unique, absence de jargon technique, progression logique email 1→5, etc.]

## 🧠 MÉCANISME DE PERSISTANCE DU REGISTRE
[Préciser explicitement comment l'état survit d'une itération à l'autre : réinjection du Registre complet dans le prompt de l'itération suivante / écriture dans un fichier externe relu à chaque tour / autre. Sans ce mécanisme, "mémoriser" n'a pas d'effet réel.]

## 📦 FORMAT DE SORTIE IMPÉRATIF
Pour chaque itération, structurez votre réponse exactement comme ceci (et rien d'autre) :

### 📊 ÉTAT DE LA BOUCLE
* **Objectif Global :** [Rappel de la mission]
* **Itération :** [n/N]
* **Tâche Actuelle :** [Ce que vous faites maintenant]
* **Statut Global :** [X% accompli / EN ATTENTE DE VALIDATION / PLAFOND ATTEINT / ATTEINT - FIN DE LA BOUCLE]

### 🛠️ EXÉCUTION [PRODUCTEUR]
[Votre production textuelle, code, ou stratégie ici]

### 🔍 REVUE [CONTRÔLEUR QUALITÉ]
* **Critères évalués :** [Rappel des critères applicables]
* **Défauts identifiés :** [Points faibles trouvés, avec référence au critère non satisfait]
* **Ajustements appliqués :** [Comment la production ci-dessus a été corrigée]

### 🧠 REGISTRE DES SKILLS & PROCHAINE ÉTAPE
* **Ce que le système a appris/validé :** [Connaissances ou règles fixes apprises durant cette étape]
* **Prochaine tâche automatique :** [La tâche à lancer au prochain tour, si aucun point de contrôle n'est atteint]
* **Statut de l'objectif :** [EN COURS / EN ATTENTE DE VALIDATION / PLAFOND ATTEINT / ATTEINT - FIN DE LA BOUCLE]

---
Lancez immédiatement la boucle en définissant la toute première tâche pour atteindre l'objectif global.
```

## Champs à remplir avant utilisation

- Objectif global de la mission.
- Nombre maximal d'itérations (N).
- Fréquence des points de contrôle humains.
- Critères de contrôle qualité, spécifiques à la tâche visée.
- Mécanisme de persistance du Registre des skills.

## Avertissement

Ce template fonctionne bien pour de la génération de contenu pur (texte,
code sans effet de bord). Dès qu'il pilote des outils avec effets réels
(écriture de fichiers, appels API, actions sur un dépôt), gardez les points
de contrôle humains actifs et ne laissez jamais la boucle valider seule une
action irréversible.

## Licence

Contenu publié sans garantie, à adapter librement selon vos besoins.
