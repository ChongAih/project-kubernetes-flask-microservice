SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
IMAGE_NAME="flask_microservice"
CONTAINER_NAME=$IMAGE_NAME
TAG_NAME="prod"
FLASK_MICROSERVICE_PORT=5000
FLASK_MICROSERVICE_ENV="prod"
command="$1"

if [ -z "$command" ];then
	command=""
fi;

if [ "$command" = "start" ]; then

  # Remove any running or completed container with the same name
  docker container ls -la -q --filter "name=$CONTAINER_NAME" | grep -q . && docker container stop $CONTAINER_NAME

  # Remove the old image
  docker image ls | grep -q $IMAGE_NAME:$TAG_NAME && docker image rm $IMAGE_NAME:$TAG_NAME

  # Build a new image based on the Dockerfile
  docker build \
    --build-arg FLASK_MICROSERVICE_PORT=$FLASK_MICROSERVICE_PORT \
    --build-arg FLASK_MICROSERVICE_ENV=$FLASK_MICROSERVICE_ENV \
    -t $IMAGE_NAME:$TAG_NAME -f "$SCRIPT_DIR"/Dockerfile .

fi;

cd kubernetes/external_service || exit
sh run_k8s_external_flask_microservice.sh "$command"

