exec:
	docker exec -it django /bin/bash

bash:
	docker run -it -v /home/artur/dev/www/dubbel/src/backend/:/srv/www/dubbel/src/backend/ --rm pyeye/dub-django:latest /bin/bash
