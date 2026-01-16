import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import textwrap  # [추가] 텍스트 줄바꿈을 위한 모듈

# 1. 페이지 설정
st.set_page_config(page_title="현장 보고서 생성기", layout="wide")

# -----------------------------------------------------------
# [폰트 설정] 서버에 폰트가 없으면 자동으로 다운로드해서 적용
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

# 4. 표를 그림으로 그려주는 함수 (수정됨)
def create_table_image(df):
    # [수정] 데이터 전처리: 텍스트 줄바꿈 및 행 높이 계산
    wrap_width = 18  # 한 줄에 들어갈 글자 수 (약 18~20자 추천)
    
    formatted_data = []
    row_lines = []   # 각 행이 몇 줄인지 저장할 리스트
    
    for idx, row in df.iterrows():
        row_data = list(row.values)
        
        # 10번째 인덱스 ('조치 사항') 처리
        action_item = str(row_data[10])
        if action_item:
            # textwrap을 이용해 지정된 너비로 줄바꿈 처리
            wrapped_text = "\n".join(textwrap.wrap(action_item, width=wrap_width))
            row_data[10] = wrapped_text
            # 줄 수 계산 (기본 1줄 + 줄바꿈 개수)
            lines = wrapped_text.count('\n') + 1
        else:
            lines = 1
            
        formatted_data.append(row_data)
        row_lines.append(lines)

    # [수정] 전체 이미지 높이 동적 계산
    # 내용이 많아지면 이미지 세로 길이도 늘어나야 함 (기본 0.8인치 * 줄 수)
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
    
    # [수정] 행 높이 개별 적용
    # 헤더 높이(고정)와 데이터 행 높이(줄 수에 비례)를 각각 설정
    header_height_rel = 0.9 / fig_height  # 헤더는 약 0.9인치 높이로 고정
    
    for (row, col), cell in table.get_celld().items():
        if row == 0: 
            # 헤더 스타일
            cell.set_facecolor('#e6f2ff')
            cell.set_text_props(weight='bold')
            cell.set_height(header_height_rel)
        else:
            # 데이터 행 스타일 및 높이 조절
            lines = row_lines[row - 1] # 현재 행의 줄 수
            
            # 행 높이: (줄 수 * 0.8인치) / 전체 이미지 높이
            row_height_rel = (lines * 0.8) / fig_height
            cell.set_height(row_height_rel)
        
        # 조치 사항(마지막 열)은 왼쪽 정렬
        if col == 10 and row > 0: 
            cell.set_text_props(ha='left')
            
    plt.title("■ 금일 영하 12도 이하 현장 리스트", fontsize=25, weight='bold', loc='center', pad=20)
    
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
