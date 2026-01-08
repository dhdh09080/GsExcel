import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
# 한글 폰트가 깨지지 않도록 자동으로 설정해주는 라이브러리
import koreanize_matplotlib 

# 1. 페이지 설정
st.set_page_config(page_title="현장 보고서 생성기", layout="wide")

st.title("🏗️ 현장 보고용 이미지 생성기")
st.markdown("""
**[사용법]**
1. 노션이나 엑셀에서 데이터를 드래그하여 복사(`Ctrl+C`)하세요.
2. 아래 표의 **첫 번째 칸**을 클릭하고 붙여넣기(`Ctrl+V`)하세요.
3. 입력이 끝나면 맨 아래 **[📸 보고용 이미지 생성]** 버튼을 누르세요.
""")

# 2. 초기 데이터 및 컬럼 설정 (보여주신 이미지 순서대로)
columns = [
    '날짜', '지역', '사업부', '현장명', '최저 기온', 
    '옥내작업', '작업 시작 시간(옥내)', 
    '옥외작업', '작업 시작 시간(옥외)', 
    '보온양생 작업 여부', '조치 사항'
]

# 처음 접속했을 때 빈 표를 보여주기 위한 설정
if 'df_data' not in st.session_state:
    # 빈 칸으로 채운 5줄짜리 데이터프레임 생성
    st.session_state.df_data = pd.DataFrame(columns=columns, index=range(5)).fillna("")

# 3. 데이터 입력창 (엑셀처럼 수정 가능)
edited_df = st.data_editor(
    st.session_state.df_data,
    num_rows="dynamic", # 행 추가/삭제 가능
    use_container_width=True,
    height=300
)

# 4. 표를 그림으로 그려주는 함수 (Matplotlib 활용)
def create_table_image(df):
    # 데이터 행 개수에 따라 이미지 높이 자동 조절
    rows, cols = df.shape
    fig_height = rows * 0.8 + 2  # 적절한 높이 계산
    
    # 캔버스 생성 (가로 22인치, 세로 자동)
    fig, ax = plt.subplots(figsize=(22, fig_height))
    
    # 그래프의 축(x축, y축)은 필요 없으니 숨김
    ax.axis('off')
    
    # 표 그리기
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc='center', # 셀 내용 가운데 정렬
        loc='center',
        # 컬럼별 너비 비율 (현장명과 조치사항을 넓게 설정)
        colWidths=[0.1, 0.05, 0.08, 0.25, 0.06, 0.08, 0.1, 0.08, 0.1, 0.1, 0.3] 
    )
    
    # 스타일 꾸미기
    table.auto_set_font_size(False)
    table.set_fontsize(13) # 글자 크기
    table.scale(1, 2.5)    # 셀 높이 늘리기 (시원시원하게)
    
    # 세부 디자인 (헤더 색상, 정렬 등)
    for (row, col), cell in table.get_celld().items():
        # 헤더(첫 줄) 디자인
        if row == 0: 
            cell.set_facecolor('#e6f2ff') # 연한 파란색 배경
            cell.set_text_props(weight='bold') # 굵은 글씨
            cell.set_height(0.15) # 헤더 높이 살짝 더 높게
        
        # '조치 사항'(마지막 열)은 내용이 기니까 왼쪽 정렬
        if col == 10 and row > 0: 
            cell.set_text_props(ha='left')
            # 글자가 너무 길면 줄바꿈이 안 되므로, 적당히 잘라주거나 패딩을 줌
            cell.set_edgecolor('black') # 테두리 색상
            
    # 표 위에 제목 추가
    plt.title("■ 금일 영하 12도 이하 현장 리스트", fontsize=25, weight='bold', loc='left', pad=20)
    
    return fig

# 5. 버튼 클릭 시 동작
if st.button("📸 보고용 이미지 생성", type="primary"):
    # 현장명이 비어있는 행은 제외하고 이미지를 만듦
    final_df = edited_df[edited_df['현장명'] != ""]
    
    if final_df.empty:
        st.warning("⚠️ 데이터를 먼저 입력해주세요!")
    else:
        with st.spinner('이미지를 예쁘게 그리는 중입니다...'):
            try:
                # 1) 이미지 생성 함수 호출
                fig = create_table_image(final_df)
                
                # 2) 파일로 저장
                output_filename = "daily_report_site.png"
                fig.savefig(output_filename, bbox_inches='tight', dpi=200, pad_inches=0.5)
                
                # 3) 화면에 보여주기
                st.success("이미지 변환 완료!")
                st.image(output_filename)
                
                # 4) 다운로드 버튼
                with open(output_filename, "rb") as file:
                    st.download_button(
                        label="📥 이미지 파일 다운로드",
                        data=file,
                        file_name=output_filename,
                        mime="image/png"
                    )
            except Exception as e:
                st.error(f"에러가 발생했습니다: {e}")
