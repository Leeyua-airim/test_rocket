import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import warnings

# mpl.rcParams["font.family"] = "AppleGothic"
mpl.rcParams["axes.unicode_minus"] = False

st.set_page_config(
    page_title="RocketPunch Platform Insight Dashboard",
    layout="wide"
)

@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path)
    return df

df = load_data("dataset/rocket_dataset_260105.csv")

#====================================================================================

st.markdown(
    "<h1 style='text-align: center;'>RocketPunch 플랫폼 1차 인사이트</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align: center; font-size: 0.9rem; color: gray;'>"
    "본 대시보드는 https://www.rocketpunch.com/ 플랫폼의 데이터 일부를 크롤링하여 제작되었습니다."
    "</p>",
    unsafe_allow_html=True
)

with st.container():
    st.subheader("데이터 출처")

    st.caption(
        "본 분석에 사용된 원본 데이터입니다. "
        "외부 검토 및 추가 분석을 위해 자유롭게 다운로드하실 수 있습니다."
    )

    st.download_button(
        label="원본 데이터 다운로드 (CSV)",
        data=df.to_csv(index=False, encoding="utf-8-sig"),
        file_name="rocket_dataset_260105.csv",
        mime="text/csv"
    )




st.divider()

#====================================================================================
st.sidebar.header("분석 옵션")


auth_options = ["전체", "인증된 계정", "비인증 계정"]
selected_auth = st.sidebar.selectbox("계정 인증 여부", auth_options)

career_options = sorted(df["경력"].dropna().unique().tolist())

selected_careers = st.sidebar.multiselect(
    "경력 선택(중복선택가능)",
    career_options,
    default=career_options
)

filtered_df = df[df["경력"].isin(selected_careers)]

if selected_auth == "인증된 계정":
    filtered_df = filtered_df[filtered_df["계정인증여부"] == "인증된 계정"]
elif selected_auth == "비인증 계정":
    filtered_df = filtered_df[filtered_df["계정인증여부"].isna()]


#====================================================================================

st.markdown(
    "<br><br><h3 style='text-align: center;'>계정별 글 작성빈도 분석</h3>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label = "총 게시글 수", 
        value = len(filtered_df),
        help = "26년 1월 5일 기준, 크롤링을 통해 획득한 게시글 수 입니다.")

with col2:
    st.metric(
        label="활동 계정 수",
        value=filtered_df["로켓계정_ID"].nunique(),
        help = "사이드 바 내 선택된 값 기준"
    )

with col3:
    auth_ratio = (
        filtered_df["계정인증여부"]
        .eq("인증된 계정")
        .mean()
    )
    st.metric(
        label="인증 계정 비율",
        value=f"{auth_ratio:.1%}",
        help="선택된 조건 내에서 인증된 계정이 차지하는 비율입니다."
    )


#====================================================================================



display_cols = ["성명",  "게시글 수", "로켓계정_ID"]

post_count = (
    filtered_df
    .groupby(["로켓계정_ID", "성명"])
    .size()
    .reset_index(name="게시글 수")
    .sort_values("게시글 수", ascending=False)
)

post_count_display = post_count[display_cols]

st.dataframe(
    post_count_display.head(30).reset_index(drop=True),
    use_container_width=True
)


