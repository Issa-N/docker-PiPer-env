export USR_NAME=rllab

xhost local:root

docker run --rm -it \
	--name piper-env-image \
	-w /home/${USR_NAME}/workspace \
	--volume "$(pwd)"/workspace:/home/${USR_NAME}/workspace \
	--volume "$(pwd)"/catkin_ws:/home/${USR_NAME}/catkin_ws \
	--volume $HOME/.Xauthority:/home/$(id -un)/.Xauthority -e XAUTHORITY=/home/$(id -un)/.Xauthority \
	--volume /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=unix$DISPLAY \
	--privileged --net=host --ipc=host \
	--device=/dev/video0 \
	--device=/dev/video2 \
	-e DOCKER_USER_NAME=$(id -un) \
	-e DOCKER_USER_ID=$(id -u) \
	-e DOCKER_USER_GROUP_NAME=$(id -gn) \
	-e DOCKER_USER_GROUP_ID=$(id -g) \
	-v /home/${USR_NAME}/docker-PiPer-env/double_PiPER:/home/${USR_NAME}/docker-PiPER-env/double_PiPER \
	docker-piper-env-template bash
	# --gpus all \
	# --device /dev/input/js1:/dev/input/js1 \
	# --device /dev/input/js2:/dev/input/js2 \
	# --device /dev/ttyUSB0:/dev/ttyUSB0 \
	# --device /dev/ttyACM0:/dev/ttyACM0 \