if [ "$MODE" == "fresh" -o "$(docker images -q camerapositioner:build 2> /dev/null)" == "" ]
then
    echo "Cloning and building container."
    git pull
    docker build --no-cache . -t camerapositioner:build
fi

docker run -it --rm -w /root/CameraPositioner -v "E:/Projetos/CameraPositioner:/root/CameraPositioner" --name linuxbuilder camerapositioner:build ./run.sh