#====================================================================================
with st.container():

    st.markdown(
        """
        <br><br><h3 style='text-align:center; margin-bottom: 0;'>부스트지수 분포 분석</h3>
        <p style='text-align:center; color: gray; '>선택된 조건 내 게시글의 반응 분포를 요약한 지표입니다.</p>
        """
        ,
        unsafe_allow_html=True
    )

        

    filtered_df["부스트지수"] = pd.to_numeric(
        filtered_df["부스트지수"],
        errors="coerce"
    ).fillna(0)
    
    boost_series = filtered_df["부스트지수"].dropna()

    boost_min = boost_series.min()
    boost_median = boost_series.median()
    boost_mean = boost_series.mean()
    boost_max = boost_series.max()

    # 상단: 수치 요약
    bcol1, bcol2, bcol3, bcol4 = st.columns(4)

    with bcol1:
        st.metric("Min", int(boost_min))
    with bcol2:
        st.metric("Median", int(boost_median))
    with bcol3:
        st.metric("Mean", round(boost_mean, 2))
    with bcol4:
        st.metric("Max", int(boost_max))



    with st.expander("**부스트지수 분포 상세 보기**"):
        fig, ax = plt.subplots(figsize=(6, 3))

        # 정수 중심 bin
        bins = np.arange(
            boost_series.min() - 0.5,
            boost_series.max() + 1.5,
            1
        )

        ax.hist(boost_series, 
                bins=bins, 
                edgecolor = 'black',
                linewidth=0.4)

        # 평균 및 중앙값 경계선
        ax.axvline(boost_median, linestyle="--", linewidth=1.5, label="중앙값")
        ax.axvline(boost_mean, linestyle=":", linewidth=1.5, label="평균값")

        # 군집 경계선 (경계값 직접 설정)
        # 군집 경계 기준 (정책적으로 명시)
        LOW_Q = 0.5    # 하위 50%
        MID_Q = 0.8    # 상위 20% 시작

        q_low = boost_series.quantile(LOW_Q)
        q_mid = boost_series.quantile(MID_Q)

        ax.axvline(q_low, color="red", linestyle="-.", linewidth=1.5, label="저/중 경계(하위 50%)")
        ax.axvline(q_mid, color="purple", linestyle="-.", linewidth=1.5, label="중/고 경계(상위 20%)")

        ax.set_xlabel("부스트지수", fontsize=9)
        ax.set_ylabel("게시글 수", fontsize=9)
        ax.set_title("부스트지수 분포", fontsize=10)

        ax.set_xticks(
            np.arange(
                int(boost_series.min()),
                int(boost_series.max()) + 1,
                1
            )
        )

        ax.tick_params(axis="both", labelsize=8)
        ax.legend(fontsize=8)

        # 🔑 군집 주석
        x_min = boost_series.min()
        x_max = boost_series.max()

        low_center = (x_min + q_low) / 2
        mid_center = (q_low + q_mid) / 2
        high_center = (q_mid + x_max) / 2

        y_max = ax.get_ylim()[1]
        ax.text(low_center, y_max * 0.9, "저반응", fontsize=6, ha="center")
        ax.text(mid_center, y_max * 0.9, "중간 반응", fontsize=6, ha="center")
        ax.text(high_center, y_max * 0.9, "고반응", fontsize=6, ha="center")

        st.pyplot(fig)


        st.subheader("구간별 계정에 따른 부스트지수 및 게시글")
        cluster_option = st.selectbox(
            "",
            ["저 반응 (하위 50%)", "중간 반응 (50~80%)", "고 반응 (상위 20%)"])
        
        if cluster_option == "저 반응 (하위 50%)":
            df_cluster = filtered_df[
                (filtered_df["부스트지수"] <= q_low)
            ]
        elif cluster_option == "중간 반응 (50~80%)":
            df_cluster = filtered_df[
                (filtered_df["부스트지수"] > q_low) & 
                (filtered_df["부스트지수"] <= q_mid)
            ]
        else:
            df_cluster = filtered_df[
                (filtered_df["부스트지수"] > q_mid)
            ]
        text_cols = ["본문1", "본문2", "본문3"]

        display_df = df_cluster[
            ["성명", "로켓계정_ID", "부스트지수"] + text_cols
            ].copy()


        display_df["글 미리보기"] = (
            display_df[text_cols]
            .fillna("")
            .agg(" ".join, axis=1)
            .str.slice(0, 80) + "..."
        )

        st.dataframe(
        display_df[["성명", "부스트지수", "글 미리보기"]].head(20),
        use_container_width=True
        )
        
        st.subheader("부스트지수 상위 계정")

        boost_rank = (
            filtered_df
            .groupby(["로켓계정_ID", "성명"])
            .agg(
                평균_부스트지수=("부스트지수", "mean"),
                게시글_수=("부스트지수", "count")
            )
            .reset_index()
            .sort_values("평균_부스트지수", ascending=False)
        )

        st.dataframe(
            boost_rank.head(20),
            use_container_width=True
        )
        # 인사이트 영역
        st.markdown("**Research Summary Report**")
        st.markdown(
            """
            [안내] 본 서머리는 내리터브의 리서처가 크롤링을 통해 수집한 데이터를 바탕으로 직접 작성한 글 임을 밝힙니다. 
            
            부스트지수의 계정 및 군집단위 분석 결과
            인증 계정과 비인증 계정은 모든 군집간의 유의미한 차이가 발생되고 있음을 시사합니다.

            **[전체 계정 기준]**
            - 저 반응 군집 : 0 ~ 6 | 중 반응 군집 : 7 ~ 11 | 고 반응 군집 : 12 ~ 
            
            **[인증 계정 기준]**
            - 저 반응 군집 : 0 ~ 8 | 중 반응 군집 : 9 ~ 15 | 고 반응 군집 : 16 ~ 
            
            **[비인증 계정 기준]** 
            - 저 반응 군집 : 0 ~ 1 | 중 반응 군집 : 2 ~ 5 | 고 반응 군집 : 6 ~ 

            특이사항은 다음과 같습니다.
            1. 비인증 계정의 경우 가장 높은 35건의 부스트지수를 갖는 게시글이 존재합니다. 해당 글은 매우 오래전(약 4년전)에 특정 주제가 없는 이상적인 내용의 글로 작성되었고, 계정('이재하') 또한 지금은 탈퇴된 것으로 확인됩니다.
            2. 인증된 계정의 경우 중 반응 및 고 반응의 작성자 및 작성 내용을 확인해본 결과 특정 사용자('조만희')가 다양한 주제로 다수의 글을 업로드 한 것으로 확인되었습니다.
            인증 계정은 특정 소수의 사용자에게서 부스트지수가 높게 관측되며, 비인증 계정의 경우 중간 반응 구간에서의 다수의 주제 및 다수의 계정이 활동하고 있는 것으로 관측됩니다. 

            **[고객 관점]**
            - 고객들이 계정 인증에 대한 장점을 아직 느끼지 못하고 있다는 것으로 추측할 수 있습니다.
            
            **[로켓펀치 관점]**
            - 로켓펀치는 인증 계정이 왜 필요한지 명확하게 설계할 필요가 있습니다.
            """
        )
                        
    
    st.markdown("\n")

    st.markdown("\n")
    



#====================================================================================

st.markdown(
    "<h3 style='text-align: center;'>계정별 등록된 경력 분포</h3>",
    unsafe_allow_html=True
)
st.subheader("경력 분포")

career_dist = (
    filtered_df["경력"]
    .value_counts()
    .reset_index()
)
career_dist.columns = ["경력", "게시글 수"]

st.bar_chart(career_dist.set_index("경력"))

#====================================================================================

st.subheader("댓글 수 분포")

st.histogram = st.bar_chart(
    filtered_df["댓글_수"]
    .fillna(0)
    .value_counts()
    .sort_index()
)


#====================================================================================



