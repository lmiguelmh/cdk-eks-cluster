# Proyecto Integrador DevOps 2203

## Grupo 7 - DevOps2203

- Luis Miguel Mamani Humpiri
- Carlos Ruiz de la Vega
- Reynaldo Capia Capia

## Instrucciones

### Despliegue local

```shell
# first, install and configure CDKv2, kubectl 1.23
cdk deploy

# update kube configuration file with information needed to access the newly created cluster
# this is located on the eks cluster stack output
aws eks update-kubeconfig ...

# test kubectl
kubectl get all

# beware that resources created by kubectl may have to be deleted manually (ie. load balancers)
kubectl apply -f pod.yml
kubectl get pods
# TODO: configure this
# kubectl port-forward nginx-pod 8080:80 --address 0.0.0.0
# curl <pod-ip>
```

### Configuración EKS Cluster

- La definición del cluster se encuentra en [ClusterStack](cluster/component.py).
- Se usó CDK para la creación de la infraestructura.
- La definición del servicio y el despliegue también se encuentra en ClusterStack.

![img_15.png](img_15.png)
![img_16.png](img_16.png)

### Configuración de OpenSearch + Fluent Bit

- La definición del cluster se encuentra en [ClusterLoggingStack](cluster_logging/component.py).
- Se usó CDK para la creación de la infraestructura.
- Se usó autenticación por Cognito User Pools en vez de un Master password.
- El mapping de los roles de ES/fluent-bit se encuentra en [ClusterLoggingRolesStack](cluster_logging_roles/component.py).

```shell
# create fluent-bit
# before, edit the file an change the namespace, cluster endpoint and aws region 
kubectl apply -f fluentbit.yaml

# there should be 3 pods for fluent-bit
kubectl get pods

# cleanup
kubectl delete -f fluentbit.yaml
```

![img_9.png](img_9.png)

![img_10.png](img_10.png)

![img_11.png](img_11.png)

### Configuración de Prometheus + Grafana

```shell
# install helm
# helm 3.9+ breaks some packages, awscliv2 should solve this but in my case didn't
# curl -sSL https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
# installing helm 3.8.2
curl -L https://git.io/get_helm.sh | bash -s -- --version v3.8.2
helm version --short
helm repo add stable https://charts.helm.sh/stable
helm search repo stable

# add prometheus repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
# add grafana repo
helm repo add grafana https://grafana.github.io/helm-charts
# add support for volumes on EBS 
#helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
#helm repo update
#helm upgrade --install aws-ebs-csi-driver --namespace kube-system aws-ebs-csi-driver/aws-ebs-csi-driver
# install eksctl - https://github.com/weaveworks/eksctl/releases/

# test EBS CSI driver
# by creating a StorageClass, a PersistentVolumeClaim (PVC) and a pod
kubectl apply -f dynamic-provisioning/
kubectl delete -f dynamic-provisioning/

# install helm
kubectl create namespace prometheus
helm install prometheus prometheus-community/prometheus \
    --namespace prometheus \
    --set alertmanager.persistentVolume.storageClass="gp2" \
    --set server.persistentVolume.storageClass="gp2"

# check pods
kubectl get pods -n prometheus

# cleanup
helm uninstall prometheus --namespace prometheus
kubectl delete ns prometheus
```

![img_13.png](img_13.png)

### Despliegue usando CI/CD

- TODO: PR to dev

## Problemas

- El despliegue falló porque se llegó al límite de 5 IPs por región.
    - Se solicitó el incremento de número de IPs.
    - ![img.png](img.png)

- El despliegue falló por un error en el manifest.
    - Se eliminó el manifest para culminar el despliegue.
    - ![img_1.png](img_1.png)

