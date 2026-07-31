from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_PATH = Path(__file__).with_name("count_merged.csv")
REQUIRED_COLUMNS = {
    "fire_station_name",
    "출동거리_2020",
    "출동거리_2021",
}


st.set_page_config(
    page_title="소방서별 출동거리 증가율",
    page_icon="🚒",
    layout="wide",
)


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)

    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")

    data = data.copy()
    data["출동거리_증가율"] = (
        (data["출동거리_2021"] - data["출동거리_2020"])
        / data["출동거리_2020"]
        * 100
    )
    data = data.replace([float("inf"), float("-inf")], pd.NA)
    data = data.dropna(subset=["출동거리_증가율"])
    data = data.sort_values("출동거리_증가율", ascending=False).reset_index(drop=True)

    data["구분"] = "양수"
    data.loc[data["출동거리_증가율"] < 0, "구분"] = "음수"
    data.loc[data.index < 5, "구분"] = "증가율 상위 5개"

    return data


st.title("2020년 대비 2021년 출동거리 증가율")
st.caption("소방서별 출동거리 증가율을 내림차순으로 비교합니다.")

try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error("count_merged.csv 파일을 app.py와 같은 폴더에 넣어주세요.")
    st.stop()
except (ValueError, pd.errors.ParserError) as error:
    st.error(f"데이터를 불러올 수 없습니다: {error}")
    st.stop()

color_map = {
    "증가율 상위 5개": "#DC2626",
    "양수": "#F97316",
    "음수": "#2563EB",
}

fig = px.bar(
    df,
    x="출동거리_증가율",
    y="fire_station_name",
    orientation="h",
    color="구분",
    color_discrete_map=color_map,
    text=df["출동거리_증가율"].map(lambda value: f"{value:.1f}%"),
    custom_data=["출동거리_2020", "출동거리_2021"],
    labels={
        "fire_station_name": "소방서",
        "출동거리_증가율": "증가율 (%)",
        "구분": "구분",
    },
)

fig.update_traces(
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{y}</b><br>"
        "2020년 출동거리: %{customdata[0]:.2f}<br>"
        "2021년 출동거리: %{customdata[1]:.2f}<br>"
        "증가율: %{x:.2f}%<extra></extra>"
    ),
)
fig.update_layout(
    height=760,
    margin=dict(l=20, r=60, t=20, b=20),
    legend_title_text="구분",
    yaxis=dict(autorange="reversed"),
    xaxis=dict(ticksuffix="%", zeroline=True, zerolinewidth=1),
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("정렬된 데이터 보기"):
    display_df = df[
        [
            "fire_station_name",
            "출동거리_2020",
            "출동거리_2021",
            "출동거리_증가율",
        ]
    ].rename(columns={"fire_station_name": "소방서"})

    st.dataframe(
        display_df.style.format(
            {
                "출동거리_2020": "{:.2f}",
                "출동거리_2021": "{:.2f}",
                "출동거리_증가율": "{:.2f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
