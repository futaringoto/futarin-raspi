#!/bin/sh
curl https://pyenv.run | bash
pyenv install 3.12
pyenv global 3.12
exec /bin/sh -l

sudo apt update
sudo apt install python3-gpiozero
sudo apt install python3-pyaudio

pip3 install .

