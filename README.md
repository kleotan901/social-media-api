# social-media-api


[https://github.com/kleotan901/social-media-api.git](https://github.com/kleotan901/social-media-api.git)

## How to run

```shell
git clone https://github.com/kleotan901/social-media-api.git
cd social-media-api
python -m venv venv
venv\Scripts\activate (on Windows)
source venv/bin/activate (on macOS)
pip install -r requirements.txt
python manage.py migrate
docker run -d -p 6379:6379 redis # run Redis Server
celery -A social_media_api beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
celery -A social_media_api worker -l INFO # run celery worker for task handling
python manage.py runserver # run app
```

## Configuration

The project uses environment variables for configuration. Please follow these steps to set up the required configuration files.


### `.env` and `.env.sample` files

The .env file is used to store sensitive information and configuration variables that are necessary for the project to function properly.

The .env.sample file serves as a template or example for the .env file. It includes the necessary variables and their expected format, but with placeholder values.
 
 To configure the project:

- Locate the .env.sample file in the project's root directory.
- Duplicate the .env.sample file and rename the duplicated file to .env.
- Open the .env file and replace the placeholder values with the actual configuration values specific to your setup.

Remember to keep the .env file secure and avoid sharing it publicly or committing it to version control systems.
