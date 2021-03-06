bump-patch:
	bumpversion patch

bump-minor:
	bumpversion minor

start-dev:
	@LOG_LEVEL=debug &&  /usr/bin/env python3 -m "$${PWD##*/}"

clean:
	find . -name "*.pyc" -exec rm -f "{}" \;

run-host:
	curl "host:10000/run/$${PWD##*/}?nocache=1" | jq

rm-host:
	curl "host:10000/rm/$${PWD##*/}" | jq

stop-host:
	curl "host:10000/stop/$${PWD##*/}" | jq
