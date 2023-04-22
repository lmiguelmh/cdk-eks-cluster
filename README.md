# Proyecto Integrador DevOps 2023 - 2203

## Grupo 8 - DevOps2203

- Luis Miguel Mamani Humpiri
- Carlos Ruiz de la Vega

## Instrucciones

### Despliegue local

```shell
# first, install and configure CDKv2, kubectl 1.23
cdk deploy

# update kube configuration file with information needed to access the newly created cluster
aws eks update-kubeconfig --name cdk-eks-cluster-cluster-eks --region us-west-2 --role-arn arn:aws:iam::719602558560:role/cdk-eks-cluster-cluster-cdkeksclusterclustereksMas-1HSZX33QNI10U

# test kubectl
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
