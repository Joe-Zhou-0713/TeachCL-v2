from visualization.bar_chart import draw_bar_chart
from visualization.radar_chart import draw_radar_chart, draw_interaction_radar_chart
from visualization.pie_chart import draw_pie_chart
from visualization.stacked_bar_chart import draw_stacked_bar_chart


def generate_visualization(scaffold):
    if scaffold.get("visualization_type") == "radar" and scaffold.get("pattern"):
        return draw_interaction_radar_chart(scaffold.get("data", {}))
    chart_type = scaffold["visualization_type"]
    data = scaffold["data"]

    if chart_type == "pie":
        return draw_pie_chart(data)

    if chart_type == "radar":
        return draw_radar_chart(data)

    if chart_type == "bar":
        return draw_bar_chart(data)

    if chart_type == "stacked_bar":
        return draw_stacked_bar_chart(data)

    return None
