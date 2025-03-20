#/usr/bin/env bash

pushd ..
docker run -d --name translator_404_bot --rm translator_404_bot
popd