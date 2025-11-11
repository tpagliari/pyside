import rio

from .app import Properly
from .theme import *

app = rio.App(
    build=lambda: rio.Container(
        Properly(),
        align_x=0.5,
        align_y=0,
        grow_y=True,
        grow_x=True,
    ),
    name="Properly",
    theme=THEME,
)
