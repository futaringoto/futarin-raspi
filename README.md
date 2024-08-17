# futarin-raspi

## Requirement

- Python
    - Poetry
    - Python ^3.12


## Getting Started

1. Install dependencies
```shell
sudo apt install -y python3-dev portaudio19-dev
```

2. Clone this repository

```shell
git clone "git@github.com:futaringoto/futarin-raspi.git" 
cd futarin-raspi
```

3. Install Packages from `.pyproject.toml`

```shell
# use normal Python envierment
pip3 install .

# use Poetry
poetry install
```

3. Run

```shell
# use normal Python envierment
python3 src/main.py

# use Poetry
poetry run python src/main.py
```


## Credits

[VOICEVOX](https://voicevox.hiroshiba.jp/):ずんだもん
