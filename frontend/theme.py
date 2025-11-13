import rio

THEME = rio.Theme.from_colors(
    mode="light",

    # Primary colors - used for buttons, highlights, and interactive elements
    primary_color=rio.Color.from_hex("#D77A61"),
    secondary_color=rio.Color.from_hex("#223843"),
    
    # Background colors
    background_color=rio.Color.from_hex("#EFF1F3"),
    
    # Neutral colors for text and borders
    neutral_color=rio.Color.from_hex("#DBD3D8"),
)