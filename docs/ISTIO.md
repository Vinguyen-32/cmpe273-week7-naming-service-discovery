# Optional: Service Mesh with Istio

## Concept

In a service mesh, the custom registry is replaced by the mesh's control plane.
Each pod gets an **Envoy sidecar proxy** injected automatically by Istio.

```
Without mesh (this project):
  Client ──discover──▶ Registry ──▶ picks address ──▶ calls Service

With Istio:
  Client ──▶ Envoy Sidecar ──▶ Istio Control Plane (Pilot) ──▶ Envoy Sidecar ──▶ Service
```

## Benefits

| Feature | Custom Registry | Istio |
|---------|----------------|-------|
| Traffic routing | ❌ manual | ✅ VirtualService / DestinationRule |
| Observability | ❌ none | ✅ Kiali, Jaeger, Prometheus |
| mTLS security | ❌ none | ✅ automatic |
| Retries / circuit breaker | ❌ manual | ✅ built-in |
| Canary deployments | ❌ hard | ✅ weight-based routing |

## Minimal Istio Config

### Install
```bash
istioctl install --set profile=demo
kubectl label namespace default istio-injection=enabled
```

### VirtualService — split traffic 50/50
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: hello-service
spec:
  hosts:
  - hello-service
  http:
  - route:
    - destination:
        host: hello-service
        subset: v1
      weight: 50
    - destination:
        host: hello-service
        subset: v2
      weight: 50
```

### DestinationRule — define subsets
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: hello-service
spec:
  host: hello-service
  trafficPolicy:
    loadBalancer:
      simple: RANDOM          # matches this project's client-side behavior
  subsets:
  - name: v1
    labels:
      version: "1"
  - name: v2
    labels:
      version: "2"
```

With this config, applications no longer need to call a registry at all — the mesh handles discovery, load balancing, retries, and mTLS transparently.
