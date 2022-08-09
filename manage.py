import argparse
import os
import unittest

from app import initialize_calculator_process_qm


def test():
    tests = unittest.TestLoader().discover("app/test", pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    else:
        return 1


def run():
    # Import only after initialization
    from app.main import start_app
    app = start_app()
    app.app_context().push()
    port = int(os.getenv("FLASK_MICROSERVICE_PORT") or 5000)
    # Disable reloader to create only 1 process
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    usage = """
    # For running unittest
    python3 manage.py --test

    # For setting up production
    python3 manage.py
    """
    # Initialize process queue manager child process in entry point to prevent spawn error
    # Protecting the entry point ensures that the program is only started once,
    # that the tasks of the main process are only executed by the main process and not the child processes.
    initialize_calculator_process_qm()

    parser = argparse.ArgumentParser(description='Flask microservice testing or deployment',
                                     usage=usage)
    parser.add_argument('--test', action='store_true', default=False,
                        help='Test Flask microservice')
    args = parser.parse_args()

    if args.test:
        test()
    else:
        run()
