# TP DevSecOps – Guide de démarrage

Lisez **`consignes.pdf`** en entier avant de commencer.

Ce README contient uniquement les commandes de mise en route. Tout le reste est dans les consignes.

---

## 1. Vérifier les prérequis

Exécutez les commandes suivantes et vérifiez que chaque outil répond :

```bash
minikube version        # >= 1.32
kubectl version --client # >= 1.28
docker version          # >= 24
trivy --version         # >= 0.50
helm version            # >= 3.12
git --version
```

Si un outil est manquant, installez-le avant de continuer (liens dans `consignes.pdf`).

---

## 2. Démarrer le cluster Kubernetes

```bash
# Créer et démarrer le cluster minikube
minikube start \
  --cpus=2 \
  --memory=3072 \
  --disk-size=15g \
  --driver=docker

# Activer les addons nécessaires
minikube addons enable ingress
minikube addons enable metrics-server

# Vérifier que le cluster est prêt
kubectl get nodes
kubectl get pods -n kube-system
```

> Le cluster est prêt quand le nœud affiche `Ready` et que tous les pods système sont `Running`.

---

## 3. Configurer le runner GitHub Actions

Le pipeline CI/CD utilise un **runner auto-hébergé** sur votre machine pour accéder au cluster minikube local.

**Étapes :**

1. Créez votre dépôt GitHub public : `esgi-devsecops-tp`
2. Allez dans **Settings → Actions → Runners → New self-hosted runner**
3. Sélectionnez votre OS et suivez les instructions affichées par GitHub
4. Démarrez le runner (la commande est affichée par GitHub, elle ressemble à `./run.sh`)
5. Vérifiez que le runner apparaît en statut **Idle** dans l'interface GitHub

> Le runner doit rester actif (terminal ouvert) pendant toute la durée du TP.

---

## 4. Initialiser votre dépôt GitHub

```bash
# Cloner votre dépôt vide
git clone https://github.com/<votre-username>/esgi-devsecops-tp
cd esgi-devsecops-tp

# Copier le code source fourni
cp -r <chemin-vers-ce-kit>/app ./app

# Structure attendue avant de commencer
# esgi-devsecops-tp/
# ├── app/
# │   ├── app.py
# │   ├── requirements.txt
# │   └── templates/
# │       └── index.html
# ├── k8s/              ← à créer
# ├── .github/
# │   └── workflows/
# │       └── ci-cd.yml ← à créer
# └── Dockerfile        ← à créer

git add .
git commit -m "initial: add application source"
git push
```

---

## 5. Configurer l'accès au registre d'images (ghcr.io)

Votre pipeline publie les images sur **GitHub Container Registry** (`ghcr.io`).

```bash
# Créer un Personal Access Token GitHub avec les droits :
# read:packages, write:packages, delete:packages
# → https://github.com/settings/tokens/new

# Ajouter ce token comme secret dans votre dépôt GitHub :
# Settings → Secrets and variables → Actions → New repository secret
# Nom : GITHUB_TOKEN (déjà disponible automatiquement)
# ou créez CR_PAT avec votre token personnel
```

---

## 6. Configurer l'accès kubectl pour le pipeline

Le job `deploy` a besoin d'un kubeconfig pour accéder à votre cluster minikube.

```bash
# Exporter votre kubeconfig actuel
kubectl config view --minify --flatten > kubeconfig-minikube.yaml

# Encoder en base64 pour le stocker comme secret GitHub
cat kubeconfig-minikube.yaml | base64

# Ajouter dans Settings → Secrets → Actions :
# Nom : KUBECONFIG_B64
# Valeur : la sortie base64 ci-dessus
```

> **Important** : supprimez `kubeconfig-minikube.yaml` après avoir copié la valeur — ne le commitez jamais.

---

## 7. Accéder à l'application après déploiement

Une fois vos manifestes Kubernetes déployés :

```bash
# Option A — tunnel minikube (recommandée, macOS/Linux)
minikube tunnel
# Puis ajouter dans /etc/hosts :
# 127.0.0.1  taskmanager.local
# Ouvrir http://taskmanager.local dans le navigateur

# Option B — port-forward direct
kubectl port-forward svc/taskmanager 8080:80 -n taskmanager
# Ouvrir http://localhost:8080 dans le navigateur

# Option C — NodePort
minikube ip   # récupérer l'IP du cluster
# Ouvrir http://<IP_MINIKUBE>:<nodePort> dans le navigateur
```

---

## Structure finale attendue du dépôt

```
esgi-devsecops-tp/
├── app/
│   ├── app.py
│   ├── requirements.txt
│   └── templates/
│       └── index.html
├── k8s/
│   ├── 00-namespace.yaml
│   ├── 01-quota-limitrange.yaml
│   ├── 02-secret.yaml          ← Secret Redis (mot de passe)
│   ├── 03-redis.yaml
│   ├── 04-app.yaml
│   ├── 05-services.yaml
│   ├── 06-ingress.yaml
│   ├── 07-hpa.yaml
│   ├── 08-rbac.yaml
│   └── 09-networkpolicy.yaml
├── .github/
│   └── workflows/
│       └── ci-cd.yml
└── Dockerfile
```

> Appliquez les manifestes dans l'ordre numérique : `kubectl apply -f k8s/` les applique automatiquement dans l'ordre alphabétique.

> La structure exacte est libre — ce qui compte c'est que tout fonctionne et soit lisible.

---

## Rappel des endpoints de l'application

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Interface web |
| `/healthz` | GET | Liveness probe — retourne `{"status": "ok"}` |
| `/readyz` | GET | Readiness probe — `ready` si Redis connecté, `503` sinon |
| `/tasks` | GET | Liste toutes les tâches |
| `/tasks` | POST | Crée une tâche `{"title": "..."}` |
| `/tasks/<id>` | PATCH | Marque une tâche comme faite `{"done": true}` |
| `/tasks/<id>` | DELETE | Supprime une tâche |
