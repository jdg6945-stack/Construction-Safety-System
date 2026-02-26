import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import platform
from datetime import datetime

# 페이지 설정
st.set_page_config(layout="wide", page_title="시공단계 부력 검토")

# 스타일 설정 (이전 화면의 사용자 정의 스타일 복구)
st.markdown(
    """
    <style>
    div[data-baseweb="input"] { background-color: #f1f3f5 !important; border: none !important; }
    input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; margin: 0; 
    }
    input[type=number] { -moz-appearance: textfield; }
    .stNumberInput { margin-bottom: -15px !important; }
    .sub-title { 
        background-color: #4A5568; color: white; padding: 5px 12px; border-radius: 5px; 
        font-weight: bold; margin-top: 10px; margin-bottom: 5px; font-size: 14px; 
    }
    .section-title { 
        color: #2D3748; border-bottom: 2px solid #2D3748; padding-bottom: 5px; 
        margin-top: 50px; margin-bottom: 20px; font-weight: bold; font-size: 20px;
    }
    .result-container-ok { 
        background-color: #1976d2; color: white; padding: 12px; border-radius: 8px; 
        text-align: center; font-size: 20px; font-weight: bold; margin: 15px 0; 
    }
    .result-container-ng { 
        background-color: #d32f2f; color: white; padding: 12px; border-radius: 8px; 
        text-align: center; font-size: 20px; font-weight: bold; margin: 15px 0; 
    }
    /* 테이블 열 너비 최적화: 수식 공간 극대화 및 겹침 방지 */
    div[data-testid="stTable"] table { width: 100% !important; table-layout: fixed !important; border-collapse: collapse !important; border: 1px solid #ddd !important; }
    div[data-testid="stTable"] th, div[data-testid="stTable"] td { white-space: nowrap !important; padding: 8px 12px !important; font-size: 13px !important; border: 1px solid #eee !important; }
    div[data-testid="stTable"] th { background-color: #f8f9fa !important; color: #333 !important; }
    
    div[data-testid="stTable"] th:nth-child(1), div[data-testid="stTable"] td:nth-child(1) { display: none !important; }
    div[data-testid="stTable"] th:nth-child(2), div[data-testid="stTable"] td:nth-child(2) { width: 130px !important; background-color: #fdfdfd; }
    div[data-testid="stTable"] th:nth-child(3), div[data-testid="stTable"] td:nth-child(3) { width: auto !important; overflow: visible !important; }
    div[data-testid="stTable"] th:nth-child(4), div[data-testid="stTable"] td:nth-child(4) { width: 110px !important; text-align: right !important; font-weight: bold; }

    /* PDF 출력용 CSS (버튼 클릭 시에만 의미 있음) */
    @media print {
        @page { size: A4; margin: 10mm; }
        .no-print { display: none !important; }
        .print-only { display: block !important; }
        div[data-testid="stExpander"] { border: none !important; }
        div[data-testid="stExpander"] > div:first-child { display: none !important; }
    }
    .print-only { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# 1. 사이드바 설정
with st.sidebar:
    st.header("📍 검토 설정")
    num_floors = st.number_input("검토 층수(기초 제외)", min_value=1, max_value=10, value=2)
    st.divider()

    with st.expander("1. 기본 정보 (단위면적)", expanded=True):
        x_dist = st.number_input("X방향 길이 (mm)", value=8200)
        y_dist = st.number_input("Y방향 길이 (mm)", value=8200)
        area = (x_dist * y_dist) / 10**6

    with st.expander("2. 단면 정보 (층고 설정)", expanded=True):
        h_soil = st.number_input("흙 높이 (mm)", value=1200)
        floor_heights = []
        for i in range(num_floors):
            h = st.number_input(
                f"지하 {i+1}층 층고 (mm)", value=4050 if i == 0 else 5380, key=f"h_{i}"
            )
            floor_heights.append(h)

    with st.expander("3. 수위 및 단위중량", expanded=True):
        gl_minus = st.number_input("지하수위 (GL - m)", value=2.35)
        target_fs = st.number_input("목표 안전율", value=1.2)
        unit_c = st.number_input("콘크리트 단위중량 (kN/m³)", value=24.0)

# 이미지 함수
def overlay_text(img_path, measurements):
    try: img = Image.open(img_path).convert("RGB")
    except Exception: img = Image.new("RGB", (1000, 800), color=(220, 220, 220))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("malgunbd.ttf", 45) if platform.system() == "Windows" else ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 45)
    except Exception: font = ImageFont.load_default()
    for pos, val, is_vertical in measurements:
        text = f"{val:,}"; tw, th = draw.textbbox((0, 0), text, font=font)[2:4]; padding = 12; x, y = pos
        if is_vertical:
            txt_img = Image.new("RGBA", (tw + padding * 2, th + padding * 2), (255, 255, 255, 255))
            ImageDraw.Draw(txt_img).text((padding, padding), text, fill="black", font=font)
            rotated = txt_img.rotate(90, expand=True); img.paste(rotated, (x-rotated.width//2, y-rotated.height//2), rotated)
        else:
            draw.rectangle([x-tw//2-padding, y-th//2-padding, x+tw//2+padding, y+th//2+padding], fill="white", outline="#333333", width=2)
            draw.text((x, y), text, fill="black", font=font, anchor="mm")
    return img

st.title("️시공단계 부력 검토")

# 사용 안내 문구 추가
st.info("""
**📢 시공단계별 부력 검토 안내**
* 각 층의 **'시공 완료' 체크박스**를 활용하여 현재 공정을 설정해 주세요.
* '체크를 해제(OFF)'하면 해당 층은 아직 시공되지 않은 것으로 간주되어 '자중 계산에서 제외' 됩니다. 
* 실제 현장 상황에 맞춰 체크박스를 조정하여 부력 안전율을 확인하시기 바랍니다.
""")

c1, _, c2 = st.columns([10, 2, 10])
with c1:
    st.subheader("[평면 정보]")
    st.image(overlay_text("plan.png", [((550, 30), x_dist, False), ((30, 500), y_dist, True)]), width=300)
with c2:
    st.subheader("[층고 정보]")
    st.image(overlay_text("section.png", [((180, 100), h_soil, False)] + [((180, 310 if i == 0 else 580), fh, False) for i, fh in enumerate(floor_heights[:2])]), width=350)

# ---------------------------------------------------------
# 1. 설계하중 설정
# ---------------------------------------------------------
st.markdown("<h2 class='section-title'>1. 설계하중(고정하중) 설정</h2>", unsafe_allow_html=True)
ld_c1, ld_c2, ld_c3 = st.columns(3)
with ld_c1:
    with st.container(border=True):
        st.markdown("**지붕층 (Roof)**")
        t_topping = st.number_input("Topping 두께(mm)", value=1100, key="ld_t_top")
        t_plain_r = st.number_input("무근 Con'c 두께(mm)", value=100, key="ld_t_pr_r")
        t_slab_r = st.number_input("구조 슬래브 두께(mm)", value=250, key="ld_t_slab_r")
        l_cl_r = st.number_input("Ceiling 하중(kN/㎡)", value=0.3, key="ld_l_cl_r")
        roof_load = (18 * t_topping / 1000) + (23 * t_plain_r / 1000) + (unit_c * t_slab_r / 1000) + l_cl_r
        st.info(f"지붕층: {roof_load:.2f} kN/㎡")
with ld_c2:
    with st.container(border=True):
        st.markdown("**지하층 일반 (B1F)**")
        t_slab_mid = st.number_input("구조 슬래브 두께(mm)", value=150, key="ld_t_slab_mid")
        l_cl_f = st.number_input("Ceiling 하중(kN/㎡)", value=0.3, key="ld_l_cl_f")
        floor_load_mid = (unit_c * t_slab_mid / 1000) + l_cl_f
        st.info(f"일반층: {floor_load_mid:.2f} kN/㎡")
with ld_c3:
    with st.container(border=True):
        st.markdown("**최하층 (B2F/기초)**")
        t_plain_bot = st.number_input("무근 Con'c 두께(mm)", value=100, key="ld_t_plain_bot")
        t_slab_bot = st.number_input("구조 슬래브 두께(mm)", value=400, key="ld_t_slab_bot")
        floor_load_bot = (23 * t_plain_bot / 1000) + (unit_c * t_slab_bot / 1000)
        st.info(f"최하층: {floor_load_bot:.2f} kN/㎡")

# ---------------------------------------------------------
# 2. 부재정보 및 시공단계 설정
# ---------------------------------------------------------
st.markdown("<h2 class='section-title'>2. 부재정보 및 시공단계 설정</h2>", unsafe_allow_html=True)
st.markdown('<div class="sub-title">지붕층 (Roof)</div>', unsafe_allow_html=True)
is_roof_done = st.checkbox("지붕층 시공 완료", value=True, key="is_roof_done_chk")
bc1, bc2, bc3 = st.columns(3)
with bc1: 
    with st.container(border=True):
        st.markdown("**B1**"); bw_rb1 = st.number_input("폭", 500, key="brb1"); bh_rb1 = st.number_input("높이", 900, key="hrb1")
with bc2: 
    with st.container(border=True):
        st.markdown("**G1**"); bw_rg1 = st.number_input("폭", 500, key="brg1"); bh_rg1 = st.number_input("높이", 900, key="hrg1")
with bc3: 
    with st.container(border=True):
        st.markdown("**G2**"); bw_rg2 = st.number_input("폭", 700, key="brg2"); bh_rg2 = st.number_input("높이", 900, key="hrg2")

floor_inputs = []
for i in range(num_floors):
    st.markdown(f'<div class="sub-title">지하 {i+1}층 (B{i+1}F)</div>', unsafe_allow_html=True)
    is_f_done = st.checkbox(f"지하 {i+1}층 시공 완료", value=True, key=f"f_done_{i}")
    curr_tf, curr_fl, curr_tp, curr_lc = (t_slab_mid, floor_load_mid, 0, l_cl_f) if i < num_floors-1 else (t_slab_bot, floor_load_bot, t_plain_bot, 0)
    fc1, fc2 = st.columns([2.5, 0.7])
    with fc1:
        fbc1, fbc2, fbc3 = st.columns(3)
        with fbc1: 
            with st.container(border=True):
                st.markdown("**B1**"); bw_b1 = st.number_input("폭", 400, key=f"bb1_{i}"); bh_b1 = st.number_input("높이", 600, key=f"hb1_{i}")
        with fbc2:
            with st.container(border=True):
                st.markdown("**G1**"); bw_g1 = st.number_input("폭", 400, key=f"bg1_{i}"); bh_g1 = st.number_input("높이", 600, key=f"hg1_{i}")
        with fbc3:
            with st.container(border=True):
                st.markdown("**G2**"); bw_g2 = st.number_input("폭", 500, key=f"bg2_{i}"); bh_g2 = st.number_input("높이", 600, key=f"hg2_{i}")
    with fc2:
        with st.container(border=True):
            st.markdown("**기둥**"); bw_c = st.number_input("가로", 500, key=f"bc_{i}"); bh_c = st.number_input("세로", 700, key=f"hc_{i}")
    floor_inputs.append({"tf": curr_tf, "fl": curr_fl, "tp": curr_tp, "lc": curr_lc, "bw_b1": bw_b1, "bh_b1": bh_b1, "bw_g1": bw_g1, "bh_g1": bh_g1, "bw_g2": bw_g2, "bh_g2": bh_g2, "bw_c": bw_c, "bh_c": bh_c, "done": is_f_done})

st.markdown('<div class="sub-title">기초 (Footing)</div>', unsafe_allow_html=True)
ftc1, ftc2, ftc3 = st.columns(3)
fw = ftc1.number_input("기초 가로(mm)", 3000, key="ft_w"); flv = ftc2.number_input("기초 세로(mm)", 3000, key="ft_l"); fd = ftc3.number_input("기초 두께(mm)", 900, key="ft_d")

# ---------------------------------------------------------
# 계산 로직
# ---------------------------------------------------------
def get_step(w, h, t, l, m): return unit_c * (w/1000) * (h/1000 - t/1000) * l * m, f"{unit_c} x {w/1000} x ({h/1000} - {t/1000}) x {l} x {m}"

total_w = 0; roof_calc = []; floor_calcs = []
m_r = 1.0 if is_roof_done else 0.0
w_rs = roof_load * area * m_r
total_w += w_rs
roof_calc.append(["지붕층 슬래브", f"({18}*({t_topping/1000}) + {23}*({t_plain_r/1000}) + {unit_c}*({t_slab_r/1000}) + {l_cl_r}) x {area:.2f} x {m_r}", f"{w_rs:,.2f}"])
v1, e1 = get_step(bw_rb1, bh_rb1, t_slab_r, x_dist/1000, m_r); roof_calc.append(["지붕층 B1", e1, f"{v1:,.2f}"]); total_w += v1
v2, e2 = get_step(bw_rg1, bh_rg1, t_slab_r, y_dist/1000, m_r); roof_calc.append(["지붕층 G1", e2, f"{v2:,.2f}"]); total_w += v2
v3, e3 = get_step(bw_rg2, bh_rg2, t_slab_r, x_dist/1000, m_r); roof_calc.append(["지붕층 G2", e3, f"{v3:,.2f}"]); total_w += v3

for i, f in enumerate(floor_inputs):
    fh = floor_heights[i]/1000; m_f = 1.0 if f["done"] else 0.0; f_rows = []
    w_c = unit_c * (f["bw_c"]/1000) * (f["bh_c"]/1000) * fh * m_f
    f_rows.append([f"지하{i+1}층 기둥", f"{unit_c} x {f['bw_c']/1000} x {f['bh_c']/1000} x {fh} x {m_f}", f"{w_c:,.2f}"]); total_w += w_c
    if i == num_floors-1:
        fa = (fw*flv)/10**6; w_sn = f["fl"]*(area-fa)*m_f; w_ft = (f["fl"] + unit_c*(fd/1000 - f["tf"]/1000))*fa
        f_expr = f"({23}*({f['tp']/1000}) + {unit_c}*({f['tf']/1000}))"
        f_rows.append([f"지하{i+1}층 슬래브", f"{f_expr} x ({area:.2f}-{fa:.2f}) x {m_f}", f"{w_sn:,.2f}"])
        f_rows.append([f"지하{i+1}층 기초부", f"({f_expr} + {unit_c} x ({fd/1000}-{f['tf']/1000})) x {fa:.2f}", f"{w_ft:,.2f}"])
        total_w += (w_sn + w_ft)
    else:
        ws = f["fl"]*area*m_f; f_expr = f"({unit_c}*({f['tf']/1000}) + {f['lc']})"
        f_rows.append([f"지하{i+1}층 슬래브", f"{f_expr} x {area:.2f} x {m_f}", f"{ws:,.2f}"]); total_w += ws
        vb1, eb1 = get_step(f["bw_b1"], f["bh_b1"], f["tf"], x_dist/1000, m_f); f_rows.append([f"지하{i+1}층 B1", eb1, f"{vb1:,.2f}"]); total_w += vb1
        vg1, eg1 = get_step(f["bw_g1"], f["bh_g1"], f["tf"], y_dist/1000, m_f); f_rows.append([f"지하{i+1}층 G1", eg1, f"{vg1:,.2f}"]); total_w += vg1
        vg2, eg2 = get_step(f["bw_g2"], f["bh_g2"], f["tf"], x_dist/1000, m_f); f_rows.append([f"지하{i+1}층 G2", eg2, f"{vg2:,.2f}"]); total_w += vg2
    floor_calcs.append(f_rows)

ht = (h_soil+sum(floor_heights))/1000; wh = ht - gl_minus; fa = (fw*flv)/10**6
u1 = 10 * (wh + floor_inputs[-1]["tf"]/1000) * (area-fa); u2 = 10 * (wh + fd/1000) * fa
u_total = u1 + u2; fs_val = total_w / u_total if u_total > 0 else 0

# ---------------------------------------------------------
# 3. 검토 결과
# ---------------------------------------------------------
st.markdown("<h2 class='section-title'>3. 검토 결과</h2>", unsafe_allow_html=True)
res1, res2, res3 = st.columns(3)
res1.metric("총 하중 (ΣW)", f"{total_w:,.2f} kN")
res2.metric("총 부력 (ΣU)", f"{u_total:,.2f} kN")
res3.metric("안전율 (FS)", f"{fs_val:.4f}")

if fs_val >= target_fs:
    st.markdown(f"<div class='result-container-ok'>판정 : OK ({fs_val:.4f} ≥ {target_fs})</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='result-container-ng'>판정 : NG ({fs_val:.4f} < {target_fs})</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. 데이터 보기 및 PDF 출력용 섹션
# ---------------------------------------------------------
st.divider()
if st.button("📊 계산 근거 보기"):
    st.info("💡 이제 Ctrl + P를 눌러 PDF로 저장하세요.")
    
    st.markdown(f"""
        <div class="print-only">
            <h1>시공단계 부력 검토 상세 보고서</h1>
            <p>출력 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("🏠 지붕층(Roof) 상세 상세", expanded=True):
        st.table(pd.DataFrame(roof_calc, columns=["부재명", "상세 산식", "하중(kN)"]))
    for i, floor_data in enumerate(floor_calcs):
        with st.expander(f"🏢 지하 {i+1}층 상세 상세", expanded=True):
            st.table(pd.DataFrame(floor_data, columns=["부재명", "상세 산식", "하중(kN)"]))
    with st.expander("🌊 부력(U) 상세 상세", expanded=True):
        u_rows = [
            ["일반구간 부력 (U1)", f"10 x ({wh:.3f} + {floor_inputs[-1]['tf']/1000}) x ({area:.2f} - {fa:.2f})", f"{u1:,.2f}"],
            ["기초구간 부력 (U2)", f"10 x ({wh:.3f} + {fd/1000}) x {fa:.2f}", f"{u2:,.2f}"],
            ["총 부력 합계 (ΣU)", "U1 + U2", f"{u_total:,.2f}"]
        ]
        st.table(pd.DataFrame(u_rows, columns=["구분", "상세 산식", "결과(kN)"]))
