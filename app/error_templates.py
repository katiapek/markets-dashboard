from dash import html, dcc

class ErrorTemplate:
    """Base template for error display"""
    
    def render(self, error_info=None):
        """Render the error display"""
        return html.Div([
            html.H3("Something went wrong"),
            html.P("We're sorry, but an unexpected error occurred."),
            dcc.Loading(
                id="error-retry-loading",
                type="default",
                children=html.Button(
                    "Try Again",
                    id="error-retry-button",
                    n_clicks=0
                )
            ),
            html.Details([
                html.Summary("Error Details"),
                html.Pre(str(error_info) if error_info else "No additional information")
            ])
        ])
