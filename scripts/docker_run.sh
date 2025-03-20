#/usr/bin/env bash

pushd ..
docker run -d --name translator_404_bot translator_404_bot
popd