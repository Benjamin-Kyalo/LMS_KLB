#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    # Plain management commands use the local settings so a fresh checkout can
    # run `python manage.py runserver` immediately. Production must opt in with
    # DJANGO_SETTINGS_MODULE=config.settings_prod; wsgi.py and asgi.py already
    # do that for deployed servers.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
