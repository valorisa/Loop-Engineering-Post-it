# Loop Engineering — Post-it & Template prêt à l'emploi

Ce dépôt est un **post-it technique** : un document de référence autonome et à jour, qui explique ce qu'est le *Loop Engineering* et fournit un template de prompt prêt à copier-coller pour l'utiliser avec un LLM (ChatGPT, Claude, etc.).

Il s'agit avant tout d'une fiche mémo : le concept, un template de prompt, et ses limites connues. Une implémentation exécutable minimale (`loop_engine.py`, Python standard library) est fournie en complément pour les cas où la boucle doit être réellement contrôlée par du code plutôt que par le modèle.

## Pourquoi ce dépôt existe

Quand on travaille avec des agents IA sur des tâches longues (rédaction de contenu, génération de code, audit itératif...), on finit par réécrire le même type d'instructions : "fais la tâche, relis-toi, corrige-toi, continue". Plutôt que de perdre ce prompt dans une conversation qui disparaît, il est versionné ici, avec son historique de corrections.

## Qu'est-ce que le Loop Engineering ?

Le *Loop Engineering* est une technique de prompt engineering qui consiste à demander à un modèle de langage de tenir, dans une seule et même session, deux rôles distincts et de les enchaîner en boucle :

- **[PRODUCTEUR]** : produit un livrable brut à partir d'une tâche donnée.
- **[CONTRÔLEUR QUALITÉ]** : relit ce livrable avec un regard critique, identifie ses défauts, puis le modèle corrige sa propre production.

Ce cycle (produire → critiquer → corriger) se répète tant que l'objectif global n'est pas atteint. L'idée est de faire jouer au modèle un rôle de relecteur exigeant, pour obtenir un résultat plus abouti qu'une simple réponse en un seul passage.

### Analogie simple

Comparez ça à un rédacteur qui écrirait un premier jet, puis endosserait le rôle d'un correcteur strict pour le relire, avant de reprendre la plume pour corriger — le tout, seul, sans attendre de retour extérieur à chaque étape.

### Ce que ce n'est PAS

- Ce n'est **pas** une mémoire persistante native du modèle : si l'outil qui exécute la boucle ne réinjecte pas l'historique à chaque itération, rien n'est réellement "mémorisé" d'un tour à l'autre.
- Ce n'est **pas** un contrôle qualité indépendant : le "Contrôleur" est le même modèle que le "Producteur". Sans critères de validation explicites et mesurables, la critique peut être complaisante.
- Ce n'est **pas** sans risque en autonomie totale : sans plafond d'itérations ni point de contrôle humain, la boucle peut dériver ou tourner indéfiniment.

### Limites du template seul, et comment les contourner

Le template est un prompt : tout ce qu'il demande reste déclaratif. Il n'y a aucun mécanisme pour l'imposer.

| Limite du prompt seul | Conséquence | Contournement dans la version exécutable |
|---|---|---|
| Le Contrôleur est le même modèle, dans le même contexte | Il valide ses propres angles morts (faits, code) | Second appel API, modèle configurable (`critic_model`), idéalement différent |
| Statut et « X % accompli » estimés par le modèle | Arrêt trop tôt ou boucle inutile | Décision calculée par le code : tous les critères pass **et** `check_command` OK |
| « Arrêt forcé » après N itérations | Dépend de la bonne volonté du modèle | Boucle `for` bornée par `max_iterations` |
| Registre « mémorisé » | Se dilue dans la fenêtre de contexte | `registry.json` relu et réécrit (écriture atomique) à chaque itération |
| « Gérez seul la progression » | Dans un chat, le modèle répond une fois puis s'arrête | Le script relance lui-même chaque itération |
| Format de sortie fixe en 4 sections | Contexte gonflé, cases remplies même sans contenu | Sorties séparées : livrable en fichier, état en JSON |

Dans un chat, le template reste utile pour un seul passage « produire puis relire ». Il ne remplace pas une orchestration externe dès que la tâche est longue ou a des effets réels.

## Comment fonctionne le template ci-dessous

1. **Objectif global** : on définit une seule fois la mission finale.
2. **Plafond d'itérations et points de contrôle** : on borne la boucle et on impose une validation humaine avant toute action irréversible.
3. **Boucle Producteur/Contrôleur** : à chaque tour, le modèle produit, puis s'auto-critique contre des critères objectifs définis à l'avance (pas une appréciation vague de type "c'est cohérent").
4. **Registre des skills** : la progression et les règles apprises sont reportées explicitement, avec le mécanisme de persistance précisé pour qu'elles survivent réellement d'une itération à l'autre.
5. **Format de sortie imposé** : chaque itération suit une structure fixe, pour rester lisible et pour permettre de suivre l'avancement d'un coup d'œil.

