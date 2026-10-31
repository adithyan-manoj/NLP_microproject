"""
Deterministic Visualization Selection Engine for CricInsight.
Transforms structured analysis results into chart-ready JSON consumed by Flutter and fl_chart:
- Recent performance: Line chart
- Player comparison: Grouped bar chart
- Opponent analysis: Sorted bar chart
- Venue comparison: Bar chart
- Summary statistics: KPI cards
"""

from typing import Dict, Any, List, Optional

def select_chart_specification(
    analysis_type: str,
    data: Dict[str, Any],
    title_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Selects the deterministic visualization type and formats fl_chart ready series data.
    """
    if analysis_type == "player_analysis":
        progression = data.get("progression", [])
        player_name = data.get("metrics", {}).get("player_name", "Player")
        
        if not progression:
            return {
                "chart_type": "empty",
                "title": f"{player_name} Innings Form",
                "empty_state_message": "No recorded innings match the specified filters in the dataset.",
                "series": []
            }

        # Build Line chart series for fl_chart
        chart_points = []
        for item in progression:
            chart_points.append({
                "x": item["innings_number"],
                "y": item["runs"],
                "label": f"Inn {item['innings_number']}",
                "tooltip": f"{item['runs']} runs ({item['balls']} balls) vs {item['opponent']} on {item['date']}",
                "is_out": item["is_out"]
            })

        return {
            "chart_type": "line",
            "title": title_override or f"{player_name} — Innings Form Progression",
            "subtitle": f"Chronological run progression across {len(progression)} innings",
            "x_axis_label": "Innings Number",
            "y_axis_label": "Runs Scored",
            "units": "runs",
            "series": [
                {
                    "name": player_name,
                    "color": "#00E5FF",
                    "points": chart_points
                }
            ],
            "average_line": data.get("metrics", {}).get("batting_average")
        }

    elif analysis_type == "player_comparison":
        comparison = data.get("comparison", [])
        if not comparison:
            return {
                "chart_type": "empty",
                "title": "Player Comparison",
                "empty_state_message": "No comparison data available.",
                "series": []
            }

        players = [c["player"] for c in comparison]
        runs_series = []
        avg_series = []
        sr_series = []

        for c in comparison:
            runs_series.append({"x": c["player"], "y": c["runs"], "label": "Runs"})
            avg_series.append({"x": c["player"], "y": c["average"] or 0, "label": "Avg"})
            sr_series.append({"x": c["player"], "y": c["strike_rate"], "label": "Strike Rate"})

        return {
            "chart_type": "grouped_bar",
            "title": title_override or f"Comparison: {' vs '.join(players)}",
            "subtitle": "Comparative metrics derived from Cricsheet records",
            "x_axis_label": "Player",
            "y_axis_label": "Value",
            "categories": ["Runs", "Average", "Strike Rate"],
            "series": [
                {"name": "Total Runs", "color": "#00E5FF", "bars": runs_series},
                {"name": "Batting Average", "color": "#00E676", "bars": avg_series},
                {"name": "Strike Rate", "color": "#FFD600", "bars": sr_series},
            ]
        }

    elif analysis_type == "opponent_analysis":
        opponents_data = data.get("opponents", [])
        bars = [{"x": o["opponent"], "y": o["runs"], "label": o["opponent"]} for o in opponents_data]
        return {
            "chart_type": "bar",
            "title": title_override or "Performance by Opponent",
            "subtitle": "Runs scored against each opposing nation",
            "x_axis_label": "Opponent",
            "y_axis_label": "Total Runs",
            "units": "runs",
            "series": [{"name": "Runs", "color": "#7C4DFF", "bars": bars}]
        }

    # Default fallback to summary card specification
    return {
        "chart_type": "kpi_cards",
        "title": "Statistical Overview",
        "series": []
    }
