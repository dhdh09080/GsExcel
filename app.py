import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 1. 페이지 설정
st.set_page_config(page_title="현장 보고서 생성기", layout="wide")

# -----------------------------------------------------------
# [중요] 한글 폰트 설정 (서버에 폰트가 없을 경우 자동 다운로드)
# -----------------------------------------------------------
@st.cache_resource
def set_korean_font():
    # 나눔고딕 폰트 파일명
    font_file = "NanumGothic.ttf"
    
    # 폰트 파일이 없으면 구글 폰트 저장소에서 다운로드
    if not os.path.exists(font_file):
        import urllib.request
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        urllib.request.urlretrieve(url, font_file)
    
    # 폰트 등록 및 설정
    fm.fontManager.addfont(font_file)
    plt.rc('font', family='NanumGothic')

# 폰트 설정 실행
set_korean_font()
# -----------------------------------------------------------

st.title("🏗️ 현장 보고용 이미지 생성기")
st.markdown("""
**[사용법]**
1. 노션이나 엑셀에서 데이터를 드래그하여 복사(`Ctrl+C`)하세요.
2. 아래 표의 **첫 번째 칸**을 클릭하고 붙여넣기(`Ctrl+V`)하세요.
3. 입력이 끝나면 맨 아래 **[📸 보고용 이미지 생성]** 버튼을 누르세요.
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

# 4. 표를 그림으로 그려주는 함수
def create_table_image(df):
    rows, cols = df.shape
    fig_height = rows * 0.8 + 2
    
    # 캔버스 생성
    fig, ax = plt.subplots(figsize=(22, fig_height))
    ax.axis('off')
    
    # 표 그리기
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc='center',
        loc='center',
        colWidths=[0.1, 0.05, 0.08, 0.25, 0.06, 0.08, 0.1, 0.08, 0.1, 0.1, 0.3] 
    )
    
    table.auto_set_font_size(False)
    table.set_fontsize(13)
    table.scale(1, 2.5)
    
    for (row, col), cell in table.get_celld().items():
        if row == 0: 
            cell.set_facecolor('#e6f2ff')
            cell.set_text_props(weight='bold')
            cell.set_height(0.15)
        
        if col == 10 and row > 0: 
            cell.set_text_props(ha='left')
            
    plt.title("■ 금일 영하 12도 이하 현장 리스트", fontsize=25, weight='bold', loc='left', pad=20)
    
    return fig

# 5. 버튼 클릭 시 동작
if st.button("📸 보고용 이미지 생성", type="primary"):
    final_df = edited_df[edited_df['현장명'] != ""]
    
    if final_df.empty:
        st.warning("⚠️ 데이터를 먼저 입력해주세요!")
    else:
        with st.spinner('이미지를 예쁘게 그리는 중입니다...'):
            try:
                fig = create_table_image(final_df)
                
                output_filename = "daily_report_site.png"
                fig.savefig(output_filename, bbox_inches='tight', dpi=200, pad_inches=0.5)
                
                st.success("이미지 변환 완료!")
                st.image(output_filename)
                
                with open(output_filename, "rb") as file:
                    st.download_button(
                        label="📥 이미지 파일 다운로드",
                        data=file,
                        file_name=output_filename,
                        mime="image/png"
                    )
            except Exception as e:
                st.error(f"에러가 발생했습니다: {e}")
