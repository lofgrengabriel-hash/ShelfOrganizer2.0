import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

st.set_page_config(page_title="Shelf Arranger", layout="wide")

st.title("📦 Shelf Arranger Web App")
st.write("Upload an Excel file with **Shelves** and **Boxes** sheets to generate placements.")

uploaded_file = st.file_uploader("Drag & drop your Excel file here", type=["xlsx"])

def cuboid_data(x, y, z, dx, dy, dz):
    return [
        (x, y, z),
        (x+dx, y, z),
        (x+dx, y+dy, z),
        (x, y+dy, z),
        (x, y, z+dz),
        (x+dx, y, z+dz),
        (x+dx, y+dy, z+dz),
        (x, y+dy, z+dz),
    ]

def plot_cube(ax, origin, dx, dy, dz, color="blue"):
    X = cuboid_data(origin[0], origin[1], origin[2], dx, dy, dz)
    faces = [
        [X[0],X[1],X[2],X[3]],
        [X[4],X[5],X[6],X[7]],
        [X[0],X[1],X[5],X[4]],
        [X[2],X[3],X[7],X[6]],
        [X[1],X[2],X[6],X[5]],
        [X[4],X[7],X[3],X[0]],
    ]
    pc = Poly3DCollection(faces, alpha=0.6, facecolor=color)
    ax.add_collection3d(pc)

def plot_shelf(ax, origin, dx, dy, dz, color="gray"):
    X = cuboid_data(origin[0], origin[1], origin[2], dx, dy, dz)
    faces = [
        [X[0],X[1],X[2],X[3]],
        [X[4],X[5],X[6],X[7]],
        [X[0],X[1],X[5],X[4]],
        [X[2],X[3],X[7],X[6]],
        [X[1],X[2],X[6],X[5]],
        [X[4],X[7],X[3],X[0]],
    ]
    pc = Poly3DCollection(faces, alpha=0.05, facecolor=color, edgecolor="black", linewidths=0.5)
    ax.add_collection3d(pc)

if uploaded_file is not None:
    shelves = pd.read_excel(uploaded_file, sheet_name="Shelves")
    boxes = pd.read_excel(uploaded_file, sheet_name="Boxes")

    if "Quantity" not in boxes: boxes["Quantity"] = 1
    if "AllowRotation" not in boxes: boxes["AllowRotation"] = True
    if "Priority" not in boxes: boxes["Priority"] = 0

    rows = []
    for _, r in boxes.iterrows():
        for i in range(int(r["Quantity"])):
            rows.append({
                "Box_Type": r["Box_ID"],
                "Box_Instance": f"{r['Box_ID']}_{i+1}",
                "Width": r["Width"],
                "Height": r["Height"],
                "Depth": r["Depth"],
                "AllowRotation": r["AllowRotation"],
                "Priority": r["Priority"]
            })
    items = pd.DataFrame(rows)
    items["Area"] = items["Width"] * items["Depth"]
    items = items.sort_values(by=["Priority","Box_Type","Area"], ascending=[False, True, False]).reset_index(drop=True)

    placements = []
    unplaced = items.copy()

    for _, shelf in shelves.iterrows():
        sid = shelf["Shelf_ID"]
        s_width, s_height, s_depth = shelf["Width"], shelf["Height"], shelf["Depth"]
        shelf_used_height, level_index = 0, 0

        while shelf_used_height < s_height and not unplaced.empty:
            remaining_height = s_height - shelf_used_height
            candidates = unplaced[unplaced["Height"] <= remaining_height]
            if candidates.empty:
                break
            level_height = min(remaining_height, candidates["Height"].max())
            x_cursor = 0
            placed_in_level = []

            for btype, group in unplaced.groupby("Box_Type", sort=False):
                for idx, item in group.iterrows():
                    orientations = [(item["Width"], item["Depth"], item["Height"], False)]
                    if item["AllowRotation"]:
                        orientations.append((item["Depth"], item["Width"], item["Height"], True))
                    placed = False
                    for w,d,h,rot in orientations:
                        if h <= level_height and d <= s_depth and x_cursor + w <= s_width:
                            placements.append({
                                "Shelf_ID": sid,
                                "Level_Index": level_index,
                                "Box_Instance": item["Box_Instance"],
                                "Box_Type": item["Box_Type"],
                                "x": x_cursor, "y": 0, "z": shelf_used_height,
                                "Width": w, "Depth": d, "Height": h,
                                "Rotated": rot
                            })
                            placed_in_level.append(item.name)
                            x_cursor += w
                            placed = True
                            break
                if not placed:
                    continue
            if placed_in_level:
                unplaced = unplaced.drop(index=placed_in_level).reset_index(drop=True)
                shelf_used_height += level_height
                level_index += 1
            else:
                break

    placements_df = pd.DataFrame(placements)

    st.subheader("📊 Placement Results")
    st.dataframe(placements_df)

    result_excel = pd.ExcelWriter("shelf_arrangement.xlsx", engine="openpyxl")
    placements_df.to_excel(result_excel, sheet_name="Placements", index=False)
    unplaced.to_excel(result_excel, sheet_name="Unplaced", index=False)
    result_excel.close()
    with open("shelf_arrangement.xlsx", "rb") as f:
        st.download_button("⬇️ Download Excel Results", f, file_name="shelf_arrangement.xlsx")

    st.subheader("🖼️ 3D Visualization")
    fig = plt.figure(figsize=(10,7))
    ax = fig.add_subplot(111, projection="3d")
    box_colors = plt.cm.tab20.colors
    shelf_colors = plt.cm.Pastel1.colors

    # --- Draw shelves with labels ---
    for i, (_, shelf) in enumerate(shelves.iterrows()):
        shelf_color = shelf_colors[i % len(shelf_colors)]
        plot_shelf(ax, (0, 0, 0), shelf["Width"], shelf["Depth"], shelf["Height"], color=shelf_color)
        ax.text(
            shelf["Width"] / 2,
            shelf["Depth"] / 2,
            shelf["Height"] / 2,
            str(shelf["Shelf_ID"]),
            color="black",
            fontsize=10,
            ha="center",
            va="center",
            weight="bold"
        )

    # --- Draw placed boxes ---
    for i, (_, p) in enumerate(placements_df.iterrows()):
        plot_cube(ax, (p["x"], p["y"], p["z"]),
                  p["Width"], p["Depth"], p["Height"],
                  color=box_colors[i % len(box_colors)])

    # --- Draw unplaced boxes grouped by type ---
    if not unplaced.empty:
        offset_y = max(shelves["Depth"]) + 30
        group_spacing = 40
        for g, group in unplaced.groupby("Box_Type", sort=False):
            base_x = list(unplaced["Box_Type"].unique()).index(g) * group_spacing
            for j, (_, u) in enumerate(group.iterrows()):
                plot_cube(ax, (base_x + j * (u["Width"] + 5), offset_y, 0),
                          u["Width"], u["Depth"], u["Height"],
                          color="red")
                ax.text(base_x + j * (u["Width"] + 5) + u["Width"]/2,
                        offset_y + u["Depth"]/2,
                        u["Height"]/2,
                        f"{u['Box_Instance']}",
                        color="red",
                        fontsize=8,
                        ha="center",
                        va="center")
            # Group label
            ax.text(base_x, offset_y + 10, max(group["Height"]) + 10,
                    f"Unplaced {g}",
                    color="darkred",
                    fontsize=10,
                    weight="bold")

    ax.set_xlabel("Width (X)")
    ax.set_ylabel("Depth (Y)")
    ax.set_zlabel("Height (Z)")
    st.pyplot(fig)
