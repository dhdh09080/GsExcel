import streamlit as st
import pandas as pd
import matplotlib
# 백엔드 설정 (반드시 pyplot import 전에)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import textwrap
import io
import urllib.request # 폰트 다운로드를 위해 추가

# 1. 페이지 설정
st.set_page_config(page_title="현장 보고서 생성기", layout="wide")

# -----------------------------------------------------------
# [폰트 설정] 폰트 파일을 직접 다운로드하여 적용 (OS 무관 해결책)
# -----------------------------------------------------------
def set_korean_font():
    font_file = "NanumGothic.ttf"
    # 구글 폰트(나눔고딕) 다운로드 URL
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"

    # 1. 폰트 파일이 없으면 다운로드
    if not os.path.exists(font_file):
        try:
            with st.spinner("한글 폰트 다운로드 중..."):
                urllib.request.urlretrieve(font_url, font_file)
        except Exception as e:
            st.error(f"폰트 다운로드 실패: {e}")
            return

    # 2. 다운받은 폰트를 Matplotlib에 등록 및 적용
    try:
        fm.fontManager.addfont(font_file)
        font_prop = fm.FontProperties(fname=font_file)
        font_name = font_prop.get_name()
        
        plt.rc('font', family=font_name)
        plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지
        
    except Exception as e:
        st.error(f"폰트 적용 중 오류: {e}")

# 폰트 설정 실행
set_korean_font()
# -----------------------------------------------------------

st.title("🏗️ 현장 보고용 이미지 생성기")
st.markdown("""
**[사용법]**
1. 엑셀 데이터를 복사(`Ctrl+C`)하여 아래 표에 붙여넣기(`Ctrl+V`)하세요.
2. **[📸 보고용 이미지 생성]** 버튼을 누르면 이미지와 **카톡용 요약 텍스트**가 생성됩니다.
""")

# 2. 초기 데이터
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

# 4. 이미지 생성 함수
def create_table_image(df):
    wrap_width = 18 
    formatted_data = []
    row_lines = []
    
    plot_df = df.copy()
    
    for idx, row in plot_df.iterrows():
        row_data = list(row.values)
        # 데이터가 비어있거나 숫자가 들어올 경우 대비 문자열 변환
        action_item = str(row_data[10]) if pd.notna(row_data[10]) else ""
        
        if action_item and action_item.strip() != "":
            wrapped_text = "\n".join(textwrap.wrap(action_item, width=wrap_width))
            row_data[10] = wrapped_text
            lines = wrapped_text.count('\n') + 1
        else:
            row_data[10] = ""
            lines = 1
            
        formatted_data.append(row_data)
        row_lines.append(lines)

    total_lines = sum(row_lines)
    if total_lines < 1: total_lines = 1
    
    fig_height = total_lines * 0.8 + 2
    
    # [안정성] figure 객체 직접 생성
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
            
    ax.set_title("■ 금일 영하 12도 이하 현장 리스트", fontsize=25, weight='bold', loc='center', pad=20)
    
    # 레이아웃 조정 시 오류 방지
    try:
        fig.tight_layout()
    except:
        pass
    
    return fig

# 5. 텍스트 요약
def generate_text_summary(df):
    count = len(df)
    site_names = ", ".join(df['현장명'].astype(str).tolist())

    summary = "[보고 한파(영하12도) 대상 현장]\n"
    summary += f"- 영하 12도 {count}개 현장이며,\n"
    summary += f"  : {site_names}\n\n"

    unique_actions = df['조치 사항'].astype(str).unique()
    
    # 빈 값 제거
    unique_actions = [x for x in unique_actions if x and str(x).strip() != 'nan' and str(x).strip() != '']

    if len(unique_actions) == 0:
        summary += "- 특이 조치 사항 없음"
    elif len(unique_actions) == 1:
        summary += f"- {unique_actions[0]}"
    else:
        summary += "- 주요 조치 사항:\n"
        for action in unique_actions:
            target_sites = df[df['조치 사항'] == action]['현장명'].tolist()
            sites_str = ",".join(target_sites)
            summary += f"  [{sites_str}] {action}\n"

    return summary

# 6. 실행 버튼
if st.button("📸 보고용 이미지 생성", type="primary"):
    final_df = edited_df[edited_df['현장명'] != ""]
    
    if final_df.empty:
        st.warning("⚠️ 데이터를 먼저 입력해주세요!")
    else:
        # 진행 상황을 시각적으로 보여줌
        status_text = st.empty()
        status_text.info("🚀 보고서 생성 시작...")
        
        try:
            # 1. 이미지 생성
            fig = create_table_image(final_df)
            
            # 메모리 버퍼 사용
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=200, pad_inches=0.5)
            plt.close(fig) # 메모리 해제
            img_buffer.seek(0)
            
            # 2. 텍스트 생성
            text_report = generate_text_summary(final_df)
            
            status_text.empty() # 상태 메시지 지우기
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.success("✅ 이미지 생성 완료")
                st.image(img_buffer)
                st.download_button("📥 이미지 다운로드", data=img_buffer, file_name="daily_report.png", mime="image/png")
            
            with col2:
                st.info("✅ 텍스트 요약")
                st.text_area("복사하기", value=text_report, height=200)
                
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
            plt.close('all')
