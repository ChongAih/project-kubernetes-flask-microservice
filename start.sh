SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
IMAGE_NAME="flask-microservice"
FLASK_MICROSERVICE_PORT=5000
FLASK_MICROSERVICE_ENV="production"

# Remove any running or completed container with the same name
docker container ls -la -q --filter "name=$IMAGE_NAME" | grep -q . && docker container stop $IMAGE_NAME

# Remove the old image
docker image ls | grep -q $IMAGE_NAME && docker image rm $IMAGE_NAME

# Build a new image based on the Dockerfile
docker build \
  --build-arg FLASK_MICROSERVICE_PORT=$FLASK_MICROSERVICE_PORT \
  --build-arg FLASK_MICROSERVICE_ENV=$FLASK_MICROSERVICE_ENV \
  -t $IMAGE_NAME -f "$SCRIPT_DIR"/Dockerfile .

# Start running image with volume bind-mounted
docker container run \
  -p $FLASK_MICROSERVICE_PORT:$FLASK_MICROSERVICE_PORT \
  -v "$SCRIPT_DIR"/database:/database \
  --rm --name $IMAGE_NAME -d $IMAGE_NAME