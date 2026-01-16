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
1. 노션이나 엑셀 데이터를 복사(`Ctrl+C`)하여 아래 표에 붙여넣기(`Ctrl+V`)하세요.
2. **[📸 보고용 이미지 생성]** 버튼을 누르면 **이미지**와 **요약 텍스트**가 생성됩니다.
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

# 4. 표를 그림으로 그려주는 함수 (텍스트 래핑 포함)
def create_table_image(df):
    wrap_width = 18 
    formatted_data = []
    row_lines = []
    
    for idx, row in df.iterrows():
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
        colLabels=df.columns,
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

# [추가됨] 5. 텍스트 요약 생성 함수
def generate_text_summary(df):
    # 날짜가 있으면 첫 번째 행의 날짜를 가져오고, 없으면 오늘 날짜
    try:
        report_date = df.iloc[0]['날짜']
    except:
        report_date = "금일"

    summary = f"📋 [{report_date} 혹한기 현장 점검 보고]\n\n"
    summary += f"■ 모니터링 대상: 총 {len(df)}개 현장\n"
    summary += "■ 주요 조치 사항:\n"
    
    for idx, row in df.iterrows():
        site_name = row['현장명']
        temp = row['최저 기온']
        # 텍스트 보고에서는 줄바꿈 문자를 공백으로 변경하여 한 줄로 표시
        action = str(row['조치 사항']).replace('\n', ' ')
        
        summary += f"- {site_name} ({temp}): {action}\n"
    
    summary += "\n이상입니다."
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
                
                # 2. 텍스트 요약 생성
                text_report = generate_text_summary(final_df)
                
                # [화면 구성] 왼쪽: 이미지 / 오른쪽: 텍스트 복사창
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
                    st.info("✅ 텍스트 요약 생성 완료 (복사해서 사용하세요)")
                    st.text_area("메신저 전송용 텍스트", value=text_report, height=400)
                    
            except Exception as e:
                st.error(f"에러가 발생했습니다: {e}")
