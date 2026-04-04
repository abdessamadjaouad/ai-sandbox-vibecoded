  
  

# Dossier Technique — **Sandbox IA** (PFE / Stage)

  
  

_**But** : proposer une plateforme modulaire et gouvernée pour **tester, comparer, valider et benchmarker** des modèles IA (ML / DL / LLM / RAG / Agentic AI) avant intégration en production._

  
  

  
  

  
  

## Table des matières

  
  

1. [Contexte & objectifs](#1-contexte--objectifs)

2. [Périmètre & critères de succès](#2-périmètre--critères-de-succès)

3. [Architecture cible (4 couches)](#3-architecture-cible-4-couches)

4. [Parcours utilisateurs & fonctionnalités](#4-parcours-utilisateurs--fonctionnalités)

5. [Sélection intelligente des modèles](#5-sélection-intelligente-des-modèles)

6. [Benchmark, métriques & scoring](#6-benchmark-métriques--scoring)

7. [Gouvernance & sécurité](#7-gouvernance--sécurité)

8. [Stack technique & options de déploiement](#8-stack-technique--options-de-déploiement)

9. [Roadmap PFE & livrables](#9-roadmap-pfe--livrables)

10. [Annexes (templates & glossaire)](#10-annexes-templates--glossaire)

  
  

  
  

  
  

## 1. Contexte & objectifs

  
  

L’IA appliquée à des environnements critiques (finance, banque, assurance, secteur public) nécessite un **cadre d’expérimentation** plus strict qu’un simple prototypage en notebooks.

  
  

Dans la pratique, une organisation se pose des questions récurrentes :

  
  

- Quel modèle offre le meilleur compromis **performance / latence / coût** sur un cas d’usage réel ?
    
- Quelle approche est la plus **robuste** face au bruit, au drift, aux outliers, et à la variation du contexte ?
    
- Comment vérifier la **conformité** : traçabilité, audit, contrôle d’accès, explicabilité, biais ?
    

  ``
  

### Objectif général

  
  

Concevoir et réaliser une **Sandbox IA** :

  
  

- **modulaire** : composants remplaçables (vector DB, tracker, runtime LLM, orchestrateur) ;
    
- **configurable** : pondérations du scoring, contraintes (on-prem, RGPD, latence), politiques d’accès ;
    
- **reproductible** : versioning des données + configuration + artefacts ;
    
- **orientée décision** : comparaison multi-modèles + rapport automatique + recommandations.
    

  
  

### Objectifs opérationnels

  
  

La sandbox doit permettre :

  
  

1. Tester des modèles **ML / LLM / Agentic AI** ;
    
2. Évaluer performance, robustesse, coût, latence ;
    
3. Comparer plusieurs architectures (ex : RAG vs fine-tuning ; LLM A vs LLM B) ;
    
4. Mesurer un ROI technique (gain qualité vs coût/latence) ;
    
5. Vérifier conformité (sécurité, biais, explicabilité).
    

  
  

  
  

  
  

## 2. Périmètre & critères de succès

  
  

### Périmètre (MVP industrialisable)

  
  

Le MVP vise une chaîne complète “data → runs → comparaison → rapport”, incluant :

  
  

- Import/validation/versioning datasets ;
    
- Exécution d’expériences (multi-modèles) ;
    
- Tracking (métriques, artefacts, logs) ;
    
- Benchmarking + scoring pondéré ;
    
- Dashboard comparatif ;
    
- Export d’un rapport PDF (ou Markdown) ;
    
- Gouvernance minimale : RBAC/ABAC, audit logs.
    

  
  

### Hors périmètre (extensible)

  
  

- Data catalog complet et gouvernance data avancée ;
    
- FinOps multi-cloud détaillé ;
    
- Déploiement production “massif” (autoscaling complet, HA multi-sites).
    

  
  

### Critères de succès

  
  

- **Reproductibilité** : un run est rejouable à partir du dataset versionné et de la config.
    
- **Comparabilité** : mêmes splits, mêmes pipelines, mêmes métriques.
    
- **Décision** : scoring global et recommandation explicable.
    
- **Gouvernance** : contrôle d’accès + audit + isolation.
    

  
  

  
  

  
  

## 3. Architecture cible (4 couches)

  
  

### 3.1 Vue d’ensemble

  
  

L’architecture se structure en **4 couches** pour séparer les responsabilités (données, modèles, évaluation, gouvernance) et permettre une évolution indépendante.

  
  

[mermaid]

flowchart TB

subgraph L1[Couche 1 — Data Layer]

A1[Ingestion

CSV/JSON/Images/Logs/Emails/PDF]

A2[Validation & Qualité]

A3[Versioning datasets]

A4[Anonymisation / Masquage]

A5[Indexation vectorielle

(embeddings + chunks)]

end

  
  

subgraph L2[Couche 2 — Experiment Layer]

B1[Catalogue de modèles]

B2[Choix approche

ML / DL / LLM / RAG / Agents]

B3[Paramétrage

hyperparams & prompts]

B4[Orchestrateur d'expériences]

B5[Tracking runs

(artefacts, métriques, logs)]

end

  
  

subgraph L3[Couche 3 — Evaluation Layer]

C1[Calcul métriques]

C2[Benchmark interne]

C3[Comparaison multi-modèles]

C4[Score global pondéré]

C5[Rapport automatique]

end

  
  

subgraph L4[Couche 4 — Governance Layer]

D1[RBAC/ABAC + IAM/SSO]

D2[Chiffrement & secrets]

D3[Logs, traçabilité, audit]

D4[Observabilité & monitoring]

D5[Politiques conformité]

end

  
  

A1-->A2-->A3-->A4-->B4

A5-->B2

B1-->B4-->B5-->C1

C1-->C3-->C4-->C5

  
  

D1-. applique .->A1

D2-. applique .->B4

D3-. collecte .->B5

D4-. observe .->C1

D5-. contraint .->C5

  ![[AI-Sandbox-architecture.png]]
  

  
  

### 3.2 Couche 1 — Data Layer (description)

  
  

**Objectif :** rendre les données « prêtes IA » et comparables.

  
  

- Ingestion multi-format ;
    
- Contrôles de qualité (schéma, valeurs manquantes, distribution) ;
    
- Versioning des datasets (et splits train/val/test) ;
    
- Anonymisation/masquage pour champs sensibles ;
    
- Indexation vectorielle pour texte/documents (RAG).
    

  
  

_Sans versioning et segmentation, les résultats ne sont ni reproductibles ni auditables._

  
  

### 3.3 Couche 2 — Experiment Layer (description)

  
  

**Objectif :** exécuter des expériences standardisées en capturant tout le contexte.

  
  

- Catalogue de modèles et runtimes ;
    
- Stratégies : ML, DL, LLM, RAG, Agents ;
    
- Configuration : hyperparamètres, prompts, paramètres d’inférence ;
    
- Orchestration et exécution (jobs) ;
    
- Tracking des runs (artefacts, métriques, code, config, environnements).
    

  
  

### 3.4 Couche 3 — Evaluation Layer (description)

  
  

**Objectif :** mesurer la qualité ET les contraintes systèmes.

  
  

- Métriques par typologie (classification, régression, LLM) ;
    
- Benchmarks internes (données métier) et externes (si pertinent) ;
    
- Comparaison multi-runs, multi-modèles ;
    
- Score global pondéré (paramétrable) ;
    
- Rapport automatique (PDF/MD).
    

  
  

### 3.5 Couche 4 — Governance Layer (description)

  
  

**Objectif :** assurer conformité, sécurité et auditabilité.

  
  

- Contrôle d’accès RBAC/ABAC ;
    
- Chiffrement au repos/en transit + secrets manager ;
    
- Logs et audit (immutables si possible) ;
    
- Observabilité (métriques infra + métriques IA) ;
    
- Politiques de conformité (on-prem, non-exfiltration, etc.).
    

  
  

### 3.6 Flux end-to-end (séquence)

  
  

[mermaid]

sequenceDiagram

autonumber

participant U as Utilisateur

participant UI as UI/API

participant DL as Data Layer

participant EX as Orchestrateur

participant RT as Runtime Modèle

participant EV as Evaluation

participant GOV as Governance

  
  

U->>UI: Déclare cas d'usage + dataset + contraintes

UI->>GOV: Vérifie droits (RBAC/ABAC)

GOV-->>UI: Autorisation OK

UI->>DL: Upload + validation + versioning

DL-->>UI: dataset_id + métadonnées

UI->>EX: Lancement run (dataset_id + config)

EX->>RT: Exécute (train/infer)

RT-->>EX: sorties + artefacts

EX->>EV: Calcule métriques + score

EV-->>EX: résultats + recommandation

EX->>GOV: Journalise (audit)

EX-->>UI: Résumé + lien rapport

UI-->>U: Dashboard comparatif

  
  

  ![[AI-SandBox-Sequence-diag.png]]
  
  

  
  

## 4. Parcours utilisateurs & fonctionnalités

  
  

### 4.1 Parcours A — Comparaison tabulaire (ML supervisé)

  
  

**Scénario :** prédiction d’un risque à partir de données structurées.

  
  

6. Import du dataset, définition de la cible, contrôle qualité ;
    
7. Définition des contraintes (latence max, budget, exigence d’explicabilité) ;
    
8. Exécution d’une batterie de modèles (XGBoost, LightGBM, RF…) ;
    
9. Comparaison via tableau multi-critères ;
    
10. Rapport final (métriques + recommandation + risques).
    

  
  

**Points d’attention :** normalisation du prétraitement ; gestion du déséquilibre de classes ; seuils métier.

  
  

### 4.2 Parcours B — RAG documentaire

  
  

**Scénario :** interroger un corpus (PDF, mails) avec citations et contrôle de fuite.

  
  

11. Ingestion des documents ;
    
12. Segmentation/chunking + classification (sensibilité) ;
    
13. Embeddings + indexation vectorielle ;
    
14. Benchmark de variantes : (chunking × embedder × retriever × LLM) ;
    
15. Évaluation : exact match, hallucinations, latence, coût tokens ;
    
16. Rapport : recommandations de configuration.
    

  
  

**Points d’attention :** politiques de citation obligatoires ; refus en absence de sources ; non-exfiltration.

  
  

### 4.3 Parcours C — Agentic AI (workflow)

  
  

**Scénario :** agent qui orchestre des outils (recherche, extraction, rédaction, ticketing).

  
  

- Isolation des outils et politiques “tool allowlist” ;
    
- Traces détaillées : quelles actions, quels inputs/outputs ;
    
- Mesure : taux de réussite, erreurs, temps moyen, escalade vers humain.
    

  
  

### 4.4 Fonctionnalités MVP (capabilities)

  
  

- **Data** : import, validation, anonymisation, versioning, indexation ;
    
- **Experiments** : définition run, orchestrateur, tracking ;
    
- **Evaluation** : métriques, scoring, comparaison ;
    
- **Reporting** : dashboard + export rapport ;
    
- **Governance** : RBAC/ABAC + audit logs.
    

  
  

  
  

  
  

## 5. Sélection intelligente des modèles

  
  

La sandbox intègre une logique de recommandation du meilleur “candidat” en fonction de :

  
  

- type de données (tabulaire / image / texte / logs) ;
    
- objectif (classification, extraction, génération, QA) ;
    
- contraintes (on-prem, latence, budget, explicabilité) ;
    
- disponibilité infra (CPU/GPU).
    

  
  

[mermaid]

flowchart TD

A[Entrées: type données + objectif + contraintes] --> B{Typologie?}

B -->|Tabulaire| C[ML supervisé

XGBoost/LGBM/CatBoost/RF]

B -->|Images| D[Deep Learning

CNN/YOLO/ViT]

B -->|Texte/Docs| E{Approche?}

E -->|QA sur corpus| F[RAG

Vector DB + Retriever + LLM]

E -->|Génération/Classification| G[LLM / Fine-tuning]

B -->|Workflow| H[Agentic AI

LangGraph/CrewAI/SK]

C --> I[Runs comparatifs]

D --> I

F --> I

G --> I

H --> I

I --> J[Score global & recommandation]

  
  

  ![[AI-Sandbox-model-Selection.png]]
  

  
  

  
  

## 6. Benchmark, métriques & scoring

  
  

### 6.1 Métriques — classification

  
  

- Accuracy, Precision, Recall, F1-score, AUC ;
    
- Courbes ROC/PR ;
    
- Matrice de confusion ;
    
- Mesures par classe (cas classes rares).
    

  
  

### 6.2 Métriques — régression

  
  

- RMSE, MAE, R² ;
    
- Analyse résidus (biais, variance, points extrêmes).
    

  
  

### 6.3 Métriques — LLM / RAG

  
  

- Exact match / similarité ;
    
- Hallucination rate (réponses sans sources) ;
    
- Latence P50/P95 ;
    
- Coût tokens ;
    
- Évaluation humaine sur échantillon (option).
    

  
  

### 6.4 Scoring global pondéré

  
  

Le scoring sert à aligner les résultats sur les priorités métiers.

  
  

[mermaid]

flowchart LR

A[Résultats bruts

(métriques + latence + coût)] --> B[Normalisation 0..1]

B --> C[Poids par cas d'usage]

C --> D[Score global]

D --> E[Classement]

E --> F[Recommandation intégration]

  
  ![[AI-Sandbox-Scoring-global.png]]

  
  

Exemple (modifiable) :

  
  

- Performance : 40%
    
- Robustesse : 20%
    
- Latence : 20%
    
- Coût : 20%
    

  
  

_La sandbox doit gérer les **contraintes bloquantes** : ex. si latence > seuil, modèle pénalisé ou exclu._

  
  

### 6.5 Benchmarks externes (option)

  
  

Les benchmarks publics (GLUE, SuperGLUE, MMLU, HELM, LMSys Arena…) peuvent servir à situer un modèle, mais ne remplacent pas un benchmark métier. Le projet doit documenter :

  
  

- pertinence du benchmark (langue, domaine, tâches) ;
    
- reproductibilité ;
    
- limites d’interprétation.
    

  
  

  
  

  
  

## 7. Gouvernance & sécurité

  
  

### 7.1 Contrôle d’accès (RBAC/ABAC)

  
  

- RBAC : rôles (admin, data-scientist, reviewer, auditor) ;
    
- ABAC : attributs (projet, classification, sensibilité, localisation, environnement).
    

  
  

Exemple : un utilisateur “DS Projet X” ne peut exécuter des runs que sur les datasets du Projet X, avec sensibilité ≤ niveau autorisé.

  
  

### 7.2 Chiffrement & gestion des secrets

  
  

- Chiffrement au repos (disque/objet) ;
    
- Chiffrement en transit (TLS) ;
    
- Secrets manager (Vault/KeyVault) ;
    
- Rotation clés + séparation responsabilités.
    

  
  

### 7.3 Cloisonnement & isolation

  
  

- Isolation par namespace/projet ;
    
- segmentation réseau (deny-by-default) ;
    
- exécution dans runtimes isolés (containers) ;
    
- séparation environnements (sandbox/preprod).
    

  
  

### 7.4 Auditabilité & traçabilité

  
  

Journalisation :

  
  

- accès dataset ;
    
- lancement run + paramètres ;
    
- artefacts produits ;
    
- appels outils (agentic).
    

  
  

Logs exportables et idéalement immuables (append-only).

  
  

### 7.5 Architecture zones (on-prem)

  
  

[mermaid]

flowchart TB

subgraph ZS[Zone Sensible — On-Prem]

D[Datasets sensibles]

V[Vector DB]

L[LLM local]

R[Runtimes isolés]

end


subgraph ZC[Zone Contrôlée — Services internes]

I[IAM/SSO]

A[Audit/Logs]

M[Monitoring]

end

  
  

I-->R

R-->D

R-->V

R-->L

R-->A

R-->M

  
  

  ![[AI-Sandbox-architecture-zone 1.png]]
  

  
  

  
  

## 8. Stack technique & options de déploiement

  
  

### 8.1 Option Open Source (flexible)

  
  

- Orchestration : Kubernetes
    
- API : FastAPI
    
- Tracking : MLflow
    
- Workflows : Argo / Prefect
    
- Vector DB : Weaviate / Chroma
    
- Stockage : MinIO (S3 compatible)
    
- DB : PostgreSQL
    

  
  

**Avantages :** maîtrise, on-prem, pas de lock-in.

  
  

### 8.2 Option Enterprise (sécurisée)

  
  

- Azure ML / SageMaker / Vertex AI
    
- IAM intégré, monitoring, gouvernance
    

  
  

**Avantages :** accélération. 
**Limites :** dépendance fournisseur, contraintes souveraineté.

  
  

### 8.3 Option Hybrid (performance)

  
  

- Ray (distribution)
    
- BentoML (serving)
    
- W&B (tracking)
    
- vLLM (inférence LLM efficace)
    

  
  

### 8.4 Modèles de déploiement

  
  

[mermaid]

flowchart LR

A[On-Prem] -->|données sensibles| B[Sandbox locale]

C[Cloud local certifié] -->|données maîtrisées| B

D[Hybrid] -->|données non sensibles| E[Cloud public]

D -->|sensibles| B

  
  
![[AI-Sandbox-Deploiment-Models.png]]
  
  

  
  

  
  

## 9. Roadmap PFE & livrables

  
  

### 9.1 Plan de réalisation (indicatif)

  
  

[mermaid]

gantt

title Roadmap PFE – Sandbox IA (indicative)

dateFormat YYYY-MM-DD

section Phase 1 — Cadrage

Benchmark marché & exigences :a1, 2026-03-02, 14d

Architecture cible & choix MVP :a2, after a1, 10d

section Phase 2 — MVP Data + Runs

Data layer (ingestion, versioning) :b1, after a2, 20d

Tracking runs (MLflow-like) :b2, after b1, 14d

section Phase 3 — Evaluation & scoring

Metrics + scoring pondéré :c1, after b2, 16d

Dashboards comparatifs :c2, after c1, 14d

section Phase 4 — Gouvernance

RBAC/ABAC + audit logs :d1, after c2, 14d

Mode on-prem & hardening :d2, after d1, 10d

section Phase 5 — Rapport & soutenance

Génération rapport + recommandations :e1, after d2, 10d

Documentation + démo finale :e2, after e1, 7d

![[AI-Sandbox-GANTT 1.png|697]]
  
  

### 9.2 Livrables

  
  

- Étude comparative des plateformes sandbox existantes (tableau + scoring) ;
    
- Spécifications fonctionnelles (Inputs/Outputs) ;
    
- Architecture + schémas ;
    
- MVP exécutable ;
    
- Dashboard comparatif ;
    
- Rapport automatique ;
    
- Documentation d’exploitation ;
    
- Démo reproductible.
    

  
  

### 9.3 Critères d’acceptation (exemples)

  
  

- Rejouer un run à partir d’un dataset versionné ;
    
- Comparer au moins 3 modèles sur le même cas ;
    
- Générer un rapport automatique ;
    
- Accès contrôlé et traçable.
    

  
  

  
  

  
  

## 10. Annexes (templates & glossaire)

  
  

### 10.1 Glossaire

  
  

- **RAG** : Retrieval-Augmented Generation.
    
- **MLOps** : industrialisation du ML.
    
- **LLMOps** : industrialisation des LLM.
    
- **RBAC** : Role-Based Access Control.
    
- **ABAC** : Attribute-Based Access Control.
    

  
  

### 10.2 Template “fiche run”

  
  

[text]

Run ID :

Objectif :

Dataset ID / Version :

Typologie : tabulaire / image / texte

Approche : ML / DL / LLM / RAG / Agent

Modèle(s) testés :

Configuration :

- hyperparams :

- prompt (si LLM) :

- retriever/chunking (si RAG) :

Contraintes : latence, coût, on-prem, conformité

Résultats :

- performance :

- robustesse :

- latence :

- coût :

Score global :

Décision : go / no-go / à approfondir

Risques :

Actions suivantes :

  
  

  
  

### 10.3 Checklist Go/No-Go

  
  

- [ ] Performance ≥ seuil
    
- [ ] Latence ≤ seuil
    
- [ ] Coût ≤ budget
    
- [ ] Explicabilité acceptable
    
- [ ] Conformité (accès, logs, non-exfiltration)
    

  
  

  
  

  
  

**Fin du document**