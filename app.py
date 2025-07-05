"""
Main module in the AcademicNet Dash application.
Initializes the Dash app, loads organization data, sets up layout and callbacks.
"""

from dash import Dash
import logging

from src.orgs import load_orgs
from src.layout import base_layout
from src.callbacks import get_callbacks

# Default constants
DEFAULT_ORG = '14346'
LOG_LEVEL = logging.ERROR


def create_app() -> Dash:
    """
    Create the Dash application.
    Returns:
        app (Dash): configured Dash instance
    """
    # Suppress Werkzeug log messages
    logging.getLogger('werkzeug').setLevel(LOG_LEVEL)

    # Create instance Dash
    app = Dash(
        __name__,
        title='AcademicNet',
        update_title=None,
        suppress_callback_exceptions=True
    )

    # Loading organization dropdown options and name mapping
    org_map, org_name_map = load_orgs()

    # Build layout
    app.layout = base_layout(org_map, DEFAULT_ORG)

    # Register сallbacks
    get_callbacks(app, org_name_map)

    return app


def main():
    """
    Launch the Dash server. 
    """
    app = create_app()
    app.run(debug=False)


if __name__ == '__main__':
    main()