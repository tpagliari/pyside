import rio
import httpx
import ast


# Result card component
class Resource(rio.Component):
    title: str          # resource title 
    link: str           # resource link
    description: str    # resource description
    source: str         # where the resource comes from
    
    def build(self) -> rio.Component:
        return rio.Card(
            rio.Column(
                rio.Text(
                    self.title,
                    style=rio.TextStyle(font_weight="bold", font_size=1.1),
                    selectable=True,
                    wrap=True,
                ),
                rio.Link(
                    content="Read the Article",
                    target_url=self.link,
                    open_in_new_tab=True,
                ),
                rio.Text(
                    self.description,
                    style="text",
                    selectable=True,
                    wrap=True,
                ),
                spacing=0.5,
                margin=1.5,
            ),
            elevate_on_hover=True,
        )


# Main search component
class Properly(rio.Component):
    query: str = "" 
    results: list[tuple[str, str, str, str]] = []
    is_searching: bool = False
    
    
    async def search(self) -> None:
        """Performing GET request and collect the results asynchronously"""

        if not self.query.strip():
            return
            
        self.is_searching = True
        self.results = []
        
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                # where fastAPI is running -> perform get request
                url = f"http://localhost:8000/search?query={self.query}"
                async with client.stream("GET", url) as response:
                    async for line in response.aiter_lines():
                        # handle API response
                        if not line.strip():
                            continue
                        try:
                            item = ast.literal_eval(line)
                            source = item["source"]
                            resources = item["resources"]
                            
                            for entry in resources:
                                parts = entry.split("\n")
                                if len(parts) >= 3:
                                    title = parts[0].strip()
                                    link = parts[1].strip()
                                    descr = parts[2].strip()
                                    self.results.append((title, link, descr, source))
                        except Exception:
                            continue
        finally:
            self.is_searching = False
    

    def build(self) -> rio.Component:
        return rio.Column(
            # Header section
            rio.Column(
                rio.Text(
                    "Learn Properly",
                    style=rio.TextStyle(
                        font_size=2,
                        font_weight="bold",
                        all_caps=True,
                    ),
                    align_x=0.5,
                ),
                rio.TextInput(
                    text=self.bind().query,
                    label="Type a topic here!",
                    on_confirm=lambda _: self.search(),
                    min_width=30,
                ),
                rio.Button(
                    content=rio.Text(
                        "GO",
                        align_x=0.5,
                        style=rio.TextStyle(fill=rio.Color.from_hex("#ffffff"), font_weight="bold")
                    ),
                    on_press=lambda: self.search(),
                    style="major",
                    is_sensitive=not self.is_searching,
                    min_width=10,
                    color="secondary",
                ),
                spacing=1,
                align_x=0.5,
                margin_top=3,
            ),
            
            # Results section -> resources stream
            rio.ScrollContainer(
                rio.Column(
                    *[
                        Resource(
                            title=title,
                            link=link,
                            description=descr,
                            source=source,
                        )
                        for title, link, descr, source in self.results
                    ],
                    spacing=1,
                    margin=2,
                    grow_x=True,
                ) if self.results else rio.Text(
                    "No results yet" if not self.is_searching else "Searching...",
                    style="dim",
                    margin_top=2,
                ),
                grow_y=True,
                margin_top=2,
                grow_x=True,
            ),
            spacing=0.5,
            align_x=0.5,
            margin_bottom=1,
            margin_left=2,
            margin_right=2,
            proportions=(1,2.5),
        )