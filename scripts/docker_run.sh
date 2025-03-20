#/usr/bin/env bash

pushd ..
docker run -d --name translator_404_bot --rm --volume translator_404_bot_storage:/app/storage translator_404_bot
popd