TEST_SAMPLES = [
    {
        "id": "en_01",
        "markdown": """# Alice Smith
**Email:** alice.smith@example.com
**Phone:** +1-555-0199

## Summary
Experienced software engineer specializing in backend development and scalable microservices.

## Skills
Python, FastAPI, React, Docker, Kubernetes, SQL, Agile

## Experience

### Senior Software Engineer
**TechCorp Inc.**
*Jan 2020 - Present*
- Architected and deployed microservices using FastAPI and Docker.
- Improved database query performance by 30% using SQL optimization techniques.

### Software Developer
**WebSolutions LLC**
*Jun 2017 - Dec 2019*
- Developed RESTful APIs using Python.
- Collaborated with frontend teams to integrate React components.

## Education

### B.S. Computer Science
**State University**
*2013 - 2017*
""",
        "ground_truth": {
            "full_name": "Alice Smith",
            "contact_email": "alice.smith@example.com",
            "contact_phone": "+1-555-0199",
            "skills": ["Python", "FastAPI", "React", "Docker", "Kubernetes", "SQL", "Agile"],
            "experience": [
                {
                    "company": "TechCorp Inc.",
                    "role": "Senior Software Engineer",
                    "start_date": "Jan 2020",
                    "end_date": "Present",
                    "achievements": [
                        "Architected and deployed microservices using FastAPI and Docker.",
                        "Improved database query performance by 30% using SQL optimization techniques."
                    ]
                },
                {
                    "company": "WebSolutions LLC",
                    "role": "Software Developer",
                    "start_date": "Jun 2017",
                    "end_date": "Dec 2019",
                    "achievements": [
                        "Developed RESTful APIs using Python.",
                        "Collaborated with frontend teams to integrate React components."
                    ]
                }
            ],
            "education": [
                {
                    "institution": "State University",
                    "degree": "B.S.",
                    "field_of_study": "Computer Science",
                    "graduation_year": "2017"
                }
            ]
        }
    },
    {
        "id": "th_01",
        "markdown": """# สมชาย ใจดี
**อีเมล:** somchai.j@example.co.th
**เบอร์โทร:** 081-234-5678

## ทักษะ
Data Engineering, Apache Spark, Airflow, Python, SQL, Hadoop, AWS

## ประสบการณ์การทำงาน

### Data Engineer
**บริษัท ข้อมูลไทย จำกัด**
*มี.ค. 2564 - ปัจจุบัน*
- สร้างและดูแล Data Pipeline ด้วย Apache Airflow และ Spark
- จัดการข้อมูลขนาดใหญ่บน Hadoop และ AWS

### Junior Data Analyst
**บริษัท วิเคราะห์ธุรกิจ จำกัด**
*ก.ค. 2561 - ก.พ. 2564*
- วิเคราะห์ข้อมูลยอดขายด้วย SQL และ Python
- สร้าง Dashboard สำหรับผู้บริหาร

## การศึกษา

### ปริญญาตรี วิศวกรรมศาสตร์ (วิศวกรรมคอมพิวเตอร์)
**มหาวิทยาลัยเทคโนโลยี**
*2557 - 2561*
""",
        "ground_truth": {
            "full_name": "สมชาย ใจดี",
            "contact_email": "somchai.j@example.co.th",
            "contact_phone": "081-234-5678",
            "skills": ["Data Engineering", "Apache Spark", "Airflow", "Python", "SQL", "Hadoop", "AWS"],
            "experience": [
                {
                    "company": "บริษัท ข้อมูลไทย จำกัด",
                    "role": "Data Engineer",
                    "start_date": "มี.ค. 2564",
                    "end_date": "ปัจจุบัน",
                    "achievements": [
                        "สร้างและดูแล Data Pipeline ด้วย Apache Airflow และ Spark",
                        "จัดการข้อมูลขนาดใหญ่บน Hadoop และ AWS"
                    ]
                },
                {
                    "company": "บริษัท วิเคราะห์ธุรกิจ จำกัด",
                    "role": "Junior Data Analyst",
                    "start_date": "ก.ค. 2561",
                    "end_date": "ก.พ. 2564",
                    "achievements": [
                        "วิเคราะห์ข้อมูลยอดขายด้วย SQL และ Python",
                        "สร้าง Dashboard สำหรับผู้บริหาร"
                    ]
                }
            ],
            "education": [
                {
                    "institution": "มหาวิทยาลัยเทคโนโลยี",
                    "degree": "ปริญญาตรี",
                    "field_of_study": "วิศวกรรมคอมพิวเตอร์",
                    "graduation_year": "2561"
                }
            ]
        }
    },
    {
        "id": "bi_01",
        "markdown": """# วรรณิภา สุขสมบูรณ์ (Wannipa Suksombun)
**Email:** w.suksombun@ai-startup.com
**Tel:** +66 90 987 6543

## Objective
Machine Learning Engineer passionate about NLP and Computer Vision. สนใจในการพัฒนา AI เพื่อแก้ปัญหาจริง

## Skills / ทักษะ
- Machine Learning: PyTorch, TensorFlow, Scikit-learn
- Languages: Python, C++
- Tools: Git, Docker, MLflow
- ภาษา: Thai (Native), English (Fluent)

## Work Experience

### Machine Learning Engineer
**AI Vision Co., Ltd.**
*August 2021 - Present*
- พัฒนาระบบ Image Recognition สำหรับโรงงานอุตสาหกรรม
- Deployed models using Docker and optimized with TensorRT.

### AI Researcher (Intern)
**National Research Lab**
*Jan 2021 - May 2021*
- วิจัยและทดลองโมเดล NLP ภาษาไทย (Thai NLP)
- Published a paper on Thai Sentiment Analysis.

## Education

### Master of Science in Artificial Intelligence
**Global Tech University**
*2019 - 2021*

### Bachelor of Science in Mathematics
**Local Science College**
*2015 - 2019*
""",
        "ground_truth": {
            "full_name": "วรรณิภา สุขสมบูรณ์",
            "contact_email": "w.suksombun@ai-startup.com",
            "contact_phone": "+66 90 987 6543",
            "skills": ["PyTorch", "TensorFlow", "Scikit-learn", "Python", "C++", "Git", "Docker", "MLflow"],
            "experience": [
                {
                    "company": "AI Vision Co., Ltd.",
                    "role": "Machine Learning Engineer",
                    "start_date": "August 2021",
                    "end_date": "Present",
                    "achievements": [
                        "พัฒนาระบบ Image Recognition สำหรับโรงงานอุตสาหกรรม",
                        "Deployed models using Docker and optimized with TensorRT."
                    ]
                },
                {
                    "company": "National Research Lab",
                    "role": "AI Researcher (Intern)",
                    "start_date": "Jan 2021",
                    "end_date": "May 2021",
                    "achievements": [
                        "วิจัยและทดลองโมเดล NLP ภาษาไทย (Thai NLP)",
                        "Published a paper on Thai Sentiment Analysis."
                    ]
                }
            ],
            "education": [
                {
                    "institution": "Global Tech University",
                    "degree": "Master of Science",
                    "field_of_study": "Artificial Intelligence",
                    "graduation_year": "2021"
                },
                {
                    "institution": "Local Science College",
                    "degree": "Bachelor of Science",
                    "field_of_study": "Mathematics",
                    "graduation_year": "2019"
                }
            ]
        }
    }
]
