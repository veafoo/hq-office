# Resume phase 0 (HQ Office)

Recommandation : pas d'install d'un des trois repos. On prend leurs idees, on construit leger.

On reuse : le modele munder-difflin (un agent = un vrai process `claude`, hooks pour les events, mailbox en fichiers JSON atomiques), le fallback JSONL de pixel-agents (les hooks seuls lachent), les agents markdown facon the-office (deja notre format).

On construit : app web locale (pas Electron), un orchestrateur qui lit une queue de taches et dispatch un agent existant par tache, contrat tache/event en JSON, queue d'approbation avec un flag "irreversible" qui bloque le batch-approve, budget et kill switch par equipe en fichiers, aucune memoire a part le brain.

Les "agent teams" de Claude Code existent (doc officielle verifiee), mais ne tournent pas en mode headless (`claude -p`) : pas la base de notre orchestrateur, a garder pour un sous-cas ponctuel plus tard.

Premiers pas : 1) coder le lecteur d'events (hooks + fallback JSONL) sur un agent reel, 2) le floor UI en lecture seule (phase 1), 3) le contrat de tache + orchestrateur qui dispatch une seule tache (phase 2).

Decisions pour toi : garder le refus de l'auto-commit meme pour l'orchestrateur (munder-difflin et the-office committent tout seuls, nous non) ; taille du budget/cap par equipe a fixer ; est-ce qu'on active `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` un jour ou jamais.

Skippe : pas de clone shahar061/the-office ni munder-difflin lance en vrai (lecture de code seulement, comme demande). Pas teste "agent teams" en live. Incertain : le rebrand harnessmd.com de munder-difflin (mentionne dans plan.md, pas retrouve dans le repo).
