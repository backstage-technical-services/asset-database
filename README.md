# Backstage PAT Database

This is the repository for the [Backstage PAT Database](https://assets.bts-crew.com), which stores records of our electrical tests (Portable Appliance Testing) and repairs. 

For more in depth information on our equipment, see the [Asset Database](https://wiki.bts-crew.com/index.php/Asset_Database_(SnipeIT)).

Administrative information can be found on the [Wiki](https://wiki.bts-crew.com/index.php/PAT_Database).


## Development pre-requisites

 - [Pipenv](https://pipenv.pypa.io/en/latest/) - for managing Python dependencies
 - [Docker](https://www.docker.com/) - for running the database in a container (alternatively just a MariaDB server)
 - [Cloned repo](https://github.com/backstage-technical-services/asset-database) - this repository cloned to your local machine

## Running the system

### Setup environment variables
Copy `.env.example` to `.env` and populate the `SECRET_KEY` with any random string.

### Build the project
The site itself runs inside of a docker container during development so that dependencies can be managed easily. 

Build the project by running: `scripts/site.sh rebuild`

### Start auxiliary services
This system includes the following services to aid development:
 - MariaDB database (port 6021)
 - Mail server (view emails sent by the system without actually sending)
    - http://localhost:6022

Run `scripts/site.sh start` to start them.

The main site will be available at http://localhost:8000

### Setup Python environment
If using an IDE with support for a custom interpreter, be sure to change the Python interpreter to the one created by Pipenv for linting to work properly. 

### Run database migrations
Run `scripts/site.sh manage migrate` to apply the database migrations.

You can check they have applied properly by observing the created tables on PhpMyAdmin: http://localhost:8080/index.php?route=/database/structure&db=asset_register

### Creating an account
Create the first admin account by running `scripts/site.sh manage createsuperuser` and following the prompts.

