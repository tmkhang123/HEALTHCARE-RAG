"""
HealthCare-RAG Deep Explainer — 1 file tổng hợp
Giải thích từng khái niệm bằng ngôn ngữ bình thường trước, rồi mới dùng thuật ngữ kỹ thuật.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Preformatted, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

FONT_DIR = "C:/Windows/Fonts/"
for name, f in [("DV","arial.ttf"),("DV-B","arialbd.ttf"),
                ("DV-I","ariali.ttf"),("DV-BI","arialbi.ttf"),
                ("DV-Mono","consola.ttf"),("DV-Mono-B","consolab.ttf")]:
    pdfmetrics.registerFont(TTFont(name, FONT_DIR+f))

C_NAV   = colors.HexColor("#1a3a5c")
C_BLUE  = colors.HexColor("#2563eb")
C_LBLUE = colors.HexColor("#dbeafe")
C_TEAL  = colors.HexColor("#0d9488")
C_LTEAL = colors.HexColor("#ccfbf1")
C_WARN  = colors.HexColor("#fef3c7")
C_WARNB = colors.HexColor("#d97706")
C_GRAY  = colors.HexColor("#64748b")
C_LGRAY = colors.HexColor("#f1f5f9")
C_DGRAY = colors.HexColor("#334155")
C_CODE  = colors.HexColor("#1e293b")
C_CODEFG= colors.HexColor("#e2e8f0")
C_TBH   = colors.HexColor("#1e40af")
C_WHITE = colors.white
C_GREEN = colors.HexColor("#166534")
C_LGREEN= colors.HexColor("#dcfce7")
C_RED   = colors.HexColor("#9f1239")

W = 15.5*cm

def S(h=6): return Spacer(1,h)
def HR(): return HRFlowable(width="100%",thickness=1,color=C_LBLUE,spaceAfter=5,spaceBefore=5)

def sty(name,**kw):
    defaults = dict(fontName="DV",fontSize=10,textColor=C_DGRAY,
                    spaceBefore=3,spaceAfter=3,leading=15.5)
    defaults.update(kw)
    return ParagraphStyle(name,**defaults)

ST = {
    "h1":    sty("h1",fontName="DV-B",fontSize=16,textColor=C_NAV,spaceBefore=22,spaceAfter=7,leading=22),
    "h2":    sty("h2",fontName="DV-B",fontSize=13,textColor=C_TEAL,spaceBefore=16,spaceAfter=5,leading=18),
    "h3":    sty("h3",fontName="DV-B",fontSize=11,textColor=C_DGRAY,spaceBefore=12,spaceAfter=4,leading=15),
    "body":  sty("body",alignment=TA_JUSTIFY),
    "plain": sty("plain",fontSize=10.5,leading=16.5,alignment=TA_JUSTIFY,
                 textColor=colors.HexColor("#1e293b")),
    "bullet":sty("bullet",leftIndent=16,firstLineIndent=-11,spaceBefore=2,spaceAfter=2,leading=15),
    "note":  sty("note",fontName="DV-I",fontSize=9.5,textColor=C_WARNB,leftIndent=10,
                 spaceBefore=3,spaceAfter=3,leading=14),
    "ct":    sty("ct",fontName="DV-B",fontSize=26,textColor=C_WHITE,alignment=TA_CENTER,leading=32),
    "cs":    sty("cs",fontName="DV-I",fontSize=12,textColor=colors.HexColor("#bfdbfe"),
                 alignment=TA_CENTER,leading=18),
}

def ic(t): return f'<font name="DV-Mono" size="8.5" color="#0369a1">{t}</font>'
def H1(t): return Paragraph(t, ST["h1"])
def H2(t): return Paragraph(t, ST["h2"])
def H3(t): return Paragraph(t, ST["h3"])
def P(t):  return Paragraph(t, ST["plain"])
def Pb(t): return Paragraph(t, ST["body"])
def B(t):  return Paragraph(f"•  {t}", ST["bullet"])
def Note(t): return Paragraph(f"⚠  {t}", ST["note"])

def Code(text, small=False):
    sz = 7.5 if small else 8.5
    inner = Preformatted(text, ParagraphStyle("cp",fontName="DV-Mono",
        fontSize=sz,textColor=C_CODEFG,leading=13))
    t = Table([[inner]],colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),C_CODE),
        ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
        ("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),9),
    ]))
    return t

def Box(text, bg=None, border=None, bold_label=None):
    """Hộp màu với viền trái dày."""
    if bg is None: bg = C_LBLUE
    if border is None: border = C_BLUE
    inner = []
    if bold_label:
        inner.append(Paragraph(f'<b>{bold_label}</b>', sty("bl",fontName="DV-B",
            fontSize=10,textColor=C_DGRAY,leading=14,spaceBefore=0,spaceAfter=4)))
    inner.append(Paragraph(text, sty("bx",fontName="DV",fontSize=10,
        textColor=C_DGRAY,leading=15,alignment=TA_JUSTIFY)))
    t = Table([inner],colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),bg),
        ("LINEAFTER",(0,0),(0,-1),3,border),
        ("LEFTPADDING",(0,0),(-1,-1),13),("RIGHTPADDING",(0,0),(-1,-1),13),
        ("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),9),
    ]))
    return t

def Warn(text, label="Lưu ý"):
    return Box(text, bg=C_WARN, border=C_WARNB, bold_label=label)

def Tip(text, label="Dễ nhớ"):
    return Box(text, bg=C_LTEAL, border=C_TEAL, bold_label=label)

def DefBox(text, label="Định nghĩa"):
    return Box(text, bg=colors.HexColor("#f0fdf4"), border=C_GREEN, bold_label=label)

def DTable(headers, rows, cws=None, header_bg=None):
    if header_bg is None: header_bg = C_TBH
    data = [[Paragraph(f'<b>{h}</b>', sty("th",fontName="DV-B",
        fontSize=9,textColor=C_WHITE,leading=12)) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), sty("td",fontName="DV",
            fontSize=9,textColor=C_DGRAY,leading=13)) for c in row])
    if cws is None: cws = [W/len(headers)]*len(headers)
    t = Table(data,colWidths=cws)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),header_bg),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[C_WHITE,C_LGRAY]),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#cbd5e1")),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    return t

def Banner(num, title, sub=""):
    inner = [
        Paragraph(f"PHẦN {num}", sty("pn",fontName="DV",fontSize=9,
            textColor=colors.HexColor("#93c5fd"),alignment=TA_CENTER,leading=13,
            spaceBefore=0,spaceAfter=5)),
        Paragraph(title, sty("bt",fontName="DV-B",fontSize=18,
            textColor=C_WHITE,alignment=TA_CENTER,leading=24,spaceBefore=0,spaceAfter=0)),
    ]
    if sub:
        inner.append(Paragraph(sub, ST["cs"]))
    t = Table([inner],colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),C_NAV),
        ("LEFTPADDING",(0,0),(-1,-1),20),("RIGHTPADDING",(0,0),(-1,-1),20),
        ("TOPPADDING",(0,0),(-1,-1),18),("BOTTOMPADDING",(0,0),(-1,-1),18),
    ]))
    return t

def QA(q, a):
    r = Table([[
        Paragraph(f'<b>H:</b> {q}',sty("qq",fontName="DV-B",fontSize=9.5,
            textColor=C_NAV,leading=13)),
        Paragraph(f'<b>Đ:</b> {a}',sty("aa",fontName="DV",fontSize=9.5,
            textColor=C_DGRAY,leading=13)),
    ]],colWidths=[6*cm,9.5*cm])
    r.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LINEBELOW",(0,0),(-1,-1),0.5,colors.HexColor("#e2e8f0")),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#eff6ff")),
    ]))
    return r

def make_doc(path):
    doc = BaseDocTemplate(path,pagesize=A4,
        leftMargin=2.5*cm,rightMargin=2*cm,topMargin=2.5*cm,bottomMargin=2.5*cm)
    h,w = A4[1],A4[0]
    def hf(canvas,doc):
        canvas.saveState()
        canvas.setFillColor(C_NAV); canvas.rect(0,h-1.7*cm,w,1.7*cm,fill=1,stroke=0)
        canvas.setFont("DV-B",9); canvas.setFillColor(C_WHITE)
        canvas.drawString(2.5*cm,h-1.1*cm,"HealthCare-RAG — Deep Explainer (Bản tổng hợp)")
        canvas.setFont("DV",8.5); canvas.setFillColor(colors.HexColor("#93c5fd"))
        canvas.drawRightString(w-2*cm,h-1.1*cm,"4 intent · Giải thích từ số 0")
        canvas.setFillColor(C_LGRAY); canvas.rect(0,0,w,1.4*cm,fill=1,stroke=0)
        canvas.setFont("DV",8); canvas.setFillColor(C_GRAY)
        canvas.drawString(2.5*cm,0.55*cm,"Dành cho người biết Python cơ bản · Mọi thuật ngữ đều được giải thích từ đầu")
        canvas.setFont("DV-B",9); canvas.setFillColor(C_NAV)
        canvas.drawRightString(w-2*cm,0.55*cm,f"Trang {doc.page}")
        canvas.restoreState()
    frame = Frame(2.5*cm,1.6*cm,W,h-4.3*cm,id="main")
    doc.addPageTemplates([PageTemplate(id="main",frames=[frame],onPage=hf)])
    return doc

# ══════════════════════════════════════════════════════════════════════════════
def build():
    e = []

    # COVER
    cover_content = [
        S(16),
        Paragraph("HealthCare-RAG", ST["ct"]),
        S(8),
        Paragraph("Bản Giải Thích Toàn Diện", ST["cs"]),
        S(6),
        Paragraph("Dành cho người biết Python cơ bản", sty("cd",fontName="DV",fontSize=11,
            textColor=colors.HexColor("#93c5fd"),alignment=TA_CENTER,leading=16)),
        S(20),
        Paragraph("Mọi khái niệm đều được giải thích bằng ngôn ngữ bình thường trước khi dùng thuật ngữ kỹ thuật.",
            sty("ci",fontName="DV-I",fontSize=10,textColor=colors.HexColor("#bfdbfe"),
                alignment=TA_CENTER,leading=16)),
        S(16),
    ]
    cv = Table([cover_content],colWidths=[W])
    cv.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),C_NAV),
        ("LEFTPADDING",(0,0),(-1,-1),20),("RIGHTPADDING",(0,0),(-1,-1),20),
        ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    e.append(cv); e.append(S(14))

    # MỤC LỤC
    e.append(H2("Mục lục"))
    e.append(DTable(["Phần","Chủ đề"],
        [["1","Hệ thống làm gì? Bức tranh toàn cảnh"],
         ["2","Nền tảng: model, token, loss, training vs inference"],
         ["3","BERT và BioBERT — bộ đọc hiểu ngôn ngữ"],
         ["4","NER — tìm thực thể: BIO tagging, CRF, Viterbi"],
         ["5","Intent Classifier — dataset, training, 99.36%"],
         ["6","Tìm kiếm tài liệu — TF-IDF, BM25, Dense, RRF, Reranker"],
         ["7","Đánh giá — MRR@10, F1, Accuracy: từng số có nghĩa gì"],
         ["8","Flow code đầy đủ — từ câu hỏi đến câu trả lời"],
         ["9","Câu hỏi phản biện và những câu không nên nói"]],
        cws=[1.5*cm,14*cm]))
    e.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 1 — BỨC TRANH TOÀN CẢNH
    # ══════════════════════════════════════════════════════════════════════════
    e.append(Banner("1","Bức tranh toàn cảnh","Hệ thống làm gì · 4 loại câu hỏi · Tại sao cần RAG"))
    e.append(S(12))

    e.append(H2("Hệ thống này là gì?"))
    e.append(P("Đây là chatbot tiếng Anh về dinh dưỡng và sức khỏe. "
               "Người dùng gõ câu hỏi, hệ thống trả lời kèm nguồn trích dẫn."))
    e.append(P("Điểm đặc biệt: hệ thống không chỉ hỏi AI một câu rồi lấy câu trả lời luôn. "
               "Nó phân loại câu hỏi trước, tìm đúng nguồn dữ liệu, rồi mới sinh câu trả lời. "
               "Lý do sẽ rõ ở phần tiếp theo."))

    e.append(H2("Tại sao không hỏi thẳng AI (Llama)?"))
    e.append(P("Thử gõ vào ChatGPT: \"100g gà ức có bao nhiêu protein?\" "
               "Nó sẽ trả lời ngay — nhưng con số đó lấy từ đâu? "
               "AI học từ hàng tỉ trang văn bản trên internet, "
               "trong đó có nhiều nguồn mâu thuẫn nhau. "
               "Nó có thể tự tin đưa ra con số 27g trong khi USDA ghi 31g."))
    e.append(P("Trong y tế và dinh dưỡng, sai một con số có thể gây hại. "
               "Vì vậy đồ án không để AI tự nhớ số, mà bắt nó tra database rồi mới trả lời."))
    e.append(Tip(
        "Hình dung AI như một sinh viên giỏi nhưng hay 'bịa' số. "
        "Giải pháp: trước khi trả lời, bắt nó mở sách giáo khoa (USDA database hoặc bài báo khoa học) ra đọc, "
        "rồi mới được phép nói. Đó là tinh thần của RAG.",
        label="Hình dung dễ hiểu"))

    e.append(H2("RAG là gì?"))
    e.append(P("RAG là viết tắt của Retrieval-Augmented Generation — "
               "tạm dịch là 'sinh câu trả lời có hỗ trợ của tra cứu'. "
               "Ba bước:"))
    e.append(B("<b>Retrieval (Tra cứu):</b> Tìm tài liệu liên quan đến câu hỏi trong kho dữ liệu."))
    e.append(B("<b>Augmentation (Bổ sung):</b> Chèn tài liệu tìm được vào 'đề bài' cho AI như ngữ cảnh."))
    e.append(B("<b>Generation (Sinh câu trả lời):</b> AI đọc câu hỏi cộng tài liệu, rồi viết câu trả lời."))
    e.append(S(4))
    e.append(Code(
        "KHÔNG phải:\n"
        "  Câu hỏi  ->  AI tự nhớ  ->  Trả lời\n\n"
        "MÀ LÀ:\n"
        "  Câu hỏi  ->  Tìm tài liệu liên quan\n"
        "           ->  AI đọc tài liệu + câu hỏi\n"
        "           ->  Trả lời dựa trên tài liệu (kèm nguồn)"))
    e.append(Note("RAG không sửa trọng số của AI. Nó chỉ cung cấp tài liệu ngay tại thời điểm hỏi, "
                  "như đưa tài liệu vào tay AI trước khi nó viết bài."))

    e.append(H2("Bốn loại câu hỏi — trái tim của hệ thống"))
    e.append(P("Hệ thống phân loại mỗi câu hỏi vào một trong bốn nhóm. "
               "Tùy nhóm, nó xử lý hoàn toàn khác nhau:"))
    e.append(DTable(
        ["Nhóm (Intent)","Ý nghĩa","Nguồn dữ liệu","Có dùng AI?"],
        [["NUTRITION_LOOKUP","Hỏi con số dinh dưỡng","USDA SQLite database","Không (nếu tìm được đúng món)"],
         ["HEALTH_ADVICE","Hỏi tác dụng, bệnh, lời khuyên","Bài báo y sinh (NFCorpus)","Có"],
         ["BOTH","Vừa cần số vừa cần lời khuyên","USDA + bài báo","Có"],
         ["NONE","Câu hỏi ngoài chủ đề (toán, code...)","Không cần","Không — từ chối ngay"]],
        cws=[4*cm,4*cm,4*cm,3.5*cm]))
    e.append(S(6))
    e.append(Code(
        '"How many calories are in apple?"       ->  NUTRITION_LOOKUP\n'
        '"Is salmon good for heart health?"      ->  HEALTH_ADVICE\n'
        '"How much protein in salmon, and is\n'
        ' it good for heart?"                    ->  BOTH\n'
        '"What is the result of 1+1?"            ->  NONE'))
    e.append(S(4))
    e.append(Warn(
        'Bẫy thường gặp: "Can ginger help nausea during pregnancy?" '
        'Câu này có tên thức ăn (ginger) và tình trạng sức khỏe (nausea) '
        'nhưng KHÔNG hỏi số dinh dưỡng cụ thể từ USDA. '
        'Đúng phải là HEALTH_ADVICE, không phải BOTH. '
        'BOTH yêu cầu đồng thời: số dinh dưỡng chính xác VÀ phân tích sức khỏe.',
        label="Bẫy dễ nhầm"))

    e.append(H2("Kiến trúc tổng thể"))
    e.append(Code(
        "Browser  ->  Spring Boot (cổng 8081)  ->  FastAPI RAG server (cổng 8000)\n\n"
        "Spring Boot: lo phần web — đăng nhập, lưu lịch sử chat, chuyển tin nhắn sang Python\n"
        "FastAPI    : lo phần AI/NLP — phân loại câu hỏi, tìm tài liệu, sinh câu trả lời\n\n"
        "Trong FastAPI, mọi thứ đi qua ENPipeline.answer() trong src/en/pipeline.py:\n"
        "  1. NER tìm food/disease/nutrient trong câu\n"
        "  2. Ghép entity từ lịch sử hội thoại nếu câu hiện tại thiếu\n"
        "  3. Intent classifier chọn 1 trong 4 nhóm\n"
        "  4a. Tra USDA SQLite (nếu cần số)\n"
        "  4b. Hybrid retrieval + reranker (nếu cần lời khuyên)\n"
        "  5. Fast-path hoặc Llama sinh câu trả lời"))
    e.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 2 — NỀN TẢNG
    # ══════════════════════════════════════════════════════════════════════════
    e.append(Banner("2","Nền tảng: Model, Token, Loss, Training",
        "Những khái niệm bạn sẽ gặp xuyên suốt — giải thích từ đầu"))
    e.append(S(12))

    e.append(H2("Model là gì?"))
    e.append(P("Một model là một hàm toán học với rất nhiều tham số số học bên trong — "
               "thường là hàng triệu hoặc hàng tỉ con số. "
               "Nó nhận input (câu hỏi) và trả output (nhãn, vector số, v.v.)."))
    e.append(P("Hình dung đơn giản bằng Python:"))
    e.append(Code(
        "def classify_intent(sentence, weights):  # weights = hàng triệu số\n"
        "    # Tính toán ma trận phức tạp dựa trên weights...\n"
        "    return 'NUTRITION_LOOKUP'  # hoặc HEALTH_ADVICE, BOTH, NONE\n\n"
        "# Câu hỏi: làm sao tìm được bộ weights tốt?\n"
        "# Câu trả lời: TRAINING — cho máy xem nhiều ví dụ có nhãn đúng\n"
        "#              và tự điều chỉnh weights để dự đoán ngày càng chính xác"))

    e.append(H2("Checkpoint là gì?"))
    e.append(P("Sau khi training xong, toàn bộ weights được lưu vào một thư mục. "
               "Thư mục đó gọi là checkpoint — hình dung như file 'save game'. "
               "Lần sau muốn dùng model, chỉ cần load checkpoint lên, "
               "không cần train lại từ đầu."))
    e.append(Code(
        "# Project có 2 checkpoint chính:\n"
        "models/classifier_bert/   <- weights của Intent Classifier\n"
        "models/ner_bert/           <- weights của NER model"))

    e.append(H2("Training vs Inference — hai thế giới khác nhau"))
    e.append(DTable(["","Training (huấn luyện)","Inference (suy luận)"],
        [["Khi nào?","Làm một lần trong notebook, trước khi demo","Mỗi lần người dùng gửi câu hỏi"],
         ["Có nhãn đúng không?","Có — dùng để tính sai số","Không — chỉ nhận input, trả output"],
         ["Weights thay đổi không?","Có — được cập nhật liên tục","Không — cố định hoàn toàn"],
         ["Mất bao lâu?","Hàng giờ hoặc hàng ngày","Vài giây hoặc vài phút"]],
        cws=[4*cm,5.75*cm,5.75*cm]))
    e.append(S(4))
    e.append(Warn("BERT có train lại mỗi lần người dùng chat không? → KHÔNG. "
                  "Runtime chỉ inference — chỉ chạy model để lấy kết quả. "
                  "Weights cố định từ lúc checkpoint được lưu.",
                  label="Câu hỏi hay gặp"))

    e.append(H2("Token và Tokenizer — cách model 'đọc' chữ"))
    e.append(P("Model không đọc chữ như người. Trước tiên Tokenizer tách câu thành "
               "các mảnh nhỏ gọi là token, rồi đổi mỗi token thành một số nguyên:"))
    e.append(Code(
        '"chicken breast" -> ["chicken", "breast"] -> [7975, 7388]\n\n'
        '# BERT còn tách từ thành mảnh nhỏ hơn (subword):\n'
        '"glycemic" -> ["glyc", "##emic"] -> [3255, 3032]\n'
        "# ## nghĩa là mảnh này nối tiếp từ trước, không phải từ mới\n\n"
        "# Vì sao subword?\n"
        "# -> Từ 'glycemic' chưa xuất hiện trong từ điển, nhưng 'glyc' và '##emic' thì có\n"
        "# -> Giúp model xử lý từ lạ mà không cần từ điển vô hạn"))
    e.append(Note("NER dùng BioBERT cũng tách subword tương tự. Vì vậy cần bước căn chỉnh nhãn: "
                  "gán nhãn gốc cho subword đầu, subword sau thành I-*."))

    e.append(H2("Loss — đo mức độ sai"))
    e.append(P("Loss là một con số duy nhất cho biết dự đoán của model lệch nhãn đúng bao nhiêu. "
               "Khi loss = 0: model dự đoán hoàn hảo. "
               "Mục tiêu của training là làm loss giảm xuống qua nhiều vòng lặp."))
    e.append(P("Với bài toán phân loại 4 intent, loss được tính bằng "
               "<b>Cross-Entropy Loss</b>. Tên nghe phức tạp nhưng ý tưởng đơn giản:"))
    e.append(Code(
        "# Giả sử câu đúng là NUTRITION_LOOKUP (class 0)\n"
        "# Model vừa dự đoán xác suất cho 4 class:\n"
        "#   NUTRITION  HEALTH  BOTH   NONE\n"
        "#   [  0.95,   0.03,  0.01,  0.01  ]\n\n"
        "# Model rất tự tin -> P(đúng) = 0.95 -> loss = -log(0.95) = 0.05\n"
        "# Loss nhỏ = tốt!\n\n"
        "#   [  0.35,   0.40,  0.15,  0.10  ]\n"
        "# Model lẫn sang HEALTH -> P(đúng) = 0.35 -> loss = -log(0.35) = 1.05\n"
        "# Loss lớn = tệ -> model bị phạt mạnh\n\n"
        "# Công thức gần đúng: loss = -log( P(class đúng) )"))
    e.append(Tip("Cách nhớ: log của số gần 1 rất gần 0 (loss nhỏ). "
                 "log của số gần 0 rất âm lớn (loss lớn). "
                 "Dấu trừ ở trước làm loss luôn dương.",
                 label="Cách nhớ Cross-Entropy"))

    e.append(H2("Backpropagation và Optimizer — cách weights được cập nhật"))
    e.append(P("Sau khi tính được loss, model cần biết mỗi weight nên tăng hay giảm "
               "để loss giảm ở bước sau. "
               "Backpropagation làm điều này: nó tính gradient — "
               "một con số cho mỗi weight, cho biết 'tăng weight này lên một chút thì loss thay đổi thế nào'."))
    e.append(Code(
        "for batch in dataloader:\n"
        "    outputs = model(**batch)\n"
        "    loss = outputs.loss          # tính sai bao nhiêu\n\n"
        "    loss.backward()              # tính gradient cho mọi weight\n"
        "                                 # (backpropagation)\n\n"
        "    optimizer.step()             # cập nhật weights dựa trên gradient\n"
        "                                 # (AdamW: tự điều chỉnh bước nhảy)\n\n"
        "    optimizer.zero_grad()        # XÓA gradient cũ\n"
        "                                 # (PyTorch cộng dồn gradient nếu không xóa\n"
        "                                 #  -> lần sau sẽ tính sai)"))
    e.append(P("<b>AdamW</b> là optimizer (bộ cập nhật weights). "
               "Adam = tự điều chỉnh learning rate cho từng weight dựa trên lịch sử gradient. "
               "W = Weight decay: phạt nhẹ các weight lớn để tránh overfitting."))

    e.append(H2("Epoch, Batch, Learning Rate"))
    e.append(B("<b>Epoch:</b> Một vòng đi qua toàn bộ tập training. "
               "Project train 3 epoch = model thấy toàn bộ 1.792 câu 3 lần."))
    e.append(B("<b>Batch size = 16:</b> Thay vì cập nhật weights sau mỗi câu (không ổn định) "
               "hoặc sau khi xem hết tất cả câu (tốn bộ nhớ), "
               "lấy 16 câu làm một nhóm, tính loss trung bình nhóm, rồi mới cập nhật."))
    e.append(B("<b>Learning rate = 2e-5:</b> Mỗi lần cập nhật, weights nhảy bao xa? "
               "2e-5 = 0.00002 — rất nhỏ, vì đây là fine-tune: "
               "BERT đã được huấn luyện trước rồi, chỉ cần tinh chỉnh nhẹ. "
               "Nhảy quá mạnh sẽ 'phá vỡ' những gì BERT đã học."))
    e.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 3 — BERT VÀ BIOBERT
    # ══════════════════════════════════════════════════════════════════════════
    e.append(Banner("3","BERT và BioBERT","Bộ đọc hiểu ngôn ngữ — giải thích từ đầu"))
    e.append(S(12))

    e.append(H2("Vấn đề với cách đọc truyền thống"))
    e.append(P("Trước BERT, nhiều model đọc câu từ trái qua phải như người đọc sách. "
               "Vấn đề: từ 'bank' trong 'river bank' (bờ sông) và 'bank account' (tài khoản ngân hàng) "
               "sẽ được hiểu giống nhau dù nghĩa hoàn toàn khác."))
    e.append(P("BERT giải quyết bằng cách nhìn toàn bộ câu cùng lúc — "
               "cả token bên trái lẫn bên phải — "
               "nên nó 'hiểu ngữ cảnh'. "
               "BERT là viết tắt của Bidirectional Encoder Representations from Transformers."))

    e.append(H2("Token [CLS] — đại diện cho cả câu"))
    e.append(P("BERT thêm một token đặc biệt " + ic("[CLS]") + " vào đầu mỗi câu trước khi xử lý. "
               "Sau khi đi qua 12 tầng Transformer, token này đã 'nhìn' và hấp thụ "
               "thông tin từ mọi token khác trong câu. "
               "Vector số của " + ic("[CLS]") + " cuối cùng trở thành bản tóm tắt toàn bộ câu."))
    e.append(P("Đây là lý do Intent Classifier dùng vector [CLS] để phân loại câu:"))
    e.append(Code(
        "Câu: 'How many calories are in apple?'\n\n"
        "BERT nhận:  [CLS] How many calories are in apple ? [SEP]\n"
        "                ↑\n"
        "        token đặc biệt thêm vào\n\n"
        "Sau 12 tầng Transformer:\n"
        "  vector của [CLS] = [0.12, -0.08, 0.31, ..., -0.45]  # 768 số\n"
        "  vector này đại diện cho nghĩa cả câu\n\n"
        "Tiếp theo:\n"
        "  logits = Linear(768, 4)( vector_CLS )\n"
        "         = [4.8, -1.2, 0.7, -3.1]  # điểm cho 4 intent\n"
        "  intent = argmax(logits) = NUTRITION_LOOKUP (index 0)"))

    e.append(H2("BERT 'bert-base-uncased' — thông số cụ thể"))
    e.append(DTable(["Thông số","Giá trị","Ý nghĩa"],
        [["Số tầng Transformer","12","Mỗi tầng tinh chỉnh thêm hiểu biết về ngữ cảnh"],
         ["Kích thước hidden","768","Mỗi token được biểu diễn bằng 768 số sau khi qua BERT"],
         ["Số attention heads","12","12 'góc nhìn' khác nhau về quan hệ giữa các token"],
         ["Uncased","Không phân biệt hoa/thường","'Apple' và 'apple' được xử lý như nhau"],
         ["Max length","512 token","Câu dài hơn sẽ bị cắt; project dùng 128 vì query ngắn"]],
        cws=[4*cm,3.5*cm,8*cm]))

    e.append(H2("BioBERT — BERT 'học chuyên y sinh'"))
    e.append(P("BioBERT bắt đầu từ BERT thông thường, "
               "sau đó được tiếp tục train thêm trên hàng triệu bài báo y sinh từ PubMed và PMC. "
               "Kết quả: nó quen thuộc với các từ chuyên ngành như glycemic, HbA1c, "
               "cardiovascular, polyphenol, lipid — những từ hiếm gặp trong văn bản thông thường."))
    e.append(P("Project dùng BioBERT cho NER (nhận diện thực thể) vì đây là domain y tế. "
               "BERT thường có thể không nhận ra 'HbA1c' là một chỉ số xét nghiệm, "
               "nhưng BioBERT thì có."))
    e.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 4 — NER
    # ══════════════════════════════════════════════════════════════════════════
    e.append(Banner("4","NER — Nhận diện thực thể",
        "BIO tagging · CRF · Viterbi — từng khái niệm giải thích từ gốc"))
    e.append(S(12))

    e.append(H2("NER là gì và khác Intent thế nào?"))
    e.append(P("Intent Classifier hỏi: 'Cả câu này thuộc loại nào?' — trả về 1 nhãn cho cả câu."))
    e.append(P("NER (Named Entity Recognition) hỏi khác: 'Từng từ trong câu là gì?' — "
               "trả về 1 nhãn cho mỗi từ."))
    e.append(Code(
        'Câu: "How much protein is in salmon?"\n\n'
        "Intent (1 nhãn cho cả câu):     NUTRITION_LOOKUP\n\n"
        "NER    (nhãn từng từ):   How    much  protein     is   in   salmon\n"
        "                          O      O    B-NUTRIENT   O    O   B-FOOD\n\n"
        "# NER lấy ra: FOOD = ['salmon'], NUTRIENT = ['protein']"))
    e.append(P("Tại sao cần NER? Vì Intent classifier chỉ biết cần tra USDA, "
               "nhưng không biết tra <i>món nào</i>. NER mới cho biết cụ thể là 'salmon'."))

    e.append(H2("BIO tagging — quy ước gán nhãn"))
    e.append(P("Khi một thực thể gồm nhiều từ (ví dụ 'chicken breast' = 2 từ), "
               "cần cách để nói 'hai từ này cùng là một thực thể'. "
               "BIO tagging giải quyết điều này:"))
    e.append(B(ic("B-X") + " (Begin): Token này <b>bắt đầu</b> một thực thể loại X"))
    e.append(B(ic("I-X") + " (Inside): Token này <b>nằm trong</b> thực thể X, nối tiếp B"))
    e.append(B(ic("O") + " (Outside): Token này <b>không</b> thuộc thực thể nào"))
    e.append(S(4))
    e.append(Code(
        '"A diabetic patient should avoid sugar cane juice"\n\n'
        " A    diabetic  patient  should  avoid  sugar   cane   juice\n"
        " O    B-DISEASE    O       O       O    B-FOOD  I-FOOD  I-FOOD\n\n"
        "# 'diabetic' = 1 entity DISEASE (B vì bắt đầu)\n"
        "# 'sugar cane juice' = 1 entity FOOD gồm 3 token: B, I, I"))
    e.append(P("Project nhận diện 3 loại thực thể: FOOD, DISEASE, NUTRIENT. "
               "(SYMPTOM là trường dự phòng trong API, model NER không train nhãn này.)"))

    e.append(H2("Vấn đề khi gán nhãn từng token riêng lẻ"))
    e.append(P("Nếu gán nhãn mỗi token độc lập — không quan tâm token trước là gì — "
               "model có thể tạo ra chuỗi vô lý:"))
    e.append(Code(
        '"sugar  cane  juice"\n'
        " B-FOOD B-FOOD I-FOOD  <- SAI: hai B liên tiếp không hợp lệ\n\n"
        " O      I-FOOD B-FOOD  <- SAI: I-FOOD xuất hiện không có B-FOOD trước\n\n"
        " B-FOOD I-DISEASE I-FOOD  <- SAI: entity 'nhảy' loại giữa chừng"))
    e.append(P("Những lỗi này không xảy ra ở người vì chúng ta hiểu ngữ pháp. "
               "Nhưng model gán nhãn độc lập không có ràng buộc đó."))

    e.append(H2("CRF — học quan hệ giữa các nhãn liền kề"))
    e.append(P("CRF (Conditional Random Field) là một lớp toán học thêm vào sau BioBERT. "
               "Thay vì gán nhãn từng token riêng lẻ, CRF xét cả chuỗi nhãn và hỏi: "
               "'Chuỗi nhãn nào hợp lý nhất toàn cục?'"))
    e.append(P("CRF học hai loại điểm:"))
    e.append(B("<b>Emission score:</b> Token này hợp với nhãn nào? "
               "(ví dụ: 'protein' rất hợp với B-NUTRIENT)"))
    e.append(B("<b>Transition score:</b> Nhãn này có hợp lý sau nhãn kia không? "
               "(ví dụ: B-FOOD → I-FOOD rất hợp lý; B-FOOD → I-DISEASE rất ít hợp lý)"))
    e.append(S(4))
    e.append(Code(
        "# CRF học các transition score kiểu này:\n"
        "B-FOOD  -> I-FOOD     : xác suất CAO  (hợp lý)\n"
        "B-FOOD  -> B-FOOD     : xác suất THẤP (ít khi hợp lý)\n"
        "O       -> I-FOOD     : xác suất RẤT THẤP (I không thể không có B trước)\n"
        "B-DISEASE -> I-DISEASE: xác suất CAO (hợp lý)\n"
        "B-DISEASE -> I-FOOD   : xác suất THẤP (nhảy loại)"))

    e.append(H2("Viterbi — tìm chuỗi nhãn tốt nhất"))
    e.append(P("Bây giờ có emission score (từ BioBERT) và transition score (từ CRF). "
               "Muốn tìm chuỗi nhãn có tổng điểm cao nhất. "
               "Nhưng không thể thử mọi tổ hợp:"))
    e.append(Code(
        "# Với 7 nhãn và câu 15 token:\n"
        "# Số tổ hợp = 7^15 = 4,7 tỉ tổ hợp  <- quá nhiều!\n\n"
        "# Viterbi giải quyết bằng dynamic programming:\n"
        "# Tại mỗi token, chỉ cần nhớ:\n"
        "#   'điểm tốt nhất có thể đạt được khi kết thúc ở nhãn X là bao nhiêu?'\n"
        "# Không cần nhớ toàn bộ đường đi trước đó\n\n"
        "# Độ phức tạp: O(T × K²) với T = số token, K = số nhãn\n"
        "# Ví dụ: 15 token × 7² = 15 × 49 = 735 phép tính  <- dễ dàng!"))
    e.append(Tip(
        "Viterbi giống như bài toán tìm đường đi ngắn nhất trong bản đồ nhiều cột. "
        "Thay vì thử mọi đường, ở mỗi cột chỉ lưu lại đường tốt nhất đến mỗi điểm. "
        "Đây là kỹ thuật dynamic programming.",
        label="Hình dung Viterbi"))

    e.append(H2("Kết quả NER — hiểu đúng con số"))
    e.append(DTable(["Entity","Precision","Recall","F1"],
        [["FOOD","0.98","0.98","0.9868"],
         ["NUTRIENT","0.96","0.97","0.9674"],
         ["DISEASE","0.92","0.92","0.9206"],
         ["Overall","0.95","0.96","0.9565"]],
        cws=[3.5*cm,3.5*cm,3.5*cm,5*cm]))
    e.append(S(4))
    e.append(P("<b>Đánh giá bằng seqeval:</b> Chấm entity span hoàn chỉnh — "
               "nếu đúng là 'chicken breast' (2 token) nhưng chỉ đoán 'chicken' (1 token) "
               "thì entity đó <b>sai</b>, không được điểm. "
               "Nghiêm ngặt hơn chấm từng token riêng lẻ."))
    e.append(Warn(
        "Argmax (0.9569) hơi cao hơn CRF Viterbi (0.9565) trong ablation. "
        "Điều này không có nghĩa CRF là vô dụng — "
        "nó vẫn đảm bảo chuỗi nhãn có cấu trúc hợp lý hơn. "
        "Nhưng không nên nói 'CRF chắc chắn cải thiện F1'.",
        label="Lưu ý ablation"))
    e.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 5 — INTENT CLASSIFIER
    # ══════════════════════════════════════════════════════════════════════════
    e.append(Banner("5","Intent Classifier","Dataset · Training · 99.36% — đọc đúng con số"))
    e.append(S(12))

    e.append(H2("Tại sao phải tự xây dataset?"))
    e.append(P("Không có dataset công khai nào có 4 nhãn NUTRITION_LOOKUP / HEALTH_ADVICE / BOTH / NONE "
               "theo đúng schema của đồ án. "
               "Các bộ intent dataset phổ biến thường dành cho chatbot ngân hàng, "
               "hỗ trợ khách hàng, hoặc các tác vụ chung — không khớp."))
    e.append(P("Vì vậy nhóm dùng LLM (Llama 3.1 local) để sinh câu hỏi tổng hợp, "
               "sau đó chạy nhiều bước kiểm tra chất lượng."))

    e.append(H2("Hành trình dataset: 2.400 → 2.000 → 2.240"))
    e.append(Code(
        "Bước 1: LLM sinh 2.400 câu thô  (600 câu × 4 nhãn)\n\n"
        "Bước 2: Lọc near-duplicate bằng MinHash LSH\n"
        "          91 câu gần trùng bị loại\n"
        "        -> còn 2.309 câu\n"
        "        Lấy 500 câu/nhãn để cân bằng 4 nhãn\n"
        "        -> còn 2.000 câu sạch  (500 câu × 4 nhãn)\n\n"
        "Bước 3: Thêm 240 hard-negative examples  (60 câu × 4 nhãn)\n"
        "        (câu khó phân loại, ranh giới mờ giữa các nhãn)\n"
        "        -> tổng cộng 2.240 câu  (560 câu × 4 nhãn)\n\n"
        "Bước 4: Standard split (stratified, seed=42)\n"
        "          Train : 1.792 câu  (448/nhãn)\n"
        "          Test  :   448 câu  (112/nhãn)"))

    e.append(H2("Vì sao cần lọc near-duplicate?"))
    e.append(P("LLM có thể sinh nhiều câu gần giống nhau:"))
    e.append(Code(
        '"How much protein is in salmon?"\n'
        '"What is the protein amount in salmon?"\n'
        '"How many grams of protein does salmon contain?"\n'
        "# Ba câu này gần như giống nhau về nghĩa\n\n"
        "# Nếu một câu vào train và một câu vào test:\n"
        "# -> Model 'đã thấy' câu test trong lúc train\n"
        "# -> Điểm test cao nhưng không phản ánh thực tế"))
    e.append(P("<b>MinHash LSH</b> là kỹ thuật tìm câu gần trùng hiệu quả. "
               "MinHash tạo 'chữ ký' ngắn cho mỗi câu, "
               "LSH (Locality-Sensitive Hashing) gom các chữ ký giống nhau vào cùng nhóm. "
               "Chỉ so sánh trong nhóm thay vì so mọi cặp — "
               "giảm từ O(n²) xuống gần O(n)."))

    e.append(H2("Vì sao cần cân bằng 4 nhãn?"))
    e.append(P("Nếu dataset có 500 NUTRITION_LOOKUP, 500 HEALTH_ADVICE, 500 BOTH và chỉ 100 NONE, "
               "model có thể đạt accuracy 83% chỉ bằng cách không bao giờ đoán NONE. "
               "Cân bằng 560 câu/nhãn giúp model học tất cả 4 nhãn công bằng."))

    e.append(H2("Kiểm tra semantic separation — trước khi train"))
    e.append(P("Trước khi bỏ công train, nhóm kiểm tra xem 4 nhãn có thực sự phân tách tốt không. "
               "Cách làm: embed tất cả câu bằng MiniLM thành vector, "
               "rồi tính độ gần giữa các cặp câu:"))
    e.append(Code(
        "within_avg  = mean(cosine similarity cặp câu CÙNG nhãn)   # = 0.258\n"
        "between_avg = mean(cosine similarity cặp câu KHÁC nhãn)   # = 0.126\n"
        "ratio       = within_avg / between_avg                     # = 2.05x\n\n"
        "# ratio > 1: câu cùng nhãn gần nhau hơn câu khác nhãn\n"
        "# ratio = 2.05: câu cùng nhãn gần nhau gấp đôi câu khác nhãn\n"
        "# Tín hiệu tốt: 4 nhãn có thể phân loại được"))
    e.append(Warn("ratio 2.05x là tín hiệu phân cụm, không phải bằng chứng mọi label đúng 100%. "
                  "Dataset do LLM sinh có thể có template bias — "
                  "model học được pattern nhưng chưa chắc tổng quát hóa tốt với câu thực tế.",
                  label="Giới hạn cần biết"))

    e.append(H2("Training: BERT fine-tune cho phân loại 4 class"))
    e.append(Code(
        "# Kiến trúc đầy đủ:\n"
        "Câu hỏi\n"
        "  -> WordPiece tokenizer\n"
        "     (max_length=128, padding, truncation)\n"
        "  -> input_ids + attention_mask\n"
        "  -> BERT encoder 12 layers\n"
        "  -> vector của [CLS]  (768 số — đại diện cả câu)\n"
        "  -> Linear(768 -> 4)  (lớp phân loại mới)\n"
        "  -> logits: 4 điểm số thô\n"
        "  -> argmax -> intent label\n\n"
        "# Hyperparameters:\n"
        "Model     : bert-base-uncased\n"
        "Epochs    : 3\n"
        "Batch size: 16\n"
        "LR        : 2e-5\n"
        "Optimizer : AdamW\n"
        "Loss      : CrossEntropyLoss (Hugging Face tự tính khi truyền labels)"))

    e.append(H2("99.36% — đọc đúng con số này"))
    e.append(Code(
        "Test set : 448 câu  (112 câu/nhãn × 4 nhãn)\n"
        "Đúng     : 445 câu\n"
        "Sai      :   3 câu  (ranh giới HEALTH_ADVICE ↔ BOTH)\n\n"
        "Accuracy = 445 / 448 = 99.33%  (slide ghi 99.36% từ split khác)\n\n"
        "ĐÂY LÀ:   held-out test accuracy trên custom synthetic dataset\n"
        "KHÔNG LÀ: accuracy của toàn chatbot ngoài thực tế\n"
        "KHÔNG LÀ: bằng chứng model không overfit\n"
        "KHÔNG LÀ: accuracy với câu hỏi tiếng Việt hay cách hỏi tự nhiên ngoài đời"))
    e.append(Tip(
        "Accuracy cao vì: (1) 4 nhãn có ranh giới rõ ràng, "
        "(2) dataset cân bằng và (3) LLM sinh câu nhất quán theo pattern. "
        "Đây là controlled test, không phải open-world benchmark.",
        label="Vì sao accuracy cao"))
    e.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 6 — TÌM KIẾM TÀI LIỆU
    # ══════════════════════════════════════════════════════════════════════════
    e.append(Banner("6","Tìm kiếm tài liệu",
        "TF-IDF · BM25 · Dense Embedding · RRF · Cross-encoder Reranker"))
    e.append(S(12))

    e.append(H2("Bài toán retrieval"))
    e.append(P("Có 3.633 bài báo y sinh trong kho. "
               "Người dùng hỏi 'Is salmon good for heart health?'. "
               "Làm sao tìm ra vài bài liên quan nhất trong vài giây "
               "mà không đọc hết 3.633 bài?"))
    e.append(P("Cần một cách chấm điểm nhanh: bài nào liên quan đến câu hỏi hơn."))

    e.append(H2("TF-IDF — cách tìm đơn giản nhất"))
    e.append(P("Ý tưởng trực quan: một từ quan trọng với câu hỏi nếu "
               "nó xuất hiện <b>nhiều trong bài này</b> nhưng <b>ít trong các bài khác</b>. "
               "Từ xuất hiện ở khắp nơi (như 'the', 'is', 'a') không mang nhiều thông tin."))
    e.append(S(4))
    e.append(Code(
        "TF (Term Frequency):\n"
        "  Từ này xuất hiện bao nhiêu lần trong bài?\n"
        "  TF('salmon', bài_A) = 5 / 200  # 5 lần trong bài 200 từ = 0.025\n\n"
        "IDF (Inverse Document Frequency):\n"
        "  Từ này có hiếm không? Hiếm = quan trọng hơn\n"
        "  IDF('salmon') = log(3633 / 120)  # chỉ 120/3633 bài có từ 'salmon'\n"
        "                = log(30.3) = 3.41  <- cao, vì salmon khá hiếm\n\n"
        "  IDF('the') = log(3633 / 3633) = log(1) = 0  <- 'the' vô nghĩa\n\n"
        "TF-IDF = TF × IDF\n"
        "  TF-IDF('salmon', bài_A) = 0.025 × 3.41 = 0.085"))
    e.append(P("<b>Điểm yếu của TF-IDF:</b>"))
    e.append(B("Từ lặp 10 lần → điểm tăng 10 lần (không 'no hơn' sau một mức nào đó)"))
    e.append(B("Bài dài tự nhiên có TF cao hơn bài ngắn dù không nhất thiết liên quan hơn"))
    e.append(B("Không nhận ra đồng nghĩa: 'heart disease' và 'cardiovascular condition' = khác nhau hoàn toàn"))

    e.append(H2("BM25 — cải tiến TF-IDF"))
    e.append(P("BM25 (Best Match 25) giải quyết 2 trong 3 vấn đề trên:"))
    e.append(P("<b>Vấn đề 1: Từ lặp nhiều quá.</b> "
               "BM25 thêm 'term saturation' — từ lặp nhiều lần thì điểm tăng ít dần, "
               "sau một ngưỡng gần như không tăng nữa. "
               "Tham số k1 = 1.5 điều chỉnh ngưỡng này."))
    e.append(Code(
        "# TF-IDF: lặp 10 lần -> điểm gấp 10\n"
        "# BM25 với k1=1.5:\n"
        "#   lặp 1  lần -> BM25 score = 0.63\n"
        "#   lặp 3  lần -> BM25 score = 0.86  (tăng ít)\n"
        "#   lặp 10 lần -> BM25 score = 0.95  (gần bằng 3 lần, không phải gấp 10)"))
    e.append(P("<b>Vấn đề 2: Bài dài có lợi không công bằng.</b> "
               "BM25 thêm 'length normalization' — chuẩn hóa điểm theo độ dài bài. "
               "Bài dài gấp đôi không tự nhiên được điểm gấp đôi. "
               "Tham số b = 0.75 điều chỉnh mức normalization."))

    e.append(H2("Dense Embedding — tìm theo nghĩa, không phải từ khóa"))
    e.append(P("BM25 và TF-IDF đều là 'sparse retrieval': "
               "chỉ so sánh xem hai văn bản có chứa cùng từ không. "
               "Vấn đề: 'heart disease' và 'cardiovascular condition' cùng nghĩa "
               "nhưng không có từ nào trùng → BM25 cho điểm 0."))
    e.append(P("Dense retrieval giải quyết: "
               "biến cả câu hỏi lẫn tài liệu thành vector số, "
               "rồi đo 'khoảng cách' giữa các vector:"))
    e.append(Code(
        '"heart disease"            -> [0.12, -0.08, 0.31, ...]  # 384 số\n'
        '"cardiovascular condition" -> [0.11, -0.07, 0.33, ...]  # Gần nhau!\n'
        '"banana smoothie recipe"   -> [-0.5,  0.9,  0.02, ...]  # Xa nhau\n\n'
        "# Model tạo vector: all-MiniLM-L6-v2\n"
        "# 384 chiều = mỗi câu được biểu diễn bằng 384 số\n"
        "# Vector được normalize: |v| = 1\n\n"
        "# Cosine similarity đo 'góc' giữa hai vector:\n"
        "# cùng hướng (góc 0°)  -> cosine = 1.0 -> rất gần nghĩa\n"
        "# vuông góc (góc 90°)  -> cosine = 0.0 -> không liên quan\n"
        "# ngược hướng (180°)   -> cosine = -1  -> đối lập nghĩa"))
    e.append(Tip(
        "Cosine similarity không cần nhớ công thức. "
        "Chỉ cần nhớ: cosine gần 1 = hai câu nói về cùng chủ đề. "
        "cosine gần 0 = hai câu không liên quan. "
        "Đây là thứ ChromaDB dùng để tìm bài báo gần với câu hỏi nhất.",
        label="Cách nhớ cosine"))

    e.append(H2("Vì sao kết hợp BM25 + Dense?"))
    e.append(DTable(["Method","Bắt được","Bỏ lỡ"],
        [["BM25","Thuật ngữ kỹ thuật chính xác: HbA1c, omega-3, polyphenol",
          "Đồng nghĩa: 'heart disease' ≠ 'cardiovascular condition'"],
         ["Dense","Đồng nghĩa, paraphrase, câu cùng nghĩa khác từ",
          "Đôi khi bỏ lỡ rare exact term"],
         ["Hybrid","Lấy ưu điểm cả hai","Phức tạp hơn cần gộp"]],
        cws=[2.5*cm,6.5*cm,6.5*cm]))
    e.append(S(4))
    e.append(P("Kết quả ablation trên 323 query NFCorpus (MRR@10):"))
    e.append(Code(
        "BM25 alone  : 0.5241\n"
        "Dense alone : 0.4991  <- thấp hơn BM25 (corpus y sinh cần exact term)\n"
        "Hybrid RRF  : 0.5435  <- cao hơn cả hai riêng lẻ\n"
        "+ Reranker  : 0.5754  <- cao nhất"))

    e.append(H2("Vì sao không cộng thẳng điểm BM25 + điểm Dense?"))
    e.append(P("Đây là vấn đề scale. "
               "Điểm BM25 có thể là 15.3 hoặc 8.7 (không có giới hạn trên). "
               "Điểm cosine của Dense luôn nằm trong [-1, 1]."))
    e.append(Code(
        "# Nếu cộng thẳng:\n"
        "Bài A: BM25 = 8.7,  Dense = 0.9  -> Tổng = 9.6\n"
        "Bài B: BM25 = 4.2,  Dense = 0.95 -> Tổng = 5.15\n\n"
        "# Bài A thắng chỉ vì BM25 lớn hơn, không phải vì thực sự liên quan hơn!\n"
        "# Dense score 0.95 vs 0.9 gần như không có tác dụng"))
    e.append(P("Giải pháp: thay vì dùng điểm số, dùng <b>thứ hạng</b> — "
               "bài đứng thứ mấy trong danh sách BM25? Thứ mấy trong Dense? "
               "Thứ hạng thì cùng scale (1, 2, 3, ...) nên có thể cộng được."))

    e.append(H2("RRF — Reciprocal Rank Fusion: gộp theo thứ hạng"))
    e.append(P("RRF dùng công thức đơn giản:"))
    e.append(Code(
        "RRF_score(bài d) = 1/(k + rank_BM25(d)) + 1/(k + rank_Dense(d))\n\n"
        "# k = 10 trong project\n"
        "# rank bắt đầu từ 1 (rank 1 = tốt nhất)\n\n"
        "# Tại sao có k?\n"
        "# -> Nếu không có k: rank 1 cho 1/(0+1) = 1.0, rank 2 cho 1/(0+2) = 0.5\n"
        "#    Khoảng cách giữa rank 1 và rank 2 quá lớn\n"
        "# -> k=10 làm 'trơn': rank 1 cho 1/11 = 0.09, rank 2 cho 1/12 = 0.08\n"
        "#    Khoảng cách nhỏ hơn -> top rank vẫn ưu tiên nhưng không 'độc tài'\n\n"
        "# Ví dụ tính tay:\n"
        "Bài A: BM25 rank 1, Dense rank 3\n"
        "  RRF(A) = 1/(10+1) + 1/(10+3)\n"
        "         = 1/11     + 1/13\n"
        "         = 0.0909   + 0.0769\n"
        "         = 0.1678\n\n"
        "Bài B: BM25 rank 2, Dense rank 2\n"
        "  RRF(B) = 1/(10+2) + 1/(10+2)\n"
        "         = 1/12     + 1/12\n"
        "         = 0.0833   + 0.0833\n"
        "         = 0.1667\n\n"
        "# Bài A thắng nhờ đứng đầu BM25\n"
        "# Bài được CẢ HAI xếp cao đều được thưởng"))
    e.append(Tip(
        "k=10 là hyperparameter của project. "
        "Paper RRF gốc dùng k=60 cho corpus web-scale. "
        "Corpus nhỏ hơn → k nhỏ hơn để top rank có ảnh hưởng rõ hơn. "
        "Muốn xác nhận 10 là tối ưu cần sweep nhiều giá trị k.",
        label="k=10 từ đâu ra?"))

    e.append(H2("Cross-encoder Reranker — đọc kỹ hơn một danh sách nhỏ"))
    e.append(P("Sau RRF có 20 bài ứng viên. "
               "Bây giờ cần chọn 3 bài tốt nhất để đưa cho AI. "
               "Retriever (BM25 + Dense) tìm nhanh nhưng không quá chính xác — "
               "có thể đưa về bài cùng chủ đề nhưng không thực sự trả lời câu hỏi."))
    e.append(P("<b>Bi-encoder (Dense Retriever):</b> Encode query và document riêng lẻ, "
               "rồi so cosine. Nhanh nhưng query và document không 'nhìn thấy' nhau khi encode."))
    e.append(P("<b>Cross-encoder (Reranker):</b> Ghép query và document lại thành một input:"))
    e.append(Code(
        "# Bi-encoder:\n"
        "query_vec = encode('Does salmon reduce heart risk?')     # encode RIÊNG\n"
        "doc_vec   = encode('Salmon contamination in Pacific')    # encode RIÊNG\n"
        "score     = cosine(query_vec, doc_vec)  <- không thấy nhau lúc encode\n\n"
        "# Cross-encoder:\n"
        "input = '[CLS] Does salmon reduce heart risk? [SEP] Salmon contamination ... [SEP]'\n"
        "score = model(input)  # query VÀ document attention đến nhau cùng lúc\n"
        "# -> Biết 'contamination' không liên quan đến 'reduce risk' -> điểm thấp"))
    e.append(P("Cross-encoder chính xác hơn nhưng chậm hơn — phải chạy model mới cho mỗi cặp. "
               "Vì vậy chỉ dùng trên 20 bài ứng viên, không phải toàn bộ 3.633 bài."))
    e.append(Code(
        "# Lazy rerank: nếu bài số 1 đã bỏ xa bài số 2, bỏ qua reranker\n"
        "if candidates[0].score - candidates[1].score >= 0.05:\n"
        "    chunks = candidates[:3]  # tiết kiệm thời gian\n"
        "else:\n"
        "    chunks = reranker.rerank(query, candidates, top_k=3)"))
    e.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 7 — ĐÁNH GIÁ
    # ══════════════════════════════════════════════════════════════════════════
    e.append(Banner("7","Đánh giá — Đọc đúng các con số",
        "MRR@10 · F1 · Accuracy · Những số không dùng làm headline"))
    e.append(S(12))

    e.append(H2("Tại sao đánh giá theo từng thành phần riêng?"))
    e.append(P("Nếu gộp tất cả vào một con số duy nhất, "
               "không biết vấn đề nằm ở đâu khi hệ thống sai. "
               "Retrieval tệ hay AI tổng hợp tệ? "
               "Tách ra đánh giá riêng từng phần mới quy được trách nhiệm."))

    e.append(H2("Accuracy, Precision, Recall, F1"))
    e.append(P("Trước khi nói metric, cần hiểu 4 khái niệm cơ bản:"))
    e.append(Code(
        "# Ví dụ: model dự đoán intent của 100 câu\n"
        "# Tập trung vào nhãn NUTRITION_LOOKUP:\n\n"
        "TP (True Positive) : model nói NUTRITION và đúng   = 40\n"
        "TN (True Negative) : model nói khác NUTRITION và đúng = 52\n"
        "FP (False Positive): model nói NUTRITION nhưng sai = 3  (nhầm sang NUTRITION)\n"
        "FN (False Negative): model nói khác nhưng thực ra NUTRITION = 5  (bỏ lỡ)"))
    e.append(Code(
        "Accuracy  = (TP + TN) / tổng = (40+52)/100 = 92%\n"
        "           [Trong 100 câu, đúng bao nhiêu câu (kể cả đúng là NOT NUTRITION)?]\n\n"
        "Precision = TP / (TP + FP) = 40/(40+3) = 93%\n"
        "           [Trong những câu model nói là NUTRITION, đúng bao nhiêu?]\n\n"
        "Recall    = TP / (TP + FN) = 40/(40+5) = 89%\n"
        "           [Trong tất cả câu thực sự là NUTRITION, model bắt được bao nhiêu?]\n\n"
        "F1        = 2 * P * R / (P + R) = 2 * 0.93 * 0.89 / (0.93+0.89) = 91%\n"
        "           [Trung bình điều hòa của Precision và Recall]"))
    e.append(P("<b>Macro-F1:</b> Tính F1 riêng cho từng nhãn (NUTRITION, HEALTH, BOTH, NONE), "
               "rồi lấy trung bình. "
               "Mỗi nhãn có trọng số ngang nhau — nhãn ít câu không bị lép vế."))

    e.append(H2("MRR@10 — đo chất lượng retrieval"))
    e.append(P("MRR = Mean Reciprocal Rank. "
               "Đây là metric đo xem bài báo liên quan đầu tiên "
               "đứng ở vị trí nào trong top 10 kết quả tìm kiếm."))
    e.append(P("Tại sao quan tâm đến vị trí? Vì nếu bài liên quan đứng ở vị trí 1 thì AI dễ dùng hơn "
               "so với khi nó đứng ở vị trí 8 trong danh sách chỉ lấy top 3."))
    e.append(Code(
        "# 'Reciprocal rank' của một query:\n"
        "Bài liên quan đứng ở rank 1  -> điểm = 1/1 = 1.0   (tốt nhất)\n"
        "Bài liên quan đứng ở rank 2  -> điểm = 1/2 = 0.5\n"
        "Bài liên quan đứng ở rank 5  -> điểm = 1/5 = 0.2\n"
        "Không có bài liên quan trong top 10 -> điểm = 0\n\n"
        "# MRR = trung bình reciprocal rank trên 323 query\n\n"
        "# Ví dụ tính tay (3 query):\n"
        "Query 1: bài liên quan ở rank 1  -> 1/1 = 1.000\n"
        "Query 2: bài liên quan ở rank 4  -> 1/4 = 0.250\n"
        "Query 3: không có trong top 10   ->       0.000\n"
        "MRR = (1.000 + 0.250 + 0.000) / 3 = 0.417\n\n"
        "# Project đạt MRR@10 = 0.5754 -> trung bình bài liên quan đứng khá cao"))
    e.append(Warn(
        "MRR@10 = 0.5754 KHÔNG có nghĩa là 57.54% câu trả lời đúng. "
        "MRR đo retrieval ranking, không phải chất lượng câu trả lời cuối cùng. "
        "Hai chỉ số này hoàn toàn khác nhau.",
        label="Lỗi hay gặp khi đọc MRR"))

    e.append(H2("323 query từ đâu?"))
    e.append(P("NFCorpus là bộ tài liệu y sinh chuẩn (BEIR benchmark). "
               "Kèm theo corpus là file qrels — ground truth: "
               "với mỗi câu query, file ghi lại document nào là liên quan và điểm relevance."))
    e.append(Code(
        "# data/nfcorpus/qrels/test.tsv có format:\n"
        "query_id   doc_id    relevance_score\n"
        "QGEN7      MED-4565  2\n"
        "QGEN7      MED-1234  1\n"
        "QGEN12     MED-8901  1\n"
        "...\n\n"
        "# 323 = số query ID duy nhất trong file test.tsv\n"
        "# (không phải file có 323 dòng, có thể nhiều dòng hơn\n"
        "#  vì một query có thể liên quan nhiều document)"))

    e.append(H2("Ablation Study — Hybrid Retrieval"))
    e.append(DTable(["Method","MRR@10","Nhận xét"],
        [["TF-IDF","0.3796","Baseline: đơn giản nhất, yếu nhất"],
         ["BM25","0.5241","Mạnh với thuật ngữ y khoa chính xác"],
         ["Dense MiniLM (base)","0.4991","Semantic tốt nhưng thấp hơn BM25 trên corpus này"],
         ["Dense Fine-tuned","0.4685","Catastrophic forgetting: fine-tune tập nhỏ làm tệ hơn"],
         ["Hybrid RRF","0.5435","Kết hợp tốt hơn từng cái riêng lẻ"],
         ["Hybrid + Reranker","0.5754","Tốt nhất; reranker tăng +0.0319"]],
        cws=[4.5*cm,2.5*cm,8.5*cm]))

    e.append(H2("Những con số KHÔNG dùng làm headline"))
    e.append(B(ic("reports/en/rag_eval/summary.json") +
               ": evaluated_rows = 3/200. Chỉ 3 câu được đánh giá. Không đại diện."))
    e.append(B("Token F1: đo overlap từ khóa giữa answer dự đoán và answer mẫu. "
               "Khi AI diễn đạt cùng ý bằng từ khác thì bị phạt — không phù hợp câu trả lời tự do."))
    e.append(B("RAGAS: workspace hiện không còn notebook RAGAS. Không claim kết quả RAGAS chính thức."))
    e.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 8 — FLOW CODE ĐẦY ĐỦ
    # ══════════════════════════════════════════════════════════════════════════
    e.append(Banner("8","Flow code đầy đủ","Từ câu hỏi đến câu trả lời — trace từng bước"))
    e.append(S(12))

    e.append(H2("Pipeline code thực tế"))
    e.append(Code(
        "# src/en/pipeline.py — ENPipeline.answer()\n\n"
        "# Bước 1: NER câu hiện tại\n"
        "curr_entities = self.ner.predict(query)\n"
        "# Ví dụ: {'FOOD': ['salmon'], 'NUTRIENT': ['protein'], 'DISEASE': [], 'SYMPTOM': []}\n\n"
        "# Bước 2: Lấy entity từ lịch sử hội thoại (tối đa 10 message gần nhất)\n"
        "for msg in reversed(history[-10:]):\n"
        "    if msg.get('role') != 'user': continue\n"
        "    hist_ent = self.ner.predict(msg['content'])\n"
        "    # Backfill: nếu câu hiện tại thiếu FOOD thì lấy từ lịch sử\n\n"
        "# Bước 3: Phân loại intent\n"
        "intent = self.clf.classify(search_query)\n"
        "# Có thể là: NUTRITION_LOOKUP, HEALTH_ADVICE, BOTH, NONE\n\n"
        "# Bước 4: Xử lý từng nhánh\n"
        "if intent == 'NONE':\n"
        "    return static_reject_response  # <100ms, không gọi DB hay AI\n\n"
        "if intent in ('NUTRITION_LOOKUP', 'BOTH'):  # HAI if ĐỘC LẬP\n"
        "    food = clean_food_entity(entities['FOOD'])\n"
        "    nutrition_data = usda_lookup(food)\n\n"
        "if intent in ('HEALTH_ADVICE', 'BOTH'):     # không phải elif\n"
        "    candidates = hybrid_retriever.retrieve(query, top_k=20)\n"
        "    health_chunks = reranker.rerank(query, candidates, top_k=3)\n\n"
        "# Bước 5: Sinh câu trả lời\n"
        "result = generator.generate(intent, nutrition_data, health_chunks)"))

    e.append(H2("Fast-path: khi nào không gọi AI?"))
    e.append(Code(
        "# generator.py — 3 điều kiện phải đủ cả 3:\n"
        "if (\n"
        "    query_type == 'NUTRITION_LOOKUP'          # (1) đúng intent\n"
        "    and single_nutrition is not None          # (2) tìm được đúng 1 record USDA\n"
        "    and single_nutrition.get('nutrients_per_100g')  # (3) record có đủ data\n"
        "):\n"
        "    # Format thẳng từ database, không gọi Llama\n"
        "    return {'answer': formatted_table, 'used_llm': False}\n\n"
        "# Nếu KHÔNG đủ 3 điều kiện -> đi LLM path\n"
        "# Ví dụ: BOTH luôn đi LLM path dù có USDA data (vì cần tổng hợp)"))

    e.append(H2("Bốn trace đầy đủ"))
    e.append(H3("Trace A — NUTRITION_LOOKUP"))
    e.append(Code(
        'Câu: "How many calories are in apple?"\n\n'
        "NER    : FOOD=['apple'], NUTRIENT=['calories']\n"
        "Intent : NUTRITION_LOOKUP\n"
        "SQLite : 'apple' -> Foundation Food record (fdc_id=1105430)\n"
        "Output : Markdown table từ USDA\n"
        "used_llm=False, latency < 1 giây\n"
        "Source : USDA FoodData Central (fdc_id=1105430)"))
    e.append(H3("Trace B — HEALTH_ADVICE"))
    e.append(Code(
        'Câu: "Is salmon good for heart health?"\n\n'
        "NER    : FOOD=['salmon']\n"
        "Intent : HEALTH_ADVICE\n"
        "BM25   : 80 bài thô (có 'salmon', 'heart', 'fish oil', 'cardiovascular'...)\n"
        "Dense  : 80 bài thô (gần nghĩa với 'salmon heart health')\n"
        "RRF    : gộp 2 danh sách -> top 20 candidate\n"
        "Reranker: đọc từng cặp (query, bài) -> top 3\n"
        "Llama  : đọc 3 bài + câu hỏi -> sinh câu trả lời có nguồn\n"
        "used_llm=True, latency ~15-30 giây"))
    e.append(H3("Trace C — BOTH"))
    e.append(Code(
        'Câu: "How much protein is in salmon, and is it good for heart?"\n\n'
        "NER    : FOOD=['salmon'], NUTRIENT=['protein']\n"
        "Intent : BOTH\n"
        "USDA   : lấy giá trị protein của salmon\n"
        "Retrieval: top 3 bài về salmon + tim mạch\n"
        "Llama  : tổng hợp USDA data + 3 bài -> câu trả lời đầy đủ\n"
        "KHÔNG fast-path vì BOTH luôn cần AI tổng hợp\n"
        "used_llm=True"))
    e.append(H3("Trace D — NONE"))
    e.append(Code(
        'Câu: "What is the result of 1+1?"\n\n'
        "Intent : NONE\n"
        "Output : 'I can only answer nutrition and health questions.'\n"
        "Không gọi USDA, không gọi retrieval, không gọi Llama\n"
        "latency < 100ms"))

    e.append(H2("Multi-turn: lịch sử hội thoại"))
    e.append(Code(
        "# use_llm_rewriter: false -> KHÔNG dùng Llama viết lại câu\n"
        "# Thay vào đó: entity backfill\n\n"
        "Turn 1: 'How much protein is in salmon?'\n"
        "        NER: FOOD=['salmon'] -> lưu vào history\n\n"
        "Turn 2: 'Is it good for heart health?'\n"
        "        NER câu này: FOOD=[]  (câu không nhắc salmon)\n"
        "        Pipeline thấy FOOD thiếu -> backfill 'salmon' từ history\n"
        "        Retrieval query: 'salmon good heart health'\n\n"
        "# Không cần người dùng nhắc lại 'salmon' mỗi câu"))
    e.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PHẦN 9 — PHẢN BIỆN
    # ══════════════════════════════════════════════════════════════════════════
    e.append(Banner("9","Câu hỏi phản biện và phòng thủ",
        "Câu hỏi thường gặp · Những câu tuyệt đối không nên nói"))
    e.append(S(12))

    e.append(H2("Câu hỏi theo từng chủ đề"))
    e.append(H3("Về toàn hệ thống"))
    e.append(QA("Đóng góp NLP nằm ở đâu nếu Llama không fine-tune?",
        "Pipeline: Intent routing (BERT 4-class), BioBERT-CRF NER, hybrid BM25+Dense+RRF, "
        "cross-encoder reranking, entity history backfill, fast-path USDA, đánh giá component. "
        "Llama là generator off-the-shelf."))
    e.append(QA("Spring Boot có vai trò AI gì?",
        "Không train/infer model. Lo phần web: auth/JWT, session, lưu lịch sử chat vào H2, "
        "chuyển message + history sang FastAPI."))

    e.append(H3("Về NER và Intent"))
    e.append(QA("NER hay Intent chạy trước?",
        "NER chạy trước (lấy entity câu hiện tại + backfill lịch sử). "
        "Sau đó classifier mới chạy. Nhưng Intent mới là thứ quyết định routing."))
    e.append(QA("BOTH có song song không?",
        "Không phải parallel thread. Hai nhánh (USDA và health retrieval) chạy tuần tự trong cùng request."))
    e.append(QA("CRF không tăng F1 thì dùng để làm gì?",
        "CRF mô hình hóa transition giữa nhãn liền kề, đảm bảo chuỗi BIO có cấu trúc hợp lý. "
        "Nếu tối giản theo metric thuần, Argmax là phương án đáng cân nhắc."))
    e.append(QA("Vì sao FOOD F1 cao hơn DISEASE?",
        "BC5CDR gốc nhiều nhãn Disease hơn FOOD. FOOD được học từ FoodBase nhỏ hơn "
        "và tên món ăn đa dạng hơn tên bệnh trong corpus y sinh."))

    e.append(H3("Về Retrieval"))
    e.append(QA("Tại sao Dense thấp hơn BM25?",
        "NFCorpus chứa nhiều thuật ngữ y khoa chính xác (HbA1c, glycemic index). "
        "BM25 tận dụng exact lexical match tốt. Dense vẫn hữu ích vì bổ sung paraphrase."))
    e.append(QA("k=10 của RRF từ đâu?",
        "Paper RRF gốc dùng k=60 cho web-scale corpus. "
        "Corpus nhỏ hơn → k nhỏ hơn để top rank có ảnh hưởng rõ hơn. "
        "Cần sweep nhiều k để xác nhận 10 là tối ưu — project chưa có sweep đó."))
    e.append(QA("Reranker có tạo document mới không?",
        "Không. Chỉ reorder 20 candidate đã có. Nếu relevant doc không có trong top 20, "
        "reranker không thể tạo ra nó."))
    e.append(QA("Đánh giá top 10 nhưng runtime lấy top 3?",
        "MRR@10 cần quan sát ranking đến rank 10 để đo. "
        "Runtime lấy top 3 để giữ prompt ngắn. Hai mục tiêu khác nhau."))

    e.append(H3("Về Generation"))
    e.append(QA("Fast-path có thực sự zero hallucination không?",
        "Fast-path loại bỏ LLM numeric hallucination vì số lấy trực tiếp từ USDA bằng code xác định. "
        "Rủi ro còn lại: food-name matching có thể chọn sai biến thể (chicken breast raw vs roasted)."))
    e.append(QA("Temperature 0 có hết hallucination không?",
        "Không. Giảm randomness của output. "
        "Grounding, source quality và fast-path mới là các lớp kiểm soát chính."))
    e.append(QA("BOTH có fast-path không?",
        "Không. BOTH cần AI tổng hợp số USDA lẫn bằng chứng y khoa → luôn gọi Llama."))
    e.append(QA("Nếu context sai, AI bám context thì sao?",
        "Answer có thể faithful (bám đúng context) nhưng vẫn incorrect (context sai). "
        "Retrieval quality và answer correctness là hai tầng khác nhau."))

    e.append(H3("Về đánh giá"))
    e.append(QA("99.36% là accuracy toàn chatbot?",
        "Không. Đây là held-out test accuracy trên 448 câu của custom synthetic dataset. "
        "Không phản ánh accuracy ngoài đời hay với câu hỏi thực tế."))
    e.append(QA("Metric mạnh nhất của bài là gì?",
        "Retrieval MRR@10: có ground truth rõ nhất từ NFCorpus qrels. "
        "NER và intent là controlled component evaluation. "
        "Generation hiện chưa có benchmark chính thức."))
    e.append(QA("Tại sao chưa dùng BLEU/ROUGE?",
        "Không có gold free-text answer đủ tin cậy. "
        "BLEU/ROUGE phạt cách diễn đạt khác dù đúng nghĩa — không phù hợp câu trả lời tự do."))

    e.append(S(10))
    e.append(H2("Những câu tuyệt đối KHÔNG nên nói"))
    donts = [
        ('"NER quyết định intent"',
         'NER lấy entity. Intent Classifier quyết định routing.'),
        ('"BOTH chỉ cần có food và disease"',
         'BOTH phải yêu cầu CẢ HAI: số USDA chính xác VÀ health analysis.'),
        ('"Ratio 2.05x chứng minh label đúng 100%"',
         'Chỉ là tín hiệu phân cụm, không chứng minh label hoàn hảo.'),
        ('"99.36% là accuracy toàn chatbot"',
         'Held-out test accuracy trên custom synthetic dataset mà thôi.'),
        ('"Hệ thống là multi-hop RAG"',
         'Single-hop hybrid RAG. Không lặp nhiều bước reasoning/retrieval.'),
        ('"Dense fine-tuned đang runtime dùng"',
         'Config dùng base MiniLM. Fine-tuned checkpoint tồn tại nhưng không dùng.'),
        ('"RRF cộng BM25 score và cosine score"',
         'RRF dùng rank, không cộng raw score.'),
        ('"MRR 0.5754 = 57.54% câu trả lời đúng"',
         'MRR là retrieval metric, không phải accuracy câu trả lời.'),
        ('"Zero hallucination toàn hệ thống"',
         'Fast-path loại bỏ LLM numeric hallucination. Rủi ro food matching vẫn còn.'),
        ('"Reranker luôn chạy cho mọi health query"',
         'Lazy rerank có thể bypass khi gap đủ lớn.'),
        ('"Fine-tuned reranker đang active"',
         'Config dùng ms-marco pretrained. Domain checkpoint có nhưng comment trong config.'),
        ('"used_llm=False hiện trên frontend"',
         'Field này chỉ log ở server terminal, không forward ra frontend/UI.'),
        ('"RAGAS benchmark chính thức"',
         'Workspace không còn notebook RAGAS, không có kết quả chính thức.'),
    ]
    for wrong, right in donts:
        row = Table([[
            Paragraph(f'<font color="#9f1239">✗  {wrong}</font>',
                sty("w",fontName="DV-B",fontSize=9,textColor=C_RED,leading=13)),
            Paragraph(f'<font color="#166534">→  {right}</font>',
                sty("r",fontName="DV",fontSize=9,textColor=C_GREEN,leading=13)),
        ]],colWidths=[6.5*cm,9*cm])
        row.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LINEBELOW",(0,0),(-1,-1),0.5,colors.HexColor("#fecaca")),
            ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#fff1f2")),
            ("BACKGROUND",(1,0),(1,-1),C_LGREEN),
        ]))
        e.append(row)

    e.append(S(14))
    e.append(H2("Tóm tắt 60 giây — học thuộc ý, không học thuộc từ"))
    e.append(Box(
        "Hệ thống là chatbot dinh dưỡng và sức khỏe với bốn intent, trong đó NONE chặn "
        "câu ngoài domain ngay lập tức. "
        "BERT phân loại intent; BioBERT-CRF nhận diện FOOD, DISEASE và NUTRIENT. "
        "Câu hỏi số liệu đi vào SQLite USDA qua fast-path không qua LLM. "
        "Câu hỏi sức khỏe đi qua BM25 và MiniLM, gộp bằng RRF k=10, "
        "cross-encoder rerank, rồi top 3 tài liệu cho Llama 3.1:8b local. "
        "Đánh giá theo component: NER F1=0.95, Intent accuracy=99.36% (448 test), "
        "Retrieval MRR@10=0.5754 (323 NFCorpus queries). "
        "Điểm mạnh: phân tách đúng nguồn dữ liệu và đánh giá component rõ ràng. "
        "Giới hạn: generation chưa benchmark đầy đủ, intent data chủ yếu synthetic.",
        bg=C_LBLUE, border=C_BLUE))

    e.append(S(14))
    e.append(H2("Checklist trước khi học/demo"))
    items = [
        "Tự giải thích được RAG bằng ví dụ thư viện",
        "Vẽ lại 4 routing path kể cả NONE mà không nhìn slide",
        "Giải thích CrossEntropyLoss = -log(P(class đúng)) bằng ví dụ số cụ thể",
        "Giải thích TF-IDF và vì sao BM25 cải tiến nó (2 điểm cụ thể)",
        "Tính tay RRF: cho ví dụ k=10, rank 1 và rank 3",
        "Giải thích MRR@10 không phải answer accuracy",
        "Giải thích CRF không tăng F1 nhưng vẫn có giá trị",
        "Giải thích vì sao Dense FT tệ hơn base (catastrophic forgetting)",
        "Nói đúng 3 điều kiện fast-path",
        "Giải thích 2.400 → 2.000 → 2.240 từng bước",
        "Biết show terminal log vì UI không trả used_llm",
        "Biết câu nào KHÔNG được nói (xem danh sách đỏ bên trên)",
    ]
    for it in items:
        e.append(Paragraph(f"☐  {it}", sty("ck",fontSize=9.5,textColor=C_DGRAY,
            leading=14.5,leftIndent=8,spaceBefore=2,spaceAfter=2)))
    return e

# BUILD
print("Building...")
doc = make_doc("HealthCare_RAG_Deep_Explainer_Final.pdf")
doc.build(build())
print("Done!")