- No se pudo usar kubectl desde local.
    - Se eliminó la versión de kubectl 1.26.3-1.
    - Se recreó la carpeta ~/.kube/
    - Se probó con la versión 1.27, 1.26, 1.25, 1.24, finalmente la
      versión [1.23.17](https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.23.md#client-binaries)
    - ![img_2.png](img_2.png)

- No se puede acceder a Kibana con el usuario de Cognito.
    - Posiblemente un error de integración entre UserPool y el IdentityPool. Se añadieron roles y redesplegó.
    - ![img_3.png](img_3.png)

- El despliegue de un manifiesto (service + deployment) falla.
    - Errores de versión de manifiesto. Se corrigió y cambiaron algunos nombres.
    - ![img_4.png](img_4.png)

- Problemas al eliminar el Cluster EKS, al parecer algunas VPCs, IGs y subnets no pueden eliminarse.
    - Un balanceador de carga creado con kubectl (manualmente) no podía ser eliminado. Se identificó el balanceador y tuvo que ser eliminado manualmente, luego
      el stack pudo ser eliminado.
    - ![img_8.png](img_8.png)
    - ![img_7.png](img_7.png)
    - ![img_6.png](img_6.png)
    - ![img_5.png](img_5.png)

- Error al desplegar Prometheus: INSTALLATION FAILED: Kubernetes cluster unreachable: exec plugin: invalid apiVersion "client.authentication.k8s.io/v1alpha1"
    - Al parecer es un problema de Helm 3.9 + AWS cli v1.
    - Instalando AWS cli v2 no funcionó (https://github.com/helm/helm/issues/10975#issuecomment-1132139799)
    - Tuve que revertir y usar la v3.8.2 de Helm.
    - ![img_12.png](img_12.png)

- El pod de helm se queda en _Pending_.
    - ![img_14.png](img_14.png)
    - No hay logs en `kubectl logs -n prometheus pod/prometheus-server-77df547d88-l8rpn -c prometheus-server`.
    - `kubectl describe -n prometheus pods/prometheus-server-77df547d88-bxtdc` no ayuda:
        - ![img_17.png](img_17.png)
    - `kubectl describe pvc -n prometheus` parece un problema de volúmenes. Al parecer no puede crear algun volumen.
        - ![img_18.png](img_18.png)
    - Se instaló aws-ebs-csi-driver, ahora todos los pods en _Pending_.
        - ![img_19.png](img_19.png)
    - Se siguió el siguiente post para [habilitar el almacenamiento persistente en EKS](https://repost.aws/knowledge-center/eks-persistent-storage)
    - Se encontró un problema al crear el ServiceAccount y realizar el despliegue. Solucionado al desinstalar `aws-ebs-csi-driver`, instalado previamente. 
        - ![img_20.png](img_20.png)
    - Se intentó la configuración del despliegue usando el add-on de EKS para el driver EBS CSI. Pero el pod de prueba de AWS se queda en _Pending_.
        - ![img_21.png](img_21.png)
    - Se intentó la [instalación del driver EBS CSI usando helm](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/docs/install.md)
        - ![img_22.png](img_22.png)
        - See below paste of describe pods #1 

### Paste #1 - details of describe pods for EBS CSI using helm

```
(.venv) [lmiguel@lmiguel-pc cdk-eks-cluster]$ kubectl get pod -n kube-system -l "app.kubernetes.io/name=aws-ebs-csi-driver,app.kubernetes.io/instance=aws-ebs-csi-driver"
NAME                                  READY   STATUS    RESTARTS   AGE
ebs-csi-controller-587f5768b4-hfbzl   5/5     Running   0          4m32s
ebs-csi-controller-587f5768b4-rxxfr   0/5     Pending   0          4m32s
ebs-csi-node-wbwjl                    3/3     Running   0          4m33s
(.venv) [lmiguel@lmiguel-pc cdk-eks-cluster]$ kubectl describe pod -n kube-system -l "app.kubernetes.io/name=aws-ebs-csi-driver,app.kubernetes.io/instance=aws-ebs-csi-driver"
Name:                 ebs-csi-controller-587f5768b4-hfbzl
Namespace:            kube-system
Priority:             2000000000
Priority Class Name:  system-cluster-critical
Node:                 ip-10-0-5-253.us-west-2.compute.internal/10.0.5.253
Start Time:           Sun, 23 Apr 2023 16:59:47 -0500
Labels:               app=ebs-csi-controller
                      app.kubernetes.io/component=csi-driver
                      app.kubernetes.io/instance=aws-ebs-csi-driver
                      app.kubernetes.io/managed-by=Helm
                      app.kubernetes.io/name=aws-ebs-csi-driver
                      app.kubernetes.io/version=1.18.0
                      helm.sh/chart=aws-ebs-csi-driver-2.18.0
                      pod-template-hash=587f5768b4
Annotations:          <none>
Status:               Running
IP:                   10.0.9.231
IPs:
  IP:           10.0.9.231
Controlled By:  ReplicaSet/ebs-csi-controller-587f5768b4
Containers:
  ebs-plugin:
    Container ID:  containerd://dcc952421ad3ddf51681f686c3ad0ea2647f9d657b78641ef301a6b5831202ef
    Image:         public.ecr.aws/ebs-csi-driver/aws-ebs-csi-driver:v1.18.0
    Image ID:      public.ecr.aws/ebs-csi-driver/aws-ebs-csi-driver@sha256:2d1ecf57fcfde2403a66e7709ecbb55db6d2bfff64c5c71225c9fb101ffe9c30
    Port:          9808/TCP
    Host Port:     0/TCP
    Args:
      controller
      --endpoint=$(CSI_ENDPOINT)
      --logging-format=text
      --v=2
    State:          Running
      Started:      Sun, 23 Apr 2023 17:00:17 -0500
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:      10m
      memory:   40Mi
    Liveness:   http-get http://:healthz/healthz delay=10s timeout=3s period=10s #success=1 #failure=5
    Readiness:  http-get http://:healthz/healthz delay=10s timeout=3s period=10s #success=1 #failure=5
    Environment:
      CSI_ENDPOINT:           unix:///var/lib/csi/sockets/pluginproxy/csi.sock
      CSI_NODE_NAME:           (v1:spec.nodeName)
      AWS_ACCESS_KEY_ID:      <set to the key 'key_id' in secret 'aws-secret'>      Optional: true
      AWS_SECRET_ACCESS_KEY:  <set to the key 'access_key' in secret 'aws-secret'>  Optional: true
      AWS_EC2_ENDPOINT:       <set to the key 'endpoint' of config map 'aws-meta'>  Optional: true
    Mounts:
      /var/lib/csi/sockets/pluginproxy/ from socket-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-nwpv9 (ro)
  csi-provisioner:
    Container ID:  containerd://dd63a8ebf3d4c751362ea5abe3098c2c7354081780b4d26dca98b1f7ba41bfd3
    Image:         public.ecr.aws/eks-distro/kubernetes-csi/external-provisioner:v3.4.1-eks-1-26-7
    Image ID:      public.ecr.aws/eks-distro/kubernetes-csi/external-provisioner@sha256:adfcb04433d1824f62dde0365877d0f7b7a2eaebc45670cbab7e0c1f07ba0607
    Port:          <none>
    Host Port:     <none>
    Args:
      --csi-address=$(ADDRESS)
      --v=2
      --feature-gates=Topology=true
      --extra-create-metadata
      --leader-election=true
      --default-fstype=ext4
    State:          Running
      Started:      Sun, 23 Apr 2023 17:00:18 -0500
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:     10m
      memory:  40Mi
    Environment:
      ADDRESS:  /var/lib/csi/sockets/pluginproxy/csi.sock
    Mounts:
      /var/lib/csi/sockets/pluginproxy/ from socket-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-nwpv9 (ro)
  csi-attacher:
    Container ID:  containerd://9908ce18cafe556a7176038d8dd931659968adebf57c755009aa09e079819926
    Image:         public.ecr.aws/eks-distro/kubernetes-csi/external-attacher:v4.2.0-eks-1-26-7
    Image ID:      public.ecr.aws/eks-distro/kubernetes-csi/external-attacher@sha256:4b0d6e8758a0213ec942381b9577d2b3e971b545dc9e3fb59973f7992763d85f
    Port:          <none>
    Host Port:     <none>
    Args:
      --csi-address=$(ADDRESS)
      --v=2
      --leader-election=true
    State:          Running
      Started:      Sun, 23 Apr 2023 17:00:19 -0500
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:     10m
      memory:  40Mi
    Environment:
      ADDRESS:  /var/lib/csi/sockets/pluginproxy/csi.sock
    Mounts:
      /var/lib/csi/sockets/pluginproxy/ from socket-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-nwpv9 (ro)
  csi-resizer:
    Container ID:  containerd://ec3939b8e1d0c9994a951f586876cb054057a808cb67f2a9135d0adcc74dd3ff
    Image:         public.ecr.aws/eks-distro/kubernetes-csi/external-resizer:v1.7.0-eks-1-26-7
    Image ID:      public.ecr.aws/eks-distro/kubernetes-csi/external-resizer@sha256:81672f19d1da5cdff8d2068d8d69776067a1e5c31537ab3282d95dff34d581b6
    Port:          <none>
    Host Port:     <none>
    Args:
      --csi-address=$(ADDRESS)
      --v=2
      --handle-volume-inuse-error=false
    State:          Running
      Started:      Sun, 23 Apr 2023 17:00:21 -0500
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:     10m
      memory:  40Mi
    Environment:
      ADDRESS:  /var/lib/csi/sockets/pluginproxy/csi.sock
    Mounts:
      /var/lib/csi/sockets/pluginproxy/ from socket-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-nwpv9 (ro)
  liveness-probe:
    Container ID:  containerd://7c1d2806c17c7a2b0aae5476794c714a5038bc241c12b07881bdf328902548cf
    Image:         public.ecr.aws/eks-distro/kubernetes-csi/livenessprobe:v2.9.0-eks-1-26-7
    Image ID:      public.ecr.aws/eks-distro/kubernetes-csi/livenessprobe@sha256:d9e11b42ae5f4f2f7ea9034e68040997cdbb04ae9e188aa897f76ae92698d78a
    Port:          <none>
    Host Port:     <none>
    Args:
      --csi-address=/csi/csi.sock
    State:          Running
      Started:      Sun, 23 Apr 2023 17:00:21 -0500
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:        10m
      memory:     40Mi
    Environment:  <none>
    Mounts:
      /csi from socket-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-nwpv9 (ro)
Conditions:
  Type              Status
  Initialized       True 
  Ready             True 
  ContainersReady   True 
  PodScheduled      True 
Volumes:
  socket-dir:
    Type:       EmptyDir (a temporary directory that shares a pod's lifetime)
    Medium:     
    SizeLimit:  <unset>
  kube-api-access-nwpv9:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    ConfigMapOptional:       <nil>
    DownwardAPI:             true
QoS Class:                   Burstable
Node-Selectors:              kubernetes.io/os=linux
Tolerations:                 :NoExecute op=Exists for 300s
                             CriticalAddonsOnly op=Exists
Events:
  Type     Reason                  Age    From               Message
  ----     ------                  ----   ----               -------
  Warning  FailedScheduling        5m17s  default-scheduler  0/1 nodes are available: 1 Too many pods.
  Normal   Scheduled               5m16s  default-scheduler  Successfully assigned kube-system/ebs-csi-controller-587f5768b4-hfbzl to ip-10-0-5-253.us-west-2.compute.internal
  Warning  FailedCreatePodSandBox  5m15s  kubelet            Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox "2a4511fe09fa396c41e1bc7af6a440e76d9c68b7a760f63f6726ae7792c0eccd": plugin type="aws-cni" name="aws-cni" failed (add): add cmd: failed to assign an IP address to container
  Warning  FailedCreatePodSandBox  5m3s   kubelet            Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox "fdd33d45b41609bf67d2001f4f97e09b698905ecc3876e438d7d933c0569d129": plugin type="aws-cni" name="aws-cni" failed (add): add cmd: failed to assign an IP address to container
  Normal   Pulled                  4m47s  kubelet            Container image "public.ecr.aws/ebs-csi-driver/aws-ebs-csi-driver:v1.18.0" already present on machine
  Normal   Created                 4m47s  kubelet            Created container ebs-plugin
  Normal   Started                 4m46s  kubelet            Started container ebs-plugin
  Normal   Pulling                 4m46s  kubelet            Pulling image "public.ecr.aws/eks-distro/kubernetes-csi/external-provisioner:v3.4.1-eks-1-26-7"
  Normal   Pulled                  4m45s  kubelet            Successfully pulled image "public.ecr.aws/eks-distro/kubernetes-csi/external-provisioner:v3.4.1-eks-1-26-7" in 1.315633737s (1.315641898s including waiting)
  Normal   Created                 4m45s  kubelet            Created container csi-provisioner
  Normal   Started                 4m45s  kubelet            Started container csi-provisioner
  Normal   Pulling                 4m45s  kubelet            Pulling image "public.ecr.aws/eks-distro/kubernetes-csi/external-attacher:v4.2.0-eks-1-26-7"
  Normal   Pulled                  4m44s  kubelet            Successfully pulled image "public.ecr.aws/eks-distro/kubernetes-csi/external-attacher:v4.2.0-eks-1-26-7" in 1.256756768s (1.256771962s including waiting)
  Normal   Created                 4m44s  kubelet            Created container csi-attacher
  Normal   Started                 4m44s  kubelet            Started container csi-attacher
  Normal   Pulling                 4m44s  kubelet            Pulling image "public.ecr.aws/eks-distro/kubernetes-csi/external-resizer:v1.7.0-eks-1-26-7"
  Normal   Pulled                  4m42s  kubelet            Successfully pulled image "public.ecr.aws/eks-distro/kubernetes-csi/external-resizer:v1.7.0-eks-1-26-7" in 1.322026888s (1.322036914s including waiting)
  Normal   Created                 4m42s  kubelet            Created container csi-resizer
  Normal   Started                 4m42s  kubelet            Started container csi-resizer
  Normal   Pulled                  4m42s  kubelet            Container image "public.ecr.aws/eks-distro/kubernetes-csi/livenessprobe:v2.9.0-eks-1-26-7" already present on machine
  Normal   Created                 4m42s  kubelet            Created container liveness-probe
  Normal   Started                 4m42s  kubelet            Started container liveness-probe


Name:                 ebs-csi-controller-587f5768b4-rxxfr
Namespace:            kube-system
Priority:             2000000000
Priority Class Name:  system-cluster-critical
Node:                 <none>
Labels:               app=ebs-csi-controller
                      app.kubernetes.io/component=csi-driver
                      app.kubernetes.io/instance=aws-ebs-csi-driver
                      app.kubernetes.io/managed-by=Helm
                      app.kubernetes.io/name=aws-ebs-csi-driver
                      app.kubernetes.io/version=1.18.0
                      helm.sh/chart=aws-ebs-csi-driver-2.18.0
                      pod-template-hash=587f5768b4
Annotations:          <none>
Status:               Pending
IP:                   
IPs:                  <none>
Controlled By:        ReplicaSet/ebs-csi-controller-587f5768b4
Containers:
  ebs-plugin:
    Image:      public.ecr.aws/ebs-csi-driver/aws-ebs-csi-driver:v1.18.0
    Port:       9808/TCP
    Host Port:  0/TCP
    Args:
      controller
      --endpoint=$(CSI_ENDPOINT)
      --logging-format=text
      --v=2
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:      10m
      memory:   40Mi
    Liveness:   http-get http://:healthz/healthz delay=10s timeout=3s period=10s #success=1 #failure=5
    Readiness:  http-get http://:healthz/healthz delay=10s timeout=3s period=10s #success=1 #failure=5
    Environment:
      CSI_ENDPOINT:           unix:///var/lib/csi/sockets/pluginproxy/csi.sock
      CSI_NODE_NAME:           (v1:spec.nodeName)
      AWS_ACCESS_KEY_ID:      <set to the key 'key_id' in secret 'aws-secret'>      Optional: true
      AWS_SECRET_ACCESS_KEY:  <set to the key 'access_key' in secret 'aws-secret'>  Optional: true
      AWS_EC2_ENDPOINT:       <set to the key 'endpoint' of config map 'aws-meta'>  Optional: true
    Mounts:
      /var/lib/csi/sockets/pluginproxy/ from socket-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-6tjss (ro)
  csi-provisioner:
    Image:      public.ecr.aws/eks-distro/kubernetes-csi/external-provisioner:v3.4.1-eks-1-26-7
    Port:       <none>
    Host Port:  <none>
    Args:
      --csi-address=$(ADDRESS)
      --v=2
      --feature-gates=Topology=true
      --extra-create-metadata
      --leader-election=true
      --default-fstype=ext4
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:     10m
      memory:  40Mi
    Environment:
      ADDRESS:  /var/lib/csi/sockets/pluginproxy/csi.sock
    Mounts:
      /var/lib/csi/sockets/pluginproxy/ from socket-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-6tjss (ro)
  csi-attacher:
    Image:      public.ecr.aws/eks-distro/kubernetes-csi/external-attacher:v4.2.0-eks-1-26-7
    Port:       <none>
    Host Port:  <none>
    Args:
      --csi-address=$(ADDRESS)
      --v=2
      --leader-election=true
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:     10m
      memory:  40Mi
    Environment:
      ADDRESS:  /var/lib/csi/sockets/pluginproxy/csi.sock
    Mounts:
      /var/lib/csi/sockets/pluginproxy/ from socket-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-6tjss (ro)
  csi-resizer:
    Image:      public.ecr.aws/eks-distro/kubernetes-csi/external-resizer:v1.7.0-eks-1-26-7
    Port:       <none>
    Host Port:  <none>
    Args:
      --csi-address=$(ADDRESS)
      --v=2
      --handle-volume-inuse-error=false
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:     10m
      memory:  40Mi
    Environment:
      ADDRESS:  /var/lib/csi/sockets/pluginproxy/csi.sock
    Mounts:
      /var/lib/csi/sockets/pluginproxy/ from socket-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-6tjss (ro)
  liveness-probe:
    Image:      public.ecr.aws/eks-distro/kubernetes-csi/livenessprobe:v2.9.0-eks-1-26-7
    Port:       <none>
    Host Port:  <none>
    Args:
      --csi-address=/csi/csi.sock
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:        10m
      memory:     40Mi
    Environment:  <none>
    Mounts:
      /csi from socket-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-6tjss (ro)
Conditions:
  Type           Status
  PodScheduled   False 
Volumes:
  socket-dir:
    Type:       EmptyDir (a temporary directory that shares a pod's lifetime)
    Medium:     
    SizeLimit:  <unset>
  kube-api-access-6tjss:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    ConfigMapOptional:       <nil>
    DownwardAPI:             true
QoS Class:                   Burstable
Node-Selectors:              kubernetes.io/os=linux
Tolerations:                 :NoExecute op=Exists for 300s
                             CriticalAddonsOnly op=Exists
Events:
  Type     Reason            Age                 From               Message
  ----     ------            ----                ----               -------
  Warning  FailedScheduling  5m17s               default-scheduler  0/1 nodes are available: 1 Too many pods. preemption: 0/1 nodes are available: 1 Too many pods.
  Warning  FailedScheduling  7s (x2 over 5m16s)  default-scheduler  0/1 nodes are available: 1 Too many pods. preemption: 0/1 nodes are available: 1 No preemption victims found for incoming pod.


Name:                 ebs-csi-node-wbwjl
Namespace:            kube-system
Priority:             2000001000
Priority Class Name:  system-node-critical
Node:                 ip-10-0-5-253.us-west-2.compute.internal/10.0.5.253
Start Time:           Sun, 23 Apr 2023 16:59:47 -0500
Labels:               app=ebs-csi-node
                      app.kubernetes.io/component=csi-driver
                      app.kubernetes.io/instance=aws-ebs-csi-driver
                      app.kubernetes.io/managed-by=Helm
                      app.kubernetes.io/name=aws-ebs-csi-driver
                      app.kubernetes.io/version=1.18.0
                      controller-revision-hash=7b74dc74db
                      helm.sh/chart=aws-ebs-csi-driver-2.18.0
                      pod-template-generation=1
Annotations:          <none>
Status:               Running
IP:                   10.0.12.10
IPs:
  IP:           10.0.12.10
Controlled By:  DaemonSet/ebs-csi-node
Containers:
  ebs-plugin:
    Container ID:  containerd://ffc395f303633c0fa738883fdf4b6d5dc2c63babe427e0ce4539f8331ae99b0a
    Image:         public.ecr.aws/ebs-csi-driver/aws-ebs-csi-driver:v1.18.0
    Image ID:      public.ecr.aws/ebs-csi-driver/aws-ebs-csi-driver@sha256:2d1ecf57fcfde2403a66e7709ecbb55db6d2bfff64c5c71225c9fb101ffe9c30
    Port:          9808/TCP
    Host Port:     0/TCP
    Args:
      node
      --endpoint=$(CSI_ENDPOINT)
      --logging-format=text
      --v=2
    State:          Running
      Started:      Sun, 23 Apr 2023 16:59:49 -0500
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:     10m
      memory:  40Mi
    Liveness:  http-get http://:healthz/healthz delay=10s timeout=3s period=10s #success=1 #failure=5
    Environment:
      CSI_ENDPOINT:   unix:/csi/csi.sock
      CSI_NODE_NAME:   (v1:spec.nodeName)
    Mounts:
      /csi from plugin-dir (rw)
      /dev from device-dir (rw)
      /var/lib/kubelet from kubelet-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-2k76l (ro)
  node-driver-registrar:
    Container ID:  containerd://d6d29584f6faa9122817eb150434fa0c12456248824f1736ef0ee667fb61e31d
    Image:         public.ecr.aws/eks-distro/kubernetes-csi/node-driver-registrar:v2.7.0-eks-1-26-7
    Image ID:      public.ecr.aws/eks-distro/kubernetes-csi/node-driver-registrar@sha256:6ad0cae2ae91453f283a44e9b430e475b8a9fa3d606aec9a8b09596fffbcd2c9
    Port:          <none>
    Host Port:     <none>
    Args:
      --csi-address=$(ADDRESS)
      --kubelet-registration-path=$(DRIVER_REG_SOCK_PATH)
      --v=2
    State:          Running
      Started:      Sun, 23 Apr 2023 16:59:50 -0500
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:     10m
      memory:  40Mi
    Liveness:  exec [/csi-node-driver-registrar --kubelet-registration-path=$(DRIVER_REG_SOCK_PATH) --mode=kubelet-registration-probe] delay=30s timeout=15s period=10s #success=1 #failure=3
    Environment:
      ADDRESS:               /csi/csi.sock
      DRIVER_REG_SOCK_PATH:  /var/lib/kubelet/plugins/ebs.csi.aws.com/csi.sock
    Mounts:
      /csi from plugin-dir (rw)
      /registration from registration-dir (rw)
      /var/lib/kubelet/plugins/ebs.csi.aws.com/ from probe-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-2k76l (ro)
  liveness-probe:
    Container ID:  containerd://c0c72cd19d2b2531af8fcf51a3030fa805460903f03534f8d224e8a006b29694
    Image:         public.ecr.aws/eks-distro/kubernetes-csi/livenessprobe:v2.9.0-eks-1-26-7
    Image ID:      public.ecr.aws/eks-distro/kubernetes-csi/livenessprobe@sha256:d9e11b42ae5f4f2f7ea9034e68040997cdbb04ae9e188aa897f76ae92698d78a
    Port:          <none>
    Host Port:     <none>
    Args:
      --csi-address=/csi/csi.sock
    State:          Running
      Started:      Sun, 23 Apr 2023 16:59:51 -0500
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  256Mi
    Requests:
      cpu:        10m
      memory:     40Mi
    Environment:  <none>
    Mounts:
      /csi from plugin-dir (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-2k76l (ro)
Conditions:
  Type              Status
  Initialized       True 
  Ready             True 
  ContainersReady   True 
  PodScheduled      True 
Volumes:
  kubelet-dir:
    Type:          HostPath (bare host directory volume)
    Path:          /var/lib/kubelet
    HostPathType:  Directory
  plugin-dir:
    Type:          HostPath (bare host directory volume)
    Path:          /var/lib/kubelet/plugins/ebs.csi.aws.com/
    HostPathType:  DirectoryOrCreate
  registration-dir:
    Type:          HostPath (bare host directory volume)
    Path:          /var/lib/kubelet/plugins_registry/
    HostPathType:  Directory
  device-dir:
    Type:          HostPath (bare host directory volume)
    Path:          /dev
    HostPathType:  Directory
  probe-dir:
    Type:       EmptyDir (a temporary directory that shares a pod's lifetime)
    Medium:     
    SizeLimit:  <unset>
  kube-api-access-2k76l:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    ConfigMapOptional:       <nil>
    DownwardAPI:             true
QoS Class:                   Burstable
Node-Selectors:              kubernetes.io/os=linux
Tolerations:                 op=Exists
                             node.kubernetes.io/disk-pressure:NoSchedule op=Exists
                             node.kubernetes.io/memory-pressure:NoSchedule op=Exists
                             node.kubernetes.io/not-ready:NoExecute op=Exists
                             node.kubernetes.io/pid-pressure:NoSchedule op=Exists
                             node.kubernetes.io/unreachable:NoExecute op=Exists
                             node.kubernetes.io/unschedulable:NoSchedule op=Exists
Events:
  Type     Reason            Age    From               Message
  ----     ------            ----   ----               -------
  Warning  FailedScheduling  5m19s  default-scheduler  0/1 nodes are available: 1 Too many pods.
  Normal   Scheduled         5m17s  default-scheduler  Successfully assigned kube-system/ebs-csi-node-wbwjl to ip-10-0-5-253.us-west-2.compute.internal
  Normal   Pulling           5m16s  kubelet            Pulling image "public.ecr.aws/ebs-csi-driver/aws-ebs-csi-driver:v1.18.0"
  Normal   Pulled            5m15s  kubelet            Successfully pulled image "public.ecr.aws/ebs-csi-driver/aws-ebs-csi-driver:v1.18.0" in 1.471982937s (1.4720023s including waiting)
  Normal   Created           5m15s  kubelet            Created container ebs-plugin
  Normal   Started           5m15s  kubelet            Started container ebs-plugin
  Normal   Pulling           5m15s  kubelet            Pulling image "public.ecr.aws/eks-distro/kubernetes-csi/node-driver-registrar:v2.7.0-eks-1-26-7"
  Normal   Pulled            5m14s  kubelet            Successfully pulled image "public.ecr.aws/eks-distro/kubernetes-csi/node-driver-registrar:v2.7.0-eks-1-26-7" in 935.199519ms (935.206948ms including waiting)
  Normal   Created           5m14s  kubelet            Created container node-driver-registrar
  Normal   Started           5m14s  kubelet            Started container node-driver-registrar
  Normal   Pulling           5m14s  kubelet            Pulling image "public.ecr.aws/eks-distro/kubernetes-csi/livenessprobe:v2.9.0-eks-1-26-7"
  Normal   Pulled            5m13s  kubelet            Successfully pulled image "public.ecr.aws/eks-distro/kubernetes-csi/livenessprobe:v2.9.0-eks-1-26-7" in 855.546437ms (855.559447ms including waiting)
  Normal   Created           5m13s  kubelet            Created container liveness-probe
  Normal   Started           5m13s  kubelet            Started container liveness-probe
```
