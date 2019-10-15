exec:
	docker exec -it django /bin/bash

bash:
	docker run -it -v /home/arthur/www/dubbel/src/backend/:/srv/www/dubbel/src/backend/ --rm pyeye/dub-django:latest /bin/bash