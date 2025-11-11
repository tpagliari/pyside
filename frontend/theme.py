import rio

THEME = rio.Theme.from_colors(
    mode="light",

    # Primary colors - used for buttons, highlights, and interactive elements
    primary_color=rio.Color.from_hex("#c200fb"),
    secondary_color=rio.Color.from_hex("#000000"),
    
    # Background colors
    background_color=rio.Color.from_hex("#ffffff"),
    
    # Neutral colors for text and borders
    neutral_color=rio.Color.from_hex("#cfdbd5"),
)