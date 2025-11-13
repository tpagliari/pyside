import rio
import httpx
import ast


# Result card component
class Resource(rio.Component):
    title: str
    link: str
    description: str
    source: str
    
    def build(self) -> rio.Component:
        return rio.Card(
            rio.Column(
                rio.Text(
                    self.title,
                    style=rio.TextStyle(font_weight="bold", font_size=1.3),
                    selectable=True,
                    overflow="wrap",
                    justify="center",
                ),
                rio.Link(
                    content=rio.Text("Read the Article", italic=True, justify="center", font_size=1, fill=rio.Color.from_hex("#0377fb")),
                    target_url=self.link,
                    open_in_new_tab=True,
                ),
                rio.Text(
                    text=self.description,
                    style="text",
                    selectable=True,
                    overflow="wrap",
                    font_size=1,
                    justify="center"
                ),
                spacing=0.5,
                margin=1.5,
            ),
            elevate_on_hover=True,
            colorize_on_hover=True,
        )


# Main search component
class Properly(rio.Component):
    query: str = "" 
    results: list[tuple[str, str, str, str]] = []
    is_searching: bool = False
    
    async def search(self) -> None:
        """Performing GET request and collect the results asynchronously"""
        
        if not self.query.strip(): return
        self.is_searching = True
        self.results = []
        self.force_refresh() # Force UI update before starting search
        
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                url = f"http://localhost:8000/search?query={self.query}"
                async with client.stream("GET", url) as response:
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            item = ast.literal_eval(line)
                            source = item["source"]
                            resources = item["resources"]
                            
                            # Process and append results
                            new_results = [
                                (parts[0].strip(), parts[1].strip(), parts[2].strip(), source)
                                for entry in resources
                                for parts in [entry.split("\n")]
                                if len(parts) >= 3
                            ]
                            
                            self.results.extend(new_results)
                            self.force_refresh()  # Update UI after each batch
                            
                        except Exception:
                            continue
        finally:
            self.is_searching = False
            self.force_refresh()
            

    def build(self) -> rio.Component:
        return rio.Column(

            # Header section (30% of the page)
            rio.Column(

                rio.Text(
                    "Learn Properly",
                    style=rio.TextStyle(
                        font_size=2,
                        font_weight="bold",
                        all_caps=True,
                    ),
                    align_x=0.5,
                    grow_x=True,
                ),

                rio.Row(
                    rio.TextInput(
                        text=self.bind().query,
                        label="Type a topic here!", # TODO: can we make this disappear after the user starts typing?
                        on_confirm=lambda _: self.search(),
                        grow_x=True,
                        min_width=30,
                        style="rounded",
                    ),
                    rio.Button(
                        content=rio.Text(
                            "GO",
                            align_x=0.5,
                            style=rio.TextStyle(
                                fill=rio.Color.from_hex("#ffffff"),
                                font_weight="bold"
                            ),
                        ),
                        on_press=lambda: self.search(),
                        shape="rounded",
                        style="major",
                        is_sensitive=not self.is_searching,
                        grow_x=True,
                    ),
                    spacing=1,
                    grow_x=True,
                    proportions=(0.9,0.1)
                ),
                spacing=1,
                margin_top=2,
            ),
            
            # Results section (70% of the page)
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
                ) if self.results else rio.Text(
                    "Searching..." if self.is_searching else "No results yet",
                    style="dim",
                    margin_top=2,
                    justify="center",
                    align_y=0,
                    italic=True,
                ),
                grow_y=True,
                margin_top=2,
                grow_x=True,
                margin_bottom=1,
            ),
            spacing=0.5,
            align_x=0.5,
            margin_left=2,
            margin_right=2,
            min_width=50,
            min_height=46.7,
            #proportions=(2, 8),  
        )