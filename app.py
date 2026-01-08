import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
# 한글 폰트 자동 설정 라이브러리
import koreanize_matplotlib 

st.set_page_config(layout="wide")
st.title("📋 현장 보고서 이미지 생성기")

st.markdown("""
**[사용법]**
1. 노션/엑셀 데이터를 드래그 복사(`Ctrl+C`)
2. 아래 표 첫 칸 클릭 후 붙여넣기(`Ctrl+V`)
3. **[이미지 생성]** 버튼 클릭
""")

# --- 1. 컬럼 정의 ---
columns = [
    '날짜', '지역', '사업부', '현장명', '최저 기온', 
    '옥내작업', '작업 시작 시간(옥내)', 
    '옥외작업', '작업 시작 시간(옥외)', 
    '보온양생 작업 여부', '조치 사항'
]

if 'df_data' not in st.session_state:
    st.session_state.df_data = pd.DataFrame(columns=columns, index=range(5)).fillna("")

# --- 2. 데이터 입력창 ---
edited_df = st.data_editor(
    st.session_state.df_data,
    num_rows="dynamic",
    use_container_width=True,
    height=300
)

# --- 3. 이미지를 그려주는 함수 (Matplotlib 활용) ---
def create_table_image(df):
    # 그림판 크기 설정 (데이터 양에 따라 세로 길이 자동 조절)
    rows, cols = df.shape
    fig_height = rows * 0.8 + 1.5 # 헤더 공간 포함
    fig, ax = plt.subplots(figsize=(20, fig_height)) # 가로 20인치 고정
    
    # 축 숨기기 (그래프가 아니니까)
    ax.axis('off')
    ax.axis('tight')
    
    # 표 그리기
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc='center',
        loc='center',
        colWidths=[0.12, 0.05, 0.08, 0.25, 0.06, 0.08, 0.1, 0.08, 0.1, 0.1, 0.25] # 컬럼 너비 비율 조절
    )
    
    # 스타일 꾸미기
    table.auto_set_font_size(False)
    table.set_fontsize(13) # 글자 크기
    table.scale(1, 2.5) # 표 셀 높이 늘리기 (시원시원하게)
    
    # 헤더(첫 줄) 색상 꾸미기 및 정렬
    for (row, col), cell in table.get_celld().items():
        if row == 0: # 헤더
            cell.set_facecolor('#e6f2ff') # 연한 파란색 배경
            cell.set_text_props(weight='bold') # 굵은 글씨
        
        # '조치 사항' 처럼 내용이 긴 컬럼은 왼쪽 정렬
        if col == 10 and row > 0: 
            cell.set_text_props(ha='left')
            
    # 제목 추가
    plt.title("■ 금일 영하 12도 이하 현장 리스트", fontsize=20, weight='bold', loc='left', pad=20)
    
    return fig

# --- 4. 버튼 동작 ---
if st.button("📸 보고용 이미지 생성"):
    # 현장명이 있는 데이터만 필터링
    final_df = edited_df[edited_df['현장명'] != ""]
    
    if final_df.empty:
        st.error("데이터를 입력해주세요!")
    else:
        with st.spinner('이미지 그리는 중...'):
            # Matplotlib으로 이미지 생성
            fig = create_table_image(final_df)
            
            # 이미지 파일로 저장
            output_filename = "site_report.png"
            fig.savefig(output_filename, bbox_inches='tight', dpi=200) # dpi=200으로 고해상도 저장
            
            # 화면에 보여주기
            st.image(output_filename)
            
            # 다운로드 버튼
            with open(output_filename, "rb") as file:
                st.download_button(
                    label="📥 이미지 다운로드",
                    data=file,
                    file_name=output_filename,
                    mime="image/png"
                )
