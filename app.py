import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import textwrap

# 1. 페이지 설정
st.set_page_config(page_title="현장 보고서 생성기", layout="wide")

# -----------------------------------------------------------
# [폰트 설정]
# -----------------------------------------------------------
@st.cache_resource
def set_korean_font():
    font_file = "NanumGothic.ttf"
    if not os.path.exists(font_file):
        import urllib.request
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        urllib.request.urlretrieve(url, font_file)
    fm.fontManager.addfont(font_file)
    plt.rc('font', family='NanumGothic')

set_korean_font()
# -----------------------------------------------------------

st.title("🏗️ 현장 보고용 이미지 생성기")
st.markdown("""
**[사용법]**
1. 엑셀 데이터를 복사(`Ctrl+C`)하여 아래 표에 붙여넣기(`Ctrl+V`)하세요.
2. **[📸 보고용 이미지 생성]** 버튼을 누르면 이미지와 **카톡용 요약 텍스트**가 생성됩니다.
""")

# 2. 초기 데이터 및 컬럼 설정
columns = [
    '날짜', '지역', '사업부', '현장명', '최저 기온', 
    '옥내작업', '작업 시작 시간(옥내)', 
    '옥외작업', '작업 시작 시간(옥외)', 
    '보온양생 작업 여부', '조치 사항'
]

if 'df_data' not in st.session_state:
    st.session_state.df_data = pd.DataFrame(columns=columns, index=range(5)).fillna("")

# 3. 데이터 입력창
edited_df = st.data_editor(
    st.session_state.df_data,
    num_rows="dynamic",
    use_container_width=True,
    height=300
)

# 4. 표 이미지 생성 함수
def create_table_image(df):
    wrap_width = 18 
    formatted_data = []
    row_lines = []
    
    # 원본 데이터 보존을 위해 복사본 사용
    plot_df = df.copy()
    
    for idx, row in plot_df.iterrows():
        row_data = list(row.values)
        action_item = str(row_data[10]) # 조치 사항 컬럼
        
        if action_item:
            wrapped_text = "\n".join(textwrap.wrap(action_item, width=wrap_width))
            row_data[10] = wrapped_text
            lines = wrapped_text.count('\n') + 1
        else:
            lines = 1
            
        formatted_data.append(row_data)
        row_lines.append(lines)

    total_lines = sum(row_lines)
    if total_lines < 1: total_lines = 1
    
    fig_height = total_lines * 0.8 + 2
    
    fig, ax = plt.subplots(figsize=(22, fig_height))
    ax.axis('off')
    
    table = ax.table(
        cellText=formatted_data,
        colLabels=plot_df.columns,
        cellLoc='center',
        loc='center',
        colWidths=[0.1, 0.05, 0.08, 0.25, 0.06, 0.08, 0.1, 0.08, 0.1, 0.1, 0.3] 
    )
    
    table.auto_set_font_size(False)
    table.set_fontsize(13)
    table.scale(1, 2.5)
    
    header_height_rel = 0.9 / fig_height
    
    for (row, col), cell in table.get_celld().items():
        if row == 0: 
            cell.set_facecolor('#e6f2ff')
            cell.set_text_props(weight='bold')
            cell.set_height(header_height_rel)
        else:
            lines = row_lines[row - 1]
            row_height_rel = (lines * 0.8) / fig_height
            cell.set_height(row_height_rel)
        
        if col == 10 and row > 0: 
            cell.set_text_props(ha='left')
            
    plt.title("■ 금일 영하 12도 이하 현장 리스트", fontsize=25, weight='bold', loc='center', pad=20)
    
    return fig

# [수정됨] 5. 카카오톡 스타일 텍스트 요약 생성 함수
def generate_text_summary(df):
    # 1. 제목 및 현장 리스트 구성
    count = len(df)
    # 현장명 리스트를 콤마로 연결 (예: 공릉, 중계, 이천자이...)
    site_names = ", ".join(df['현장명'].astype(str).tolist())

    summary = "[보고 한파(영하12도) 대상 현장]\n"
    summary += f"- 영하 12도 {count}개 현장이며,\n"
    summary += f"  : {site_names}\n\n"

    # 2. 조치 사항 구성 (내용이 같은 현장끼리 묶기)
    # 조치 사항의 줄바꿈 문자는 공백으로 치환하여 한 줄로 만듦
    # unique()를 사용하여 중복된 조치사항을 제거하고 확인
    unique_actions = df['조치 사항'].astype(str).unique()

    if len(unique_actions) == 1:
        # 케이스 1: 모든 현장의 조치사항이 같을 경우 (스크린샷처럼 깔끔하게 출력)
        action = unique_actions[0]
        summary += f"- {action}"
    else:
        # 케이스 2: 현장마다 조치사항이 다를 경우 (현장별 구분 출력)
        summary += "- 주요 조치 사항:\n"
        for action in unique_actions:
            # 해당 조치사항을 가진 현장 찾기
            target_sites = df[df['조치 사항'] == action]['현장명'].tolist()
            sites_str = ",".join(target_sites)
            
            # (예: [공릉, 중계] 옥외작업 중지...)
            summary += f"  [{sites_str}] {action}\n"

    return summary

# 6. 버튼 클릭 시 동작
if st.button("📸 보고용 이미지 생성", type="primary"):
    final_df = edited_df[edited_df['현장명'] != ""]
    
    if final_df.empty:
        st.warning("⚠️ 데이터를 먼저 입력해주세요!")
    else:
        with st.spinner('보고서를 생성 중입니다...'):
            try:
                # 1. 이미지 생성
                fig = create_table_image(final_df)
                output_filename = "daily_report_site.png"
                fig.savefig(output_filename, bbox_inches='tight', dpi=200, pad_inches=0.5)
                
                # 2. 텍스트 요약 생성 (NEW)
                text_report = generate_text_summary(final_df)
                
                # [화면 구성]
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.success("✅ 이미지 생성 완료")
                    st.image(output_filename)
                    with open(output_filename, "rb") as file:
                        st.download_button(
                            label="📥 이미지 다운로드",
                            data=file,
                            file_name=output_filename,
                            mime="image/png"
                        )
                
                with col2:
                    st.info("✅ 텍스트 요약 (복사용)")
                    # 텍스트 박스 높이를 조절하여 보기 편하게 함
                    st.text_area("Ctrl+A, Ctrl+C 하여 사용하세요", value=text_report, height=200)
                    
            except Exception as e:
                st.error(f"에러가 발생했습니다: {e}")
