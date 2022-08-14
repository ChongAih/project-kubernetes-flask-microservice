## Flask MicroService with Kubernetes

The project aims to deploy a light-weight Flask microservice that allows user
to submit request to perform computation based on the selected model. The microservice
makes use of multiprocessing queue and process to perform computation in parallel.
Besides, the SQLite is used to persist the incoming request to prevent data loss.

The microservice provides 3 APIs:

* evaluate - compute the output based on the user selected model and input
* result - check the result given the task id
* status - check the status given the task id

### Prerequisite

* Install Docker Desktop and enable Kubernetes
* Install pipenv

### Install Dependencies

```
pipenv install Pipfile
```

### Run in Debug Mode

To develop code, the environment can be first activated

```
pipenv shell
```

Unittest can be performed using the following command

```
python -m unittest <path to test folder>/<test>.py
python manage.py --test
```

### Run in Docker

Running the below command will spin up a Docker container and expose localhost:5000
for quick verification of Docker image and functionality

```
sh run_docker.sh
```

Check the logs to investigate the expected behaviour, eg. if the multiprocessing
is working

```
docker container logs -f -n 25 flask-microservice
```

Once verified, the container and its associated volume will be removed

```
docker container stop flask-microservice
```

### Run in Kubernetes

Running the below command will spin up a Kubernetes pod using the same Docker image
as above. There are two options:

* an external service of which the pod will expose
  a port (localhost:30000) for requests to be directed to.
* (ongoing) an internal service of which the pod will
  expose an internal port to only Ingress (with load balancer function) and requests will be
  directed by Ingress to the corresponding interval service container port

The following are the settings in Kubernetes:

* Docker environment variables:
    * FLASK_MICROSERVICE_PORT: 5000
    * FLASK_MICROSERVICE_ENV: prod
* Kubernetes settings:
    * namespace: flask-microservice-namespace

The commands below can be used to run and inspect the Kubernetes

```
sh run_k8s.sh <start / stop>
```

```
kubectl get nodes --> to check # of K8s available nodes
kubectl describe nodes
kubectl get namespace
kubectl get all -n flask-microservice-namespace
kubectl get configmap -o json -n flask-microservice-namespace
kubectl describe svc <service name> -n flask-microservice-namespace
kubectl describe pod <pod name> -n flask-microservice-namespace
kubectl logs -f <pod name> -n flask-microservice-namespace
kubectl get node -o wide -n flask-microservice-namespace 
kubectl get pv -o json -n flask-microservice-namespace
kubectl get pvc -o json -n flask-microservice-namespace
```
