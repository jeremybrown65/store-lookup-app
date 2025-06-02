import streamlit as st
import pandas as pd
from io import BytesIO
from difflib import get_close_matches
import os

DEFAULT_PATH = "default_store_list.xlsx"

def load_store_list():
    try:
        return pd.read_excel(DEFAULT_PATH)
    except Exception:
        return pd.DataFrame()

def save_store_list(df):
    df.to_excel(DEFAULT_PATH, index=False)

def get_region_code(df, input_value):
    input_value = str(input_value).strip().lower()
    match = df[
        df['Store Number'].astype(str).str.strip().str.lower().eq(input_value) |
        df['Mall / Store Name'].astype(str).str.strip().str.lower().eq(input_value)
    ]
    if not match.empty:
        return str(match.iloc[0]['Region Code'])
    return None

def find_closest_stores(df, input_value):
    names = df['Mall / Store Name'].astype(str).str.strip().tolist()
    lower_name_map = {name.lower(): name for name in names}
    matches = get_close_matches(input_value.strip().lower(), lower_name_map.keys(), n=5, cutoff=0.4)
    if matches:
        original_matches = [lower_name_map[m] for m in matches]
        return df[df['Mall / Store Name'].str.strip().isin(original_matches)]
    return pd.DataFrame()

def filter_by_flag(df, flag):
    if flag.capitalize() in df.columns:
        return df[df[flag.capitalize()].astype(str).str.upper() == 'X']
    return pd.DataFrame()

def filter_by_store_numbers(df, numbers):
    numbers = [str(n).strip() for n in numbers.split(',')]
    return df[df['Store Number'].astype(str).isin(numbers)]

st.title("Store Lookup & Region Code Generator")

st.header("1. Upload or Replace Store List")
store_file = st.file_uploader("Upload new store list (.xlsx)", type="xlsx")
if store_file:
    store_df = pd.read_excel(store_file)
    save_store_list(store_df)
    st.success("Store list uploaded and saved as the new default.")
else:
    store_df = load_store_list()
    st.info("Using default store list from the repository.")

if store_df.empty:
    st.warning("No store list available.")
    st.stop()

st.header("2. Choose Store Mode")
mode = st.radio("Single or Multiple Store?", ["Single", "Multiple"])

if mode == "Single":
    store_input = st.text_input("Enter store number or name")
    if store_input:
        region_code = get_region_code(store_df, store_input)
        if region_code:
            st.success(f"This bills to: GL code 170.3010.{region_code}.000.6340.623020.000.0000")
        else:
            close_matches_df = find_closest_stores(store_df, store_input)
            if not close_matches_df.empty:
                options = close_matches_df['Mall / Store Name'].tolist()
                selected = st.selectbox("Did you mean one of these?", options)
                if selected:
                    match_row = close_matches_df[close_matches_df['Mall / Store Name'] == selected].iloc[0]
                    region_code = str(match_row['Region Code'])
                    st.success(f"This bills to: GL code 170.3010.{region_code}.000.6340.623020.000.0000")
            else:
                st.error("Store not found.")

elif mode == "Multiple":
    multi_input = st.text_input("Enter store numbers (comma-separated) or type a flag like 'scrubs', 'kids', 'swim'")
    if multi_input:
        if multi_input.lower() in [c.lower() for c in store_df.columns]:
            filtered = filter_by_flag(store_df, multi_input.lower())
        else:
            filtered = filter_by_store_numbers(store_df, multi_input)

        if not filtered.empty:
            st.success(f"Found {len(filtered)} matching stores.")
            st.dataframe(filtered)

            output = BytesIO()
            filtered.to_excel(output, index=False, engine='openpyxl')
            st.download_button("Download filtered list", output.getvalue(), file_name="filtered_stores.xlsx")
        else:
            st.warning("No matches found.")
