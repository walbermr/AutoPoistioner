if [ "$MODE" == "fresh" -o "$(sudo docker images -q camerapositioner:build 2> /dev/null)" == "" ]
then
    echo "Cloning and building container."
    git pull
    sudo docker build . -t camerapositioner:build --no-cache
fi

# sudo docker run -it --rm -w /root/CameraPositioner -v "E:/Projetos/CameraPositioner:/root/CameraPositioner" --name linuxbuilder camerapositioner:build ./run.sh
sudo docker run -it --rm -w /root/CameraPositioner -v "/home/walber/Documents/AutoPoistioner:/root/CameraPositioner" --name linuxbuilder camerapositioner:build ./run.sh