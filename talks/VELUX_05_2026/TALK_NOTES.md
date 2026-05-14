# Runbook — pre-demo checklist

Quick technical setup before running the live demo. Pair with
[`CHEATSHEET.md`](./CHEATSHEET.md) for the per-question reference.

## 30 minutes before

```bash
# 1. Confirm model is pulled
ollama list   # should include qwen2.5:3b

# 2. Stop any old uvicorn, start fresh
pkill -f 'uvicorn app:app'
cd talks/VELUX_05_2026
.venv/bin/uvicorn app:app --app-dir service --port 8000
# Wait for the "model warm-up complete" log line

# 3. Open two browser tabs / windows, both full-screen-ready:
#    a. https://bitecloud.dk/presentations/velux-ai   ← slides
#    b. http://localhost:8000/                        ← live demo
#
#    On the demo tab: click each of the four chips once — confirm
#    clean answers and that the Deployment tab renders. Leave on Demo.
```

If Ollama is slow or unreachable: `USE_MOCK=1` in the env and restart.
The four canned questions answer in milliseconds with deterministic
mock responses.

## Optional — pre-stage a local kind cluster

If you want a real Kubernetes cluster running alongside the demo
(useful for showing `kubectl get pods` output during the deployment
slide), pre-stage it before the talk:

```bash
# 1. Spin up kind with enough memory for ollama
cat <<EOF > /tmp/kind-velux.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            system-reserved: memory=2Gi
EOF
kind create cluster --name velux --config /tmp/kind-velux.yaml

# 2. Build and load the image (kind doesn't pull from your local Docker)
docker build -f talks/VELUX_05_2026/service/Dockerfile \
  -t velux-nl-query:0.1.0 talks/VELUX_05_2026/
kind load docker-image velux-nl-query:0.1.0 --name velux

# 3. Apply
kubectl create namespace nl-query-demo
kubectl apply -k talks/VELUX_05_2026/deploy/base

# 4. Pull the model into the running ollama pod
kubectl -n nl-query-demo rollout status deploy/ollama
kubectl -n nl-query-demo exec deploy/ollama -- ollama pull qwen2.5:3b

# 5. Port-forward and confirm
kubectl -n nl-query-demo port-forward svc/nl-query 8001:80 &
curl -s localhost:8001/healthz | jq
```

During the talk, keep the demo on `:8000` (local uvicorn) for speed.
Use the cluster only for *proof reads* from a terminal beside the
browser:

```bash
kubectl get pods -n nl-query-demo
kubectl describe configmap nl-query-schema -n nl-query-demo | head -40
kubectl logs deploy/nl-query -n nl-query-demo --tail=20
```

Don't drive the live demo through the cluster — image pulls and model
loads on conference wifi are too risky for stage time.

## After the talk

```bash
# Tear down the local cluster if you spun one up
kind delete cluster --name velux

# Stop the demo service
pkill -f 'uvicorn app:app'
```
