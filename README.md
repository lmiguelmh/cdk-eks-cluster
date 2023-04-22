# Proyecto Integrador DevOps 2023 - 2203

## Grupo 8 - DevOps2203

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
    - Se probó con la versión 1.27, 1.26, 1.25, 1.24, finalmente la versión [1.23.17](https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.23.md#client-binaries) 
    - ![img_2.png](img_2.png)

- No se puede acceder a Kibana con el usuario de Cognito.
    - Posiblemente un error de integración entre UserPool y el IdentityPool. Se añadieron roles y redesplegó.
    - ![img_3.png](img_3.png)

- El despliegue de un manifiesto (service + deployment) falla.
    - Errores de versión de manifiesto. Se corrigió y cambiaron algunos nombres.
    - ![img_4.png](img_4.png)

- Problemas al eliminar el Cluster EKS, al parecer algunas VPCs, IGs y subnets no pueden eliminarse.
    - Un balanceador de carga creado con kubectl (manualmente) no podía ser eliminado. Se identificó el balanceador y tuvo que ser eliminado manualmente, luego el stack pudo ser eliminado.
    - ![img_8.png](img_8.png)
    - ![img_7.png](img_7.png)
    - ![img_6.png](img_6.png)
    - ![img_5.png](img_5.png)
