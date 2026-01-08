import streamlit as st
import pandas as pd
import dataframe_image as dfi

st.set_page_config(layout="wide")
st.title("📋 현장 보고서 이미지 생성기")

st.markdown("""
**[사용법]**
1. 노션에서 오늘 보고할 표 영역을 드래그해서 복사(`Ctrl+C`)하세요.
2. 아래 표의 **첫 번째 칸**을 클릭하고 붙여넣기(`Ctrl+V`)하세요.
3. 데이터가 들어간 게 확인되면 맨 아래 버튼을 누르세요.
""")

# 1. 빈 껍데기 표 만들기 (노션 컬럼 순서와 일치시켜야 함!)
# 보여주신 이미지 순서: 날짜 | 지역 | 사업부 | 현장명 | 최저기온 | ...
columns = [
    '날짜', '지역', '사업부', '현장명', '최저 기온', 
    '옥내작업', '작업 시작 시간(옥내)', 
    '옥외작업', '작업 시작 시간(옥외)', 
    '보온양생 작업 여부', '조치 사항'
]

# 초기에는 빈 데이터프레임 생성 (행 5개 정도 미리 만들어둠)
if 'df_data' not in st.session_state:
    # 빈 칸으로 채운 5줄짜리 데이터프레임
    st.session_state.df_data = pd.DataFrame(columns=columns, index=range(5)).fillna("")

# 2. 데이터 에디터 (여기에 복붙!)
edited_df = st.data_editor(
    st.session_state.df_data,
    num_rows="dynamic", # 행 추가/삭제 가능
    use_container_width=True,
    height=300
)

# 3. 이미지 변환 버튼
if st.button("📸 보고용 이미지 생성"):
    # 빈 행(데이터가 없는 줄)은 제거하고 이미지로 만들기
    # '현장명'이 비어있으면 데이터가 없는 것으로 간주
    final_df = edited_df[edited_df['현장명'] != ""]
    
    if final_df.empty:
        st.error("데이터를 입력해주세요!")
    else:
        with st.spinner('이미지 변환 중...'):
            # 스타일링 (제목 추가)
            styled_df = final_df.style.set_caption("■ 금일 영하 12도 이하 현장 리스트")\
                .set_table_styles([{
                    'selector': 'caption',
                    'props': [
                        ('color', 'black'), 
                        ('font-size', '20px'), 
                        ('font-weight', 'bold'),
                        ('text-align', 'left'),
                        ('padding', '10px')
                    ]
                }])
            
            output_filename = "site_report.png"
            dfi.export(styled_df, output_filename, max_cols=-1, max_rows=-1)
            
            st.image(output_filename)
            
            with open(output_filename, "rb") as file:
                st.download_button(
                    label="다운로드",
                    data=file,
                    file_name=output_filename,
                    mime="image/png"
                )
