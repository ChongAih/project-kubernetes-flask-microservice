#!/bin/bash

command="$1"
NAMESPACE="flask-microservice-namespace"
CONFIG_YAML="flask_microservice_config.yaml"
DEPLOYMENT_SERVICE_YAML="flask_microservice.yaml"
DEPLOYMENT_POD_NAME_PREFIX="flask-microservice-deployment"

if [ -z "$command" ];then
	command=""
fi;

if [ "$command" = "start" ]; then

  echo "Starting all Kubernetes pods, services and etc..."

  # Create namespace if not exists
  kubectl get namespace | grep -q $NAMESPACE
  if [ "$?" = "1" ]; then
    kubectl create namespace $NAMESPACE
  fi;

  # Create config & secret
  kubectl apply -f $CONFIG_YAML

  # Create docker service
  kubectl apply -f $DEPLOYMENT_SERVICE_YAML

  # Checking pop name
  pod_starting=1
  while [ "$pod_starting" = "1" ]; do
    echo "Pod $DEPLOYMENT_POD_NAME_PREFIX is starting..."
    kubectl get pods -n $NAMESPACE | grep -q $DEPLOYMENT_POD_NAME_PREFIX
    pod_starting=$?
    sleep 2
  done;

  pod_name=$(kubectl get pods -n $NAMESPACE | grep $DEPLOYMENT_POD_NAME_PREFIX | awk '{print $1}')

  # Displaying pod's logs
  pod_running=""
  while [ "$pod_running" != "Running" ]; do
    echo "Pod $DEPLOYMENT_POD_NAME_PREFIX is deploying..."
    pod_running=$(kubectl get pods -n $NAMESPACE | grep "$pod_name" | awk '{print $3}')
    sleep 2
  done;

  kubectl logs -f -n 25 "$pod_name" -n $NAMESPACE

elif [ "$command" = "stop" ]; then

  echo "Stopping and removing all Kubernetes pods, services and etc..."
  kubectl delete -f $CONFIG_YAML
  kubectl delete -f $DEPLOYMENT_SERVICE_YAML
#  kubectl delete namespace $NAMESPACE

  # Ensure proper termination of pod
  pod_terminating=0
  while [ "$pod_terminating" = "0" ]; do
    echo "Pod $DEPLOYMENT_POD_NAME_PREFIX is terminating..."
    kubectl get pods -n $NAMESPACE | grep -q $DEPLOYMENT_POD_NAME_PREFIX
    pod_terminating=$?
    sleep 2
  done;

else

  echo "Invalid 'command' argument given - expecting 'start'/'stop', '$command' given."
  echo "  sh start_external_flask_microservice.sh <command>"
  echo "    - <start | stop> start or stop kubernetes pods, services and etc."
  exit 1

fi;
