try:
    from . import models
except ModuleNotFoundError as error:
    if error.name != "odoo":
        raise
