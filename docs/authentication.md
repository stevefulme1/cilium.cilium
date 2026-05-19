# Authentication

All modules in the `stevefulme1.cilium` collection interact with Kubernetes
clusters to manage Cilium CRDs, ConfigMaps, and Helm releases. Authentication
is configured using standard Kubernetes credentials.

## Methods

### Kubeconfig File (Default)

The default method reads `~/.kube/config`:

```yaml
- name: Use default kubeconfig
  stevefulme1.cilium.cilium_network_policy:
    name: my-policy
    namespace: default
    state: present
```

### Custom Kubeconfig Path

```yaml
- name: Use custom kubeconfig
  stevefulme1.cilium.cilium_network_policy:
    name: my-policy
    namespace: default
    kubeconfig: /path/to/kubeconfig
    context: my-cluster-context
    state: present
```

### Environment Variable

Set `KUBECONFIG` in your environment:

```bash
export KUBECONFIG=/path/to/kubeconfig
```

### In-Cluster Authentication

When running inside a Kubernetes pod (e.g., in Ansible Automation Platform
on OpenShift), in-cluster authentication is used automatically if no
kubeconfig is provided.

### Service Account Token

For CI/CD pipelines, provide a service account token via kubeconfig:

```yaml
- name: Use service account
  stevefulme1.cilium.cilium_status_info:
    kubeconfig: /var/run/secrets/kubernetes.io/serviceaccount/token
```

## Required RBAC Permissions

The service account or user must have permissions to manage Cilium CRDs.
Minimum required ClusterRole:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cilium-ansible-operator
rules:
  - apiGroups: ["cilium.io"]
    resources: ["*"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["configmaps", "secrets", "services", "pods"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["apps"]
    resources: ["daemonsets", "deployments"]
    verbs: ["get", "list", "watch"]
```
