"""
Point d'entrée Django — utilisé pour toutes les commandes de gestion
(migrations, runserver, shell, etc.)
"""
import os
import sys


def main():
    # Réglages : variable d'environnement, sinon ligne DJANGO_SETTINGS_MODULE du .env,
    # sinon développement (votre ordinateur).
    from decouple import config

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", config("DJANGO_SETTINGS_MODULE", default="config.settings.dev")
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d'importer Django. Assurez-vous que Django est installé "
            "et que votre environnement virtuel est activé."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
