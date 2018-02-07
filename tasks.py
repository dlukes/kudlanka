import os
from invoke import run, task

# user management


@task
def adduser(db, email, passwd):
    """Add a user to the database.

    :param db: The name of the database.
    :param email: More of a username. Doesn't really have to be a valid e-mail,
       unless you wish to contact users.
    :param passwd: Password in plain text. Will be hashed on first login.

    """
    query = 'db.user.insert({{email: "{email}", password: "{passwd}"}})'
    comm = "mongo --eval '{query}' {db}".format(query=query, db=db)
    print(comm)
    run(comm.format(email=email, passwd=passwd))


# i18n and l10


@task
def pybextract():
    """Extract strings for translation.

    Watch out: some .js files might need to be translated separately!

    """
    run("pybabel extract -F babel.cfg -o messages.pot kudlanka")


@task
def pybinit(lang):
    """Initialize localization into language lang.

    """
    comm = "pybabel init -i messages.pot -d kudlanka/translations -l {}"
    run(comm.format(lang))


@task
def pybupdate():
    """Update translations based on currently available strings.

    """
    run("pybabel update -i messages.pot -d kudlanka/translations")


@task
def pybcompile():
    """Compile translations.

    """
    run("pybabel compile -d kudlanka/translations")
    print("pybcompile: Remember that .js files need to be taken care of manually!")


@task
def jscompile():
    """Compile various javascript files.

    At the moment, this includes:

    - compiling DataTables l10n files

    """
    dtp = "kudlanka/static/vendor/datatables-plugins/i18n"
    for dirname, _, files in os.walk(dtp):
        for file in files:
            path = os.path.join(dirname, file)
            run("tail -n+8 {} >tmp".format(path))
            run("mv tmp {}".format(path))
    run("rm -f tmp")
