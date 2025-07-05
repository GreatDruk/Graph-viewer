from src.orgs import load_orgs
from src.layout import base_layout
from src.callbacks import get_callbacks

from dash import Dash
import logging

logging.getLogger('werkzeug').setLevel(logging.ERROR)

DEFAULT_ORG = '14346'

# DASH
app = Dash(
    __name__,
    title='AcademicNet',
    update_title=None,
    suppress_callback_exceptions=True
)

# Loading organization
org_map, org_name_map = load_orgs()

# Layout
app.layout = base_layout(org_map, DEFAULT_ORG)

# Callbacks
get_callbacks(app, org_name_map)

# START
if __name__ == '__main__':
    app.run(debug=False)
