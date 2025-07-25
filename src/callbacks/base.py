"""
Module: base
Registers all application callbacks.
"""
from .canvas_callbacks import canvas_callbacks
from .graph_callbacks import graph_callbacks
from .overlay_callbacks import overlay_callbacks
from .tooltip_callbacks import tooltip_callbacks
from .upload_org import upload_org

def get_callbacks(app, org_name_map):
    """
    Attach all callbacks to the Dash application.

    Args:
        app: Dash instance to register callbacks on.
        org_name_map: Dict mapping organization IDs to display names.
    """
    upload_org(app, org_name_map)
    overlay_callbacks(app)
    graph_callbacks(app)
    tooltip_callbacks(app)
    canvas_callbacks(app)
