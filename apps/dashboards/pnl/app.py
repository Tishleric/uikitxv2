"""P&L Dashboard Application

Main module for the P&L tracking dashboard integrated into UIKitXv2.
Now displays TYU5 Excel output directly.
"""

import logging
from dash import html, dcc
import dash_bootstrap_components as dbc

# Import wrapped components
from lib.components.basic import Container, Button
from lib.components.advanced import DataTable
from lib.components.themes import default_theme

# Import TYU5 Excel reader
from lib.trading.pnl_integration.tyu5_excel_reader import TYU5ExcelReader

# Import controller to start file watchers
from lib.trading.pnl_calculator.controller import PnLController

# Import market price file monitor
from lib.trading.market_prices import MarketPriceFileMonitor

logger = logging.getLogger(__name__)

# Initialize reader at module level
tyu5_reader = TYU5ExcelReader()

# Initialize and start the PnL controller for file watching
pnl_controller = PnLController()
pnl_controller.start_file_watchers()
logger.info("P&L file watchers started")

# Initialize and start the market price file monitor
market_price_monitor = MarketPriceFileMonitor()
market_price_monitor.start()
logger.info("Market price file monitor started")


def create_summary_card(title: str, value: str, color: str = 'white', subtitle: str | None = None) -> html.Div:
    """Create a summary statistics card.
    
    Args:
        title: Card title
        value: Main value to display
        color: Text color for the value
        subtitle: Optional subtitle text
        
    Returns:
        html.Div component with styled card
    """
    card_content = [
        html.H6(title, style={
            'color': default_theme.text_subtle,
            'fontSize': '14px',
            'marginBottom': '5px',
            'fontWeight': '400'
        }),
        html.H3(value, style={
            'color': color,
            'fontSize': '24px',
            'fontWeight': '600',
            'marginBottom': '0'
        })
    ]
    
    if subtitle:
        card_content.append(html.P(subtitle, style={
            'color': default_theme.text_subtle,
            'fontSize': '12px',
            'marginTop': '5px',
            'marginBottom': '0'
        }))
    
    return html.Div(
        card_content,
        style={
            'backgroundColor': default_theme.panel_bg,
            'padding': '20px',
            'borderRadius': '8px',
            'border': f'1px solid {default_theme.secondary}',
            'minHeight': '100px',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center'
        }
    )


def create_sheet_datatable(sheet_name: str, df) -> Container:
    """Create a DataTable for a TYU5 Excel sheet.
    
    Args:
        sheet_name: Name of the sheet
        df: Pandas DataFrame with sheet data
        
    Returns:
        Container with DataTable
    """
    # Convert DataFrame columns to DataTable format
    columns = []
    for col in df.columns:
        col_config = {'name': col, 'id': col}
        
        # Add type hints for numeric columns
        if df[col].dtype in ['float64', 'int64']:
            col_config['type'] = 'numeric'
            # Format currency/monetary columns
            if any(x in col.lower() for x in ['pnl', 'value', 'fee']):
                col_config['format'] = {'specifier': '$,.2f'}
            # Format price columns (more decimal places)
            elif 'price' in col.lower():
                col_config['format'] = {'specifier': ',.6f'}
            # Format quantity columns
            elif any(x in col.lower() for x in ['quantity', 'qty']):
                col_config['format'] = {'specifier': ',.0f'}
            # Default numeric format
            else:
                col_config['format'] = {'specifier': ',.2f'}
                
        columns.append(col_config)
    
    # Convert DataFrame to records
    data = df.to_dict('records')
    
    # Set page_size to total rows to effectively disable pagination
    total_rows = len(data) if data else 10
    
    return Container(
        id=f"pnl-{sheet_name.lower()}-container",
        children=[
            DataTable(
                id=f"pnl-{sheet_name.lower()}-table",
                columns=columns,
                data=data,
                page_size=total_rows,  # Show all rows
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': default_theme.panel_bg
                    },
                    {
                        'if': {'row_index': 'even'},
                        'backgroundColor': default_theme.base_bg
                    }
                ],
                style_table={
                    'overflowX': 'auto',     # Allow horizontal scroll if needed
                    'width': '100%',         # Full width
                    'minWidth': '100%'       # Ensure full width usage
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '12px',       # Increased padding for better readability
                    'whiteSpace': 'nowrap',  # Prevent wrapping for cleaner look
                    'height': 'auto',        # Auto height for cells
                    'overflow': 'hidden',    # Hide overflow
                    'textOverflow': 'ellipsis',  # Add ellipsis for very long text
                    'minWidth': '100px',     # Minimum column width
                    'fontSize': '14px',      # Slightly larger font
                    'fontFamily': 'monospace',  # Monospace for numbers
                    'backgroundColor': default_theme.base_bg,
                    'color': default_theme.text_light,
                    'borderBottom': f'1px solid {default_theme.secondary}'
                },
                style_header={
                    'backgroundColor': default_theme.panel_bg,
                    'fontWeight': 'bold',
                    'fontSize': '14px',
                    'borderBottom': f'2px solid {default_theme.secondary}'
                }
            )
        ]
    )


def create_pnl_content():
    """Create the P&L dashboard content displaying TYU5 Excel output.
    
    Returns:
        Rendered Dash components for the P&L dashboard layout
    """
    logger.info("Creating P&L dashboard content with TYU5 data")
    
    # Read TYU5 Excel data
    sheets_data = tyu5_reader.read_all_sheets()
    summary_data = tyu5_reader.get_summary_data()
    file_timestamp = tyu5_reader.get_file_timestamp()
    
    # Summary stats section
    summary_section = Container(
        id="pnl-summary-section",
        children=[
            html.H4("TYU5 P&L Summary", style={'color': default_theme.text_light, 'marginBottom': '20px'}),
            html.Div(
                id="pnl-summary-cards",
                children=[
                    create_summary_card(
                        "Total P&L",
                        f"${summary_data.get('total_pnl', 0):,.2f}",
                        color=default_theme.success if summary_data.get('total_pnl', 0) >= 0 else default_theme.danger
                    ),
                    create_summary_card(
                        "Daily P&L", 
                        f"${summary_data.get('daily_pnl', 0):,.2f}",
                        color=default_theme.success if summary_data.get('daily_pnl', 0) >= 0 else default_theme.danger
                    ),
                    create_summary_card(
                        "Realized P&L",
                        f"${summary_data.get('realized_pnl', 0):,.2f}",
                        color=default_theme.success if summary_data.get('realized_pnl', 0) >= 0 else default_theme.danger
                    ),
                    create_summary_card(
                        "Unrealized P&L",
                        f"${summary_data.get('unrealized_pnl', 0):,.2f}",
                        color=default_theme.success if summary_data.get('unrealized_pnl', 0) >= 0 else default_theme.danger
                    ),
                    create_summary_card(
                        "Active Positions",
                        f"{int(summary_data.get('active_positions', 0))}",
                        color=default_theme.text_light
                    ),
                    create_summary_card(
                        "Total Trades",
                        f"{int(summary_data.get('total_trades', 0))}",
                        color=default_theme.text_light
                    )
                ],
                style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))',
                    'gap': '15px',
                    'marginBottom': '30px'
                }
            )
        ]
    )
    
    # Control buttons and status
    controls_section = Container(
        id="pnl-controls-section",
        children=[
            html.Div([
                Button(
                    id="pnl-refresh-button",
                    label="Refresh TYU5 Data",
                    style={'marginRight': '10px'}
                ).render(),
                Button(
                    id="pnl-reprocess-button",
                    label="Drop & Reprocess All Data",
                    style={
                        'marginRight': '10px',
                        'backgroundColor': default_theme.danger,
                        'borderColor': default_theme.danger
                    }
                ).render(),
                html.Span(
                    f"File: {file_timestamp}",
                    id="pnl-file-timestamp",
                    style={
                        'color': default_theme.text_subtle,
                        'fontSize': '14px',
                        'marginLeft': '20px'
                    }
                )
            ], style={'marginBottom': '10px'}),
            # Reprocess status area
            dcc.Loading(
                id="pnl-reprocess-loading",
                type="default",
                children=[
                    html.Div(
                        id="pnl-reprocess-status",
                        style={
                            'marginTop': '10px',
                            'padding': '10px',
                            'backgroundColor': default_theme.panel_bg,
                            'borderRadius': '4px',
                            'fontSize': '14px',
                            'display': 'none'  # Hidden by default
                        }
                    )
                ]
            )
        ]
    )
    
    # Create tabs with DataTables that will be updated via callbacks
    sheet_order = ['Positions', 'Trades', 'Risk_Matrix', 'Position_Breakdown']
    
    # Create all tabs with empty DataTables
    tab_list = []
    for sheet_name in sheet_order:
        tab_label = sheet_name.replace('_', ' ')
        
        # Create an empty DataTable that will be populated by callback
        datatable = DataTable(
            id=f"pnl-{sheet_name.lower()}-table",
            columns=[],
            data=[],
            page_size=10,
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': default_theme.panel_bg
                }
            ],
            style_table={
                'overflowX': 'visible',
                'width': '100%',
                'tableLayout': 'fixed'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'whiteSpace': 'normal',
                'height': 'auto',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': 0
            }
        )
        
        # Wrap in container
        tab_content = Container(
            id=f"pnl-{sheet_name.lower()}-container",
            children=[datatable.render()]
        ).render()
        
        # Create tab
        tab = dbc.Tab(
            label=tab_label,
            tab_id=f"pnl-tab-{sheet_name.lower()}",
            children=tab_content
        )
        tab_list.append(tab)
    
    # Create tabs component with all tabs
    tabs_component = dbc.Tabs(
        id="pnl-tabs",
        children=tab_list,
        active_tab="pnl-tab-positions"  # Set default active tab
    )
    
    no_data_component = Container(
        id="pnl-no-data",
        children=[
            html.Div(
                "No TYU5 data available. Please enter trades or click 'Drop & Reprocess All Data' to reload existing trades.",
                style={
                    'color': default_theme.text_subtle,
                    'textAlign': 'center',
                    'padding': '40px',
                    'fontSize': '16px'
                }
            )
        ],
        style={'display': 'none' if tab_list else 'block'}
    )
    
    # Auto-refresh interval (5 seconds for <10s trade-to-dashboard latency)
    refresh_interval = dcc.Interval(
        id='pnl-interval-component',
        interval=5*1000,  # 5 seconds in milliseconds
        n_intervals=0
    )
    
    # Combine all sections
    return Container(
        id="pnl-main-container",
        children=[
            refresh_interval,
            summary_section,
            controls_section,
            tabs_component,
            no_data_component
        ],
        style={
            'padding': '20px',
            'maxWidth': '1800px',  # Increased from default
            'margin': '0 auto'     # Center the container
        }
    ).render() 