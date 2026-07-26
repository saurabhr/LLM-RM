import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from great_tables import GT, style, loc, google_font


def to_apa_table(df, title=None, round_digits=2):
    """
    Converts a summary dataframe to an APA formatted markdown/latex table.
    Expects columns like 'mean', 'std', 'count'.
    """
    # 1. Reset index if it's a MultiIndex (common with groupby) or has names
    apa_df = (
        df.reset_index() if isinstance(df.index, pd.MultiIndex) or df.index.names[0] else df.copy()
    )

    # 2. Rename columns to APA style
    rename_map = {
        "mean": "M",
        "std": "SD",
        "count": "n",
        "source": "Source",
        "memory": "Memory",
        "model": "Model",
    }
    apa_df = apa_df.rename(columns=rename_map)

    # 3. Reorder columns as requested: Model, Source, Memory, then others
    preferred_order = ["Model", "Source", "Memory"]
    actual_cols = [c for c in preferred_order if c in apa_df.columns]
    other_cols = [c for c in apa_df.columns if c not in actual_cols]
    apa_df = apa_df[actual_cols + other_cols]

    # 3b. Sort rows model-wise
    sort_cols = [c for c in ["Model", "Source", "Memory"] if c in apa_df.columns]
    if sort_cols:
        apa_df = apa_df.sort_values(by=sort_cols)

    # 4. Round numerical columns
    num_cols = apa_df.select_dtypes(include=[np.number]).columns
    apa_df[num_cols] = apa_df[num_cols].round(round_digits)

    # 5. Generate Markdown
    md_output = ""
    if title:
        md_output += f"Table 1\n\n*{title}*\n\n"

    md_output += apa_df.to_markdown(index=False)

    return apa_df, md_output


def save_apa_image(df, save_path):
    """
    Saves the dataframe as an APA styled image using matplotlib.
    """
    # Adjust height to be tighter based on number of rows
    fig_height = len(df) * 0.3 + 0.3
    fig, ax = plt.subplots(figsize=(10, fig_height))
    ax.axis("off")

    # Create the table
    tbl = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="center",
        loc="center",
        edges="horizontal",
    )

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(12)
    tbl.scale(1, 1.2)  # Single-ish spacing

    # Customizing lines for APA style (horizontal lines only)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_text_props(horizontalalignment="center")
        if row == 0:
            cell.set_text_props(weight="bold", horizontalalignment="center")
            cell.visible_edges = "TB"  # Top and bottom for header
        elif row == len(df):
            cell.visible_edges = "B"  # Bottom for last row
        else:
            cell.visible_edges = ""  # No lines for body cells

    # Save with tight bounding box and minimal padding
    plt.savefig(save_path, dpi=300, bbox_inches="tight", pad_inches=0.01)
    plt.close()
    print(f"Saved APA image to {save_path}")


def save_apa_table(df, base_path, title=None):
    """
    Saves the dataframe to CSV, Markdown, and Image with APA headers.
    """
    apa_df, md_output = to_apa_table(df, title=title)

    # Save CSV
    csv_path = f"{base_path}_apa.csv"
    apa_df.to_csv(csv_path, index=False)

    # Save Markdown
    md_path = f"{base_path}_apa.md"
    with open(md_path, "w") as f:
        f.write(md_output)

    # Save Image
    img_path = f"{base_path}_apa.png"
    save_apa_image(apa_df, save_path=img_path)

    print(f"Saved APA tables to:")
    print(f"  - {csv_path}")
    print(f"  - {md_path}")
    print(f"  - {img_path}")

    return apa_df


def to_gt_apa(df, title=None, subtitle=None):
    """
    Converts a summary dataframe to a great_tables GT object with APA styling.
    """
    # 1. Reset index if it's a MultiIndex or has names
    apa_df = (
        df.reset_index() if isinstance(df.index, pd.MultiIndex) or df.index.names[0] else df.copy()
    )

    # 2. Rename columns to APA style
    rename_map = {
        "mean": "M",
        "std": "SD",
        "count": "n",
        "source": "Source",
        "memory": "Memory",
        "model": "Model",
        "gamma": "Gamma",
        "rating": "Rating",
        "reading_hallucination": "Reading Hallucination",
        "accuracy": "Accuracy",
    }
    apa_df = apa_df.rename(columns=rename_map)

    # 3. Reorder columns
    preferred_order = ["Model", "Source", "Memory"]
    actual_cols = [c for c in preferred_order if c in apa_df.columns]
    other_cols = [c for c in apa_df.columns if c not in actual_cols]
    apa_df = apa_df[actual_cols + other_cols]

    # 4. Sort rows model-wise
    sort_cols = [c for c in ["Model", "Source", "Memory"] if c in apa_df.columns]
    if sort_cols:
        apa_df = apa_df.sort_values(by=sort_cols)

    # Create GT object
    gt_tbl = GT(apa_df)

    if title:
        gt_tbl = gt_tbl.tab_header(title=title, subtitle=subtitle)

    # APA Styling
    gt_tbl = gt_tbl.tab_options(
        table_font_names=[google_font("Inter"), "Arial", "sans-serif"],
        table_border_top_style="solid",
        table_border_top_width="2px",
        table_border_top_color="black",
        table_border_bottom_style="solid",
        table_border_bottom_width="2px",
        table_border_bottom_color="black",
        column_labels_border_bottom_style="solid",
        column_labels_border_bottom_width="1px",
        column_labels_border_bottom_color="black",
        table_body_border_bottom_style="none",
        heading_align="left",
        column_labels_font_weight="bold",
    ).fmt_number(
        columns=list(apa_df.select_dtypes(include=[np.number]).columns),
        decimals=2,
    )

    return gt_tbl


def save_gt_table(gt_obj, base_path):
    """
    Saves the GT object as HTML and attempts to save as PNG.
    """
    # Save as HTML
    html_path = f"{base_path}_gt.html"
    gt_obj.save(html_path)
    print(f"Saved GT table to {html_path}")

    # Note: great_tables saving to PNG usually requires additional system deps like chromium
    # We will try, but HTML is the primary high-quality output.
    try:
        img_path = f"{base_path}_gt.png"
        gt_obj.save(img_path)
        print(f"Saved GT image to {img_path}")
    except Exception as e:
        print(f"Could not save GT image to PNG (likely missing system dependencies): {e}")

    return html_path
