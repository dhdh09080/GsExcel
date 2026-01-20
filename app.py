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

# 4. 이미지 생성 함수 (수정)
def create_table_image(df):
    # [수정] 기존 18에서 40으로 변경 (칸을 넓게 씁니다)
    wrap_width = 30 
    
    formatted_data = []
    row_lines = []
    
    plot_df = df.copy()
    
    for idx, row in plot_df.iterrows():
        row_data = list(row.values)
        action_item = str(row_data[10]) if pd.notna(row_data[10]) else ""
        
        # 줄바꿈 처리 로직
        if action_item and action_item.strip() != "":
            # 여기서 설정한 너비(40자)에 맞춰서 줄을 나눕니다
            wrapped_text = "\n".join(textwrap.wrap(action_item, width=wrap_width))
            row_data[10] = wrapped_text
            lines = wrapped_text.count('\n') + 1
        else:
            row_data[10] = ""
            lines = 1
            
        formatted_data.append(row_data)
        row_lines.append(lines)

    # (이하 코드는 기존과 동일합니다)
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
        # 마지막 조치사항 열의 비율이 0.3(30%)이므로 40글자 정도가 적당합니다.
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
        
        # 조치사항(10번째 열)은 왼쪽 정렬
        if col == 10 and row > 0: 
            cell.set_text_props(ha='left')
            
    ax.set_title("■ 금일 영하 12도 이하 현장 리스트", fontsize=25, weight='bold', loc='center', pad=20)
    
    try:
        fig.tight_layout()
    except:
        pass
    
    return fig

# 4-1. [최종 수정] 노션 줄바꿈 "영혼까지 끌어모으기" 병합 함수
def merge_notion_rows(df):
    """
    현장명(필수값)이 없는 행은 '노션 줄바꿈'으로 간주합니다.
    이런 행에서 데이터가 '날짜' 열에 있든, '지역' 열에 있든 찾아내서
    바로 위쪽 '주인 행'의 [조치 사항]에 합쳐줍니다.
    """
    # 원본 보호를 위해 복사
    processed_df = df.copy()
    
    # 삭제할 행을 담을 리스트
    rows_to_drop = []
    
    # 마지막으로 발견한 '주인 있는 행' (현장명이 제대로 있는 줄)
    last_valid_idx = -1

    for i in range(len(processed_df)):
        # 1. 현장명 확인 (주인인지 아닌지 판별)
        site_raw = processed_df.iloc[i]['현장명']
        
        # 현장명이 비어있는지 체크 (None, NaN, 빈문자열)
        is_site_empty = False
        if pd.isna(site_raw) or str(site_raw).strip() == "" or str(site_raw).strip() == "nan":
            is_site_empty = True

        # 2. 로직 수행
        if not is_site_empty:
            # 현장명이 있으면 이 행이 새로운 '주인'입니다.
            last_valid_idx = i
            
        elif is_site_empty and last_valid_idx != -1:
            # 주인은 없는데 위에 부모 행이 있다면 -> "떨어져 나온 텍스트" 찾기
            
            # 해당 줄(row)의 모든 컬럼을 뒤져서 글자가 있는 내용을 찾습니다.
            # 보통 '날짜' 열(0번)에 들어가지만, 혹시 모르니 전체를 훑습니다.
            found_text_list = []
            for col_val in processed_df.iloc[i]:
                val_str = str(col_val).strip()
                if not pd.isna(col_val) and val_str != "" and val_str != "nan" and val_str != "None":
                    found_text_list.append(val_str)
            
            # 찾은 내용이 있다면 합치기
            if found_text_list:
                # 흩어진 텍스트를 하나로 뭉침
                fragment_text = " ".join(found_text_list)
                
                # 주인 행의 기존 조치사항 가져오기
                parent_col_idx = processed_df.columns.get_loc('조치 사항')
                parent_action = processed_df.iat[last_valid_idx, parent_col_idx]
                parent_text = str(parent_action).strip() if not pd.isna(parent_action) else ""
                
                # 내용 합치기 (줄바꿈 추가)
                if parent_text:
                    new_text = parent_text + "\n" + fragment_text
                else:
                    new_text = fragment_text
                
                # 주인 행에 업데이트
                processed_df.iat[last_valid_idx, parent_col_idx] = new_text
                
                # 내용 뺏긴 행은 삭제 목록에 추가
                rows_to_drop.append(i)

    # 3. 껍데기만 남은 행들 삭제 및 정리
    processed_df = processed_df.drop(processed_df.index[rows_to_drop]).reset_index(drop=True)
    
    return processed_df

