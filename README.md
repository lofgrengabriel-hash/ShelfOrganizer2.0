# Shelf Arranger Web App

This is a Streamlit web app for arranging boxes on shelves with 3D visualization.

## How to run

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   streamlit run shelf_app.py
   ```

3. Upload your Excel file with two sheets:
   - **Shelves**: Shelf_ID, Width, Height, Depth
   - **Boxes**: Box_ID, Width, Height, Depth, Quantity, AllowRotation, Priority

4. View placements, download results, and see a 3D visualization with shelves, placed boxes, and unplaced boxes grouped by type.
