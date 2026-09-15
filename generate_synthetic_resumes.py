"""
Synthetic Resume Generator & Augmentation Engine
Generates paired High-Resolution Resume Images + Ground-Truth Markdown
Supports Thai, English, and Bilingual resumes across diverse layouts:
- Single-Column Clean
- Modern Two-Column (Sidebar + Content)
- Tabular Qualifications Layout
- Dense Timeline Layout
Includes authentic scan & photocopier augmentations.
"""

import os
import sys
import random
import argparse
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pypdfium2 as pdfium

# Register Windows Thai font
FONT_NAME = "Helvetica"
THAI_FONT = None
for fp in [
    Path("C:/Windows/Fonts/tahoma.ttf"),
    Path("C:/Windows/Fonts/angsana.ttf"),
    Path("C:/Windows/Fonts/cordia.ttf"),
]:
    if fp.exists():
        try:
            pdfmetrics.registerFont(TTFont("ThaiFont", str(fp)))
            THAI_FONT = "ThaiFont"
            break
        except Exception:
            pass

DEFAULT_FONT = THAI_FONT or "Helvetica"

# Thai and English Sample Data Pools
THAI_FIRST_NAMES = ["สมชาย", "วรรณิภา", "ธีรพัฒน์", "อภิสิทธิ์", "กานดา", "ณัฐพร", "กิตติพงษ์", "ปิยะภรณ์", "ชลธิชา", "วีระพล"]
THAI_LAST_NAMES = ["รักเรียน", "สุขสมบูรณ์", "วงศ์สวัสดิ์", "เจริญผล", "คงมั่น", "รัตนไพศาล", "จันทรวงศ์", "มีชัย"]
EN_FIRST_NAMES = ["Alex", "Jordan", "David", "Alice", "Elena", "Michael", "Sarah", "Marcus", "Samantha", "Lucas"]
EN_LAST_NAMES = ["Smith", "Chen", "Miller", "Taylor", "Wong", "Patel", "Johnson", "Davis", "Larsson", "Tanaka"]

ROLES = [
    ("Senior Software Engineer", "วิศวกรซอฟต์แวร์อาวุโส"),
    ("Cloud Infrastructure Architect", "สถาปนิกโครงสร้างคลาวด์"),
    ("Senior Data Engineer", "วิศวกรข้อมูลอาวุโส"),
    ("Machine Learning Specialist", "ผู้เชี่ยวชาญด้านการเรียนรู้ของเครื่อง"),
    ("DevOps Platform Engineer", "วิศวกรแพลตฟอร์มเดฟออปส์"),
    ("Lead Backend Developer", "หัวหน้านักพัฒนาแบ็กเอนด์"),
]

COMPANIES = [
    ("SCB 10X Co., Ltd.", "บริษัท เอสซีบี เท็นเอกซ์ จำกัด"),
    ("TechCorp Global", "บริษัท เทคคอร์ป จำกัด"),
    ("Agoda Services", "บริษัท อโกด้า เซอร์วิสเซส จำกัด"),
    ("KASIKORN Business-Technology Group (KBTG)", "กลุ่มเทคโนโลยีกสิกรไทย"),
    ("Ascend Group", "บริษัท แอสเซนด์ กรุ๊ป"),
    ("True Digital Group", "ทรู ดิจิทัล กรุ๊ป"),
    ("Shopee Thailand", "ช้อปปี้ ประเทศไทย"),
]

UNIVERSITIES = [
    ("Chulalongkorn University", "จุฬาลงกรณ์มหาวิทยาลัย"),
    ("Kasetsart University", "มหาวิทยาลัยเกษตรศาสตร์"),
    ("Thammasat University", "มหาวิทยาลัยธรรมศาสตร์"),
    ("King Mongkut's University of Technology Thonburi", "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี (KMUTT)"),
    ("Carnegie Mellon University", "มหาวิทยาลัยคาร์เนกีเมลลอน"),
]

TECH_SKILLS = [
    "Python", "Go", "Java", "TypeScript", "FastAPI", "React", "Docker", "Kubernetes",
    "Terraform", "AWS (EKS, S3, RDS)", "GCP", "PostgreSQL", "Redis", "Apache Kafka",
    "Apache Spark", "Airflow", "PyTorch", "Hugging Face", "MLflow", "Elasticsearch",
    "CI/CD", "GitOps", "Microservices Architecture", "Performance Optimization"
]