# 5. 텍스트 요약 (업그레이드 버전)
def generate_text_summary(df):
    # ---------------------------------------------------------
    # 1. 데이터 전처리 (기온 숫자 변환)
    # ---------------------------------------------------------
    temp_df = df.copy()
    
    # '최저 기온'에서 숫자만 추출하는 함수
    def clean_temp(x):
        try:
            # 문자열로 변환 후 '도', 공백 제거
            clean_str = str(x).replace('도', '').replace('℃', '').strip()
            return float(clean_str)
        except:
            return 999 # 에러 시 큰 수로 처리하여 분류 제외

    temp_df['temp_val'] = temp_df['최저 기온'].apply(clean_temp)
    
    # 사업부 순서, 기온 낮은 순서로 정렬
    temp_df = temp_df.sort_values(by=['사업부', 'temp_val'])

    # ---------------------------------------------------------
    # 2. 보고서 헤더 작성
    # ---------------------------------------------------------
    total_count = len(temp_df)
    # 영하 15도 이하 개수 파악
    severe_cold_count = len(temp_df[temp_df['temp_val'] <= -15])
    
    summary = "📋 [한파(영하 12도) 관리 대상 현장 보고]\n"
    summary += f"■ 총 {total_count}개 현장 (영하 15도 이하: {severe_cold_count}개)\n\n"

    # ---------------------------------------------------------
    # 3. 사업부별 상세 내역
    # ---------------------------------------------------------
    # 사업부 목록 추출 (빈 값 제외)
    divisions = [d for d in temp_df['사업부'].unique() if str(d).strip() != '']
    
    for div in divisions:
        div_df = temp_df[temp_df['사업부'] == div]
        
        # 해당 사업부의 현장 리스트업 (이름 + 기온)
        site_info_list = []
        cnt_under_15 = 0
        
        for _, row in div_df.iterrows():
            site_name = str(row['현장명'])
            temp = row['최저 기온'] # 원본 텍스트 사용
            temp_val = row['temp_val']
            
            # 영하 15도 이하는 강조 표시 등을 할 수도 있음
            if temp_val <= -15:
                cnt_under_15 += 1
                site_info_list.append(f"{site_name}({temp}⚠️)")
            else:
                site_info_list.append(f"{site_name}({temp})")
        
        # 텍스트 조합
        sites_str = ", ".join(site_info_list)
        div_total = len(div_df)
        
        summary += f"[{div}] {div_total}개 현장"
        if cnt_under_15 > 0:
            summary += f" (🚨영하15도: {cnt_under_15}개)"
        summary += "\n"
        summary += f" : {sites_str}\n\n"

    # ---------------------------------------------------------
    # 4. 조치 사항 요약 (기존 로직 유지 + 보완)
    # ---------------------------------------------------------
    summary += "■ 주요 조치 사항\n"
    
    # 조치사항 빈 값 제거 및 문자열 변환
    unique_actions = temp_df['조치 사항'].astype(str).unique()
    valid_actions = [x for x in unique_actions if x and x.strip() != 'nan' and x.strip() != '']

    if len(valid_actions) == 0:
        summary += "- 특이 조치 사항 없음"
    else:
        for action in valid_actions:
            # 해당 조치를 한 현장들 찾기
            target_sites = temp_df[temp_df['조치 사항'] == action]['현장명'].astype(str).tolist()
            
            # 현장이 너무 많으면 'OO현장 외 N개'로 줄일 수도 있으나, 일단 다 표시
            sites_str = ",".join(target_sites)
            
            # 조치사항 내용이 너무 길면 첫 줄만 보여주거나 줄바꿈 정리
            clean_action = action.replace('\n', ' ')
            if len(clean_action) > 50:
                clean_action = clean_action[:50] + "..."
                
            summary += f"- {clean_action}\n"
            summary += f"  └ 대상: {sites_str}\n"

    return summary
# 6. 실행 버튼 (완전체 버전)
if st.button("📸 보고용 이미지 생성", type="primary"):
    
    # 1. 노션 줄바꿈 문제 해결 (흩어진 내용 합치기)
    merged_df = merge_notion_rows(edited_df)
    
    # 2. [수정됨] '모든 칸이 비어있는 행'만 삭제
    # (현장명을 깜빡했어도 다른 데이터가 있으면 살립니다)
    def is_row_completely_empty(row):
        # 행의 모든 값을 하나씩 꺼내서 문자로 만들고 공백을 제거한 뒤 합칩니다.
        # "nan", "None" 같은 시스템 문자도 걸러냅니다.
        all_text = "".join([str(x).strip().replace('nan', '').replace('None', '') for x in row])
        return len(all_text) == 0 # 합친 글자 길이가 0이면 진짜 빈 줄

    # 위 함수를 적용해서 데이터가 조금이라도 있는 행만 남깁니다.
    final_df = merged_df[~merged_df.apply(is_row_completely_empty, axis=1)]

    if final_df.empty:
        st.warning("⚠️ 입력된 데이터가 없습니다.")
    else:
        # 3. 사업부 기준으로 정렬 (끼리끼리 묶기)
        # 사업부가 비어있을 수도 있으니, 비어있으면 맨 뒤로 보내기 위해 fillna 처리 후 정렬
        final_df = final_df.sort_values(by='사업부', na_position='last').reset_index(drop=True)

        status_text = st.empty()
        status_text.info("🚀 보고서 생성 시작...")
        
        try:
            # 이미지 생성
            fig = create_table_image(final_df)
            
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=200, pad_inches=0.5)
            plt.close(fig)
            img_buffer.seek(0)
            
            # 텍스트 생성
            text_report = generate_text_summary(final_df)
            
            status_text.empty()
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.success("✅ 이미지 생성 완료")
                st.image(img_buffer)
                st.download_button("📥 이미지 다운로드", data=img_buffer, file_name="daily_report.png", mime="image/png")
            
            with col2:
                st.info("✅ 텍스트 요약")
                st.text_area("복사하기", value=text_report, height=600)
                
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
            plt.close('all')
