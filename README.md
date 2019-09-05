# Backend for CentOS CI project-onboarding
> APIs for [ci-user-frontend](https://github.com/shailysangwan/ci-user-frontend/tree/master/client) consumption
## To run the application in development mode, run the following from the application root

Install python and pip
> ```sudo apt install python3```

> ```sudo apt install python3-pip```

Create a virtual environment
> ```pip3 install --user virtualenv```

> ```virtualenv venv```

> ```source venv/bin/activate```

Install dependencies
> ```pip3 install -r requirements.txt```

Export environment variables using either of the following
1. Export variables from the command line
2. or install autoenv and create a .env file as such:
    ```python
    source venv/bin/activate
    export FLASK_APP="app.py"
    export FLASK_DEBUG=1
    export APP_SETTINGS="config.DevelopmentConfig"
    export SECRET_KEY="some_secret_key"
    export DATABASE_URL="postgresql://abc:xyz@localhost:5432/ci_onboarding"
    ```

Start the application
> ```flask run```

To run tests
> ```python -m pytest```