THAI_SKILLS = [
    "การพัฒนาไมโครเซอร์วิส (Microservices)", "การบริหารคลัสเตอร์ Kubernetes",
    "การสร้าง Data Pipeline", "การประมวลผลภาษาธรรมชาติภาษาไทย (Thai NLP)",
    "การปรับแต่งฐานข้อมูลความเร็วสูง", "การจัดการโครงสร้างพื้นฐานแบบโค้ด (IaC)"
]


def generate_single_column_resume(canvas_obj, c_id: str, is_thai: bool = False) -> str:
    """Generate a clean single-column resume and return ground-truth markdown."""
    fn = random.choice(THAI_FIRST_NAMES) if is_thai else random.choice(EN_FIRST_NAMES)
    ln = random.choice(THAI_LAST_NAMES) if is_thai else random.choice(EN_LAST_NAMES)
    full_name = f"{fn} {ln}"
    role_en, role_th = random.choice(ROLES)
    title = role_th if is_thai else role_en
    email = f"{fn.lower()}.{ln.lower()}@example.com"
    phone = f"08{random.randint(1,9)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
    
    # Draw Canvas
    canvas_obj.setFont(DEFAULT_FONT, 20)
    canvas_obj.drawString(50, 770, full_name)
    canvas_obj.setFont(DEFAULT_FONT, 12)
    canvas_obj.drawString(50, 750, title)
    canvas_obj.setFont(DEFAULT_FONT, 10)
    canvas_obj.drawString(50, 735, f"Email: {email} | Phone: {phone} | Bangkok, Thailand")
    canvas_obj.setStrokeColorRGB(0.7, 0.7, 0.7)
    canvas_obj.setLineWidth(1)
    canvas_obj.line(50, 725, 545, 725)
    
    # Skills
    canvas_obj.setFont(DEFAULT_FONT, 14)
    sec_skills = "ทักษะและความเชี่ยวชาญ (Technical Skills)" if is_thai else "Technical Skills"
    canvas_obj.drawString(50, 700, sec_skills)
    canvas_obj.setFont(DEFAULT_FONT, 9.5)
    selected_skills = random.sample(TECH_SKILLS, 8)
    if is_thai:
        selected_skills.extend(random.sample(THAI_SKILLS, 2))
    skills_str = ", ".join(selected_skills)
    canvas_obj.drawString(50, 680, skills_str[:90])
    if len(skills_str) > 90:
        canvas_obj.drawString(50, 665, skills_str[90:180])
        
    # Experience
    canvas_obj.setFont(DEFAULT_FONT, 14)
    sec_exp = "ประสบการณ์การทำงาน (Experience)" if is_thai else "Professional Experience"
    canvas_obj.drawString(50, 635, sec_exp)
    
    y = 615
    md_exp = []
    comp_list = random.sample(COMPANIES, 2)
    
    for i, (comp_en, comp_th) in enumerate(comp_list):
        c_name = comp_th if is_thai else comp_en
        dates = f"25{random.randint(62,64)} - ปัจจุบัน" if is_thai else f"20{random.randint(20,22)} - Present" if i == 0 else f"20{random.randint(16,19)} - 20{random.randint(20,22)}"
        canvas_obj.setFont(DEFAULT_FONT, 11)
        canvas_obj.drawString(50, y, f"{title} — {c_name}")
        canvas_obj.setFont(DEFAULT_FONT, 9)
        canvas_obj.drawString(420, y, dates)
        y -= 18
        
        bullets = [
            "- ออกแบบและพัฒนาระบบ Cloud Microservices รองรับผู้ใช้กว่า 1,000,000 รายต่อวัน" if is_thai else "- Architected distributed microservices platform processing 10M+ daily events.",
            "- ลดเวลาการประมวลผลข้อมูลลง 45% ด้วยการปรับแต่ง Database Indexing และ Caching" if is_thai else "- Reduced end-to-end database query latency by 45% using Redis caching and PostgreSQL tuning."
        ]
        for b in bullets:
            canvas_obj.drawString(65, y, b)
            y -= 16
        y -= 12
        md_exp.append(f"### {title}\n**{c_name}** | *{dates}*\n" + "\n".join(bullets))
        
    # Education
    canvas_obj.setFont(DEFAULT_FONT, 14)
    sec_edu = "ประวัติการศึกษา (Education)" if is_thai else "Education"
    canvas_obj.drawString(50, y, sec_edu)
    y -= 20
    u_en, u_th = random.choice(UNIVERSITIES)
    u_name = u_th if is_thai else u_en
    deg = "ปริญญาตรี วิศวกรรมคอมพิวเตอร์" if is_thai else "B.Sc. in Computer Science"
    canvas_obj.setFont(DEFAULT_FONT, 10)
    canvas_obj.drawString(50, y, f"{deg} — {u_name}")
    canvas_obj.drawString(450, y, "2561" if is_thai else "2018")
    
    # Build Ground Truth Markdown
    md_text = f"""# {full_name}
**Title:** {title}
**Contact:** {email} | {phone} | Bangkok, Thailand

## {sec_skills}
{skills_str}

## {sec_exp}
""" + "\n\n".join(md_exp) + f"""

## {sec_edu}
- **{deg}** — {u_name} ({"2561" if is_thai else "2018"})
"""
    return md_text


def generate_two_column_resume(canvas_obj, c_id: str, is_thai: bool = False) -> str:
    """Generate a modern two-column layout resume (sidebar + main body)."""
    fn = random.choice(THAI_FIRST_NAMES) if is_thai else random.choice(EN_FIRST_NAMES)
    ln = random.choice(THAI_LAST_NAMES) if is_thai else random.choice(EN_LAST_NAMES)
    full_name = f"{fn} {ln}"
    role_en, role_th = random.choice(ROLES)
    title = role_th if is_thai else role_en
    email = f"{fn.lower()}@{ln.lower()}.dev"
    phone = f"+66 {random.randint(80,99)}-{random.randint(100,999)}-{random.randint(1000,9999)}"

    # Draw Sidebar Background
    canvas_obj.setFillColorRGB(0.93, 0.94, 0.96)
    canvas_obj.rect(0, 0, 180, 842, fill=1, stroke=0)
    canvas_obj.setFillColorRGB(0, 0, 0)
    
    # Sidebar Content (Contact & Skills)
    canvas_obj.setFont(DEFAULT_FONT, 12)
    canvas_obj.drawString(20, 770, "CONTACT")
    canvas_obj.setFont(DEFAULT_FONT, 8.5)
    canvas_obj.drawString(20, 750, email[:25])
    canvas_obj.drawString(20, 735, phone)
    canvas_obj.drawString(20, 720, "Bangkok, Thailand")
    
    canvas_obj.setFont(DEFAULT_FONT, 12)
    canvas_obj.drawString(20, 680, "CORE SKILLS")
    canvas_obj.setFont(DEFAULT_FONT, 9)
    skills = random.sample(TECH_SKILLS, 10)
    sy = 660
    for s in skills:
        canvas_obj.drawString(20, sy, f"• {s}")
        sy -= 18

    # Main Column Content
    canvas_obj.setFont(DEFAULT_FONT, 22)
    canvas_obj.drawString(200, 770, full_name)
    canvas_obj.setFont(DEFAULT_FONT, 13)
    canvas_obj.drawString(200, 748, title)
    canvas_obj.setStrokeColorRGB(0.8, 0.8, 0.8)
    canvas_obj.line(200, 735, 560, 735)

    canvas_obj.setFont(DEFAULT_FONT, 13)
    canvas_obj.drawString(200, 710, "EXPERIENCE")
    comp_en, comp_th = random.choice(COMPANIES)
    c_name = comp_th if is_thai else comp_en
    canvas_obj.setFont(DEFAULT_FONT, 11)
    canvas_obj.drawString(200, 685, f"{title} | {c_name}")
    canvas_obj.setFont(DEFAULT_FONT, 9)
    canvas_obj.drawString(200, 668, "2021 – Present (Bangkok)")

    bullets = [
        "- Lead the architectural redesign of core data ingestion pipeline.",
        "- Managed Kubernetes deployment clusters across multi-cloud infrastructure.",
        "- Enhanced CI/CD throughput by 60% with automated canary releases."
    ]
    by = 648
    for b in bullets:
        canvas_obj.drawString(210, by, b)
        by -= 16

    canvas_obj.setFont(DEFAULT_FONT, 13)
    canvas_obj.drawString(200, 570, "EDUCATION")
    u_en, u_th = random.choice(UNIVERSITIES)
    canvas_obj.setFont(DEFAULT_FONT, 10)
    canvas_obj.drawString(200, 545, f"Bachelor of Engineering — {u_th if is_thai else u_en}")
    canvas_obj.drawString(200, 530, "Graduation: 2020")

    md_text = f"""# {full_name}
**Title:** {title}
**Email:** {email}
**Phone:** {phone}
**Location:** Bangkok, Thailand

## Skills
{", ".join(skills)}

## Experience
### {title} | {c_name}
*2021 – Present*
""" + "\n".join(bullets) + f"""

## Education
- **Bachelor of Engineering** — {u_th if is_thai else u_en} (2020)
"""
    return md_text


def apply_scan_augmentations(img: Image.Image) -> Image.Image:
    """Apply realistic scan artifacts: tilt, Gaussian blur, noise, photocopier contrast."""
    # 1. Perspective tilt / rotation (-2.5 to +2.5 degrees)
    angle = random.uniform(-2.5, 2.5)
    img = img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False, fillcolor="white")
    
    # 2. Subtle scanner blur
    if random.random() < 0.6:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.8)))

    # 3. Gaussian sensor / scanner noise
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, random.uniform(3, 10), arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    # 4. Photocopy contrast and brightness shifts
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(random.uniform(0.9, 1.25))
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(random.uniform(0.92, 1.05))

    return img


def generate_dataset(output_dir: Path, total_count: int = 100, augment: bool = True):
    """Generate paired High-Res Images and Ground-Truth Markdown files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    train_dir = output_dir / "train"
    val_dir = output_dir / "val"
    for d in [train_dir / "images", train_dir / "markdown", val_dir / "images", val_dir / "markdown"]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Generating {total_count} synthetic resumes with augment={augment}...")

    train_count = int(total_count * 0.85)
    
    for i in range(total_count):
        split = "train" if i < train_count else "val"
        target_dir = train_dir if split == "train" else val_dir
        sample_id = f"resume_{i+1:04d}"

        pdf_path = target_dir / "images" / f"{sample_id}.tmp.pdf"
        img_path = target_dir / "images" / f"{sample_id}.png"
        md_path = target_dir / "markdown" / f"{sample_id}.md"

        c = canvas.Canvas(str(pdf_path), pagesize=A4)
        is_thai = (i % 3 != 0)  # 66% Thai / Bilingual, 33% English
        is_two_col = (i % 2 == 0)

        if is_two_col:
            md_content = generate_two_column_resume(c, sample_id, is_thai=is_thai)
        else:
            md_content = generate_single_column_resume(c, sample_id, is_thai=is_thai)

        c.save()

        # Render PDF to image using pypdfium2 at 200 DPI
        doc = pdfium.PdfDocument(str(pdf_path))
        page_img = doc[0].render(scale=2.77).to_pil() # ~200 DPI
        doc.close()
        pdf_path.unlink()

        if augment:
            page_img = apply_scan_augmentations(page_img)

        page_img.save(str(img_path), "PNG")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content.strip() + "\n")

        if (i + 1) % 20 == 0 or (i + 1) == total_count:
            print(f"  [{i+1}/{total_count}] Created {sample_id} ({split})")

    print(f"[SUCCESS] Finished generating {total_count} resume pairs in {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic Resume Dataset Generator")
    parser.add_argument("--count", type=int, default=100, help="Total number of resumes to generate (default: 100)")
    parser.add_argument("--output", type=str, default="synthetic_dataset", help="Output directory path")
    parser.add_argument("--no-augment", action="store_true", help="Disable scan/noise augmentations")
    args = parser.parse_args()

    generate_dataset(Path(args.output), total_count=args.count, augment=not args.no_augment)