## Template

Copiez ce bloc, remplissez les champs entre crochets, et collez-le comme prompt système (ou premier message) à un LLM.

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

## Version exécutable (`loop_engine.py`)

Boucle producteur/critique en Python pur (stdlib, Python 3.9+, compatible Windows/PowerShell et Termux). Appelle l'API Anthropic via `urllib` ; aucune dépendance à installer.

> **Statut :** syntaxe vérifiée. Pas encore éprouvé sur des runs réels : à tester sur une tâche à faible enjeu avant tout usage sérieux.

### Principe

À chaque itération :

1. **Producteur** (appel 1) : reçoit l'objectif, les critères, les leçons acquises, le livrable précédent et les défauts à corriger, puis renvoie le livrable complet.
2. **Contrôleur** (appel 2, modèle configurable) : évalue le livrable critère par critère et répond en JSON (`pass`/`fail` + preuve, défauts, leçons).
3. **Vérification optionnelle** : `check_command` (tests, linter...) exécutée sur le livrable ; un code retour non nul bloque la sortie.
4. **Décision par le code** : `ATTEINT` uniquement si aucun critère en échec et vérification OK. Un critère absent de la réponse du contrôleur compte comme échec.
5. **Registre** : état sauvegardé dans `registry.json`.
6. **Point de contrôle humain** toutes les `checkpoint_every` itérations (`input()`), avec possibilité de saisir un retour réinjecté à l'itération suivante. Hors terminal interactif, arrêt en `EN ATTENTE DE VALIDATION`.

### Configuration (`loop_config.example.json`)

| Champ | Rôle |
|---|---|
| `objective` | Mission finale |
| `criteria` | Liste `{id, text}` de critères vérifiables |
| `producer_model` / `critic_model` | Modèles des deux appels |
| `max_iterations` | Plafond appliqué par le code |
| `checkpoint_every` | Fréquence des validations humaines |
| `registry_path` / `output_path` | Fichiers d'état et de livrable |
| `check_command` | Commande shell optionnelle ; le chemin du livrable est dans `$LOOP_DELIVERABLE` |

### Utilisation

```bash
# Linux / Termux
export ANTHROPIC_API_KEY="..."
python loop_engine.py loop_config.example.json
python loop_engine.py loop_config.example.json --resume   # reprise depuis registry.json
```

```powershell
# Windows PowerShell 7
$env:ANTHROPIC_API_KEY = "..."
python loop_engine.py loop_config.example.json
```

Statuts finaux possibles : `ATTEINT - FIN DE LA BOUCLE`, `PLAFOND ATTEINT`, `EN ATTENTE DE VALIDATION`, `ARRETE PAR L'HUMAIN`, ou un message d'erreur API / critique non exploitable. Pour reprendre après `PLAFOND ATTEINT`, augmentez `max_iterations` puis relancez avec `--resume`.

### Limites connues

- Sans `check_command`, le contrôleur reste un LLM : il peut se tromper. Sur du code, branchez des tests.
- `check_command` est exécutée avec `shell=True` : n'y mettez que des commandes de confiance.
- Pas d'étape de planification séparée (« prochaine tâche ») : le producteur reçoit directement les défauts à corriger.
- Fournisseur unique (Anthropic). Pour un contrôleur d'un autre fournisseur, adapter `call_llm`.
- Le coût croît avec le nombre d'itérations (deux appels chacune, avec le livrable complet réinjecté) : fixer un plafond raisonnable.

## Champs à remplir avant utilisation (template prompt)

- Objectif global de la mission.
- Nombre maximal d'itérations (N).
- Fréquence des points de contrôle humains.
- Critères de contrôle qualité, spécifiques à la tâche visée.
- Mécanisme de persistance du Registre des skills.

## Avertissement

Le template fonctionne bien pour de la génération de contenu pur (texte, code sans effet de bord), mais uniquement en un passage ou en quelques tours supervisés. Dès que la tâche est longue ou pilote des outils avec effets réels (écriture de fichiers, appels API, actions sur un dépôt) :

- préférez la version exécutable, où plafond, registre et décision de sortie sont appliqués par le code ;
- gardez les points de contrôle humains actifs ;
- ne laissez jamais la boucle valider seule une action irréversible ;
- ne considérez pas un « critère satisfait » déclaré par le modèle comme une preuve : seule une vérification exécutée en est une.

## Licence

Contenu publié sans garantie, à adapter librement selon vos besoins.
