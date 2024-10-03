#!/bin/sh

set -euxo pipefail

pyenv virtualenv 3.12.0 similar_video
pyenv activate similar_video
pyenv local

pip install -r requirements.txt
playwright install
