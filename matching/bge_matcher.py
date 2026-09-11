import logging
import math
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

CANONICAL_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "SQL",
    "FastAPI", "Django", "Flask", "React", "Vue.js", "Next.js", "Node.js",
    "Docker", "Kubernetes", "Terraform", "AWS", "GCP", "Azure",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "PyTorch", "TensorFlow", "Scikit-learn",
    "Data Engineering", "Data Analysis", "Apache Spark", "Apache Kafka", "Airflow",
    "Git", "CI/CD", "Agile", "Scrum",
    "Project Management", "Team Leadership", "Communication",
]

COMMON_ALIASES: Dict[str, str] = {
    # Acronyms & common variants
    "k8s": "Kubernetes",
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "nlp": "NLP",
    "cv": "Computer Vision",
    "data sci": "Data Analysis",
    "data science": "Data Analysis",
    "js": "JavaScript",
    "ts": "TypeScript",
    "golang": "Go",
    "py": "Python",
    "postgres": "PostgreSQL",
    "reactjs": "React",
    "react.js": "React",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "tf": "TensorFlow",
    "pm": "Project Management",
    # Thai translations
    "การจัดการโครงการ": "Project Management",
    "การบริหารโครงการ": "Project Management",
    "การเป็นผู้นำทีม": "Team Leadership",
    "ภาวะผู้นำ": "Team Leadership",
    "การสื่อสาร": "Communication",
    "วิศวกรรมข้อมูล": "Data Engineering",
    "การวิเคราะห์ข้อมูล": "Data Analysis",
    "การเรียนรู้ของเครื่อง": "Machine Learning",
    "ปัญญาประดิษฐ์": "Machine Learning",
    "การประมวลผลภาษาธรรมชาติ": "NLP",
}

# Try importing sentence-transformers and torch
try:
    from sentence_transformers import SentenceTransformer
    import torch
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class SkillMatcher:
    def __init__(self, canonical_skills: Optional[List[str]] = None, model_name: str = 'BAAI/bge-m3', similarity_threshold: float = 0.85):
        self.canonical_skills = canonical_skills if canonical_skills is not None else CANONICAL_SKILLS
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        
        self.model = None
        self.canonical_embeddings = None
        self.use_fallback = not HAS_SENTENCE_TRANSFORMERS

        if not self.use_fallback:
            try:
                # Device detection
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Loading {model_name} on {device}...")
                self.model = SentenceTransformer(model_name, device=device)
                logger.info("Pre-computing canonical skill embeddings...")
                self.canonical_embeddings = self.model.encode(self.canonical_skills, normalize_embeddings=True)
            except Exception as e:
                logger.warning(f"Failed to load sentence-transformers model: {e}. Falling back to basic string matching.")
                self.use_fallback = True
        else:
            logger.info("sentence-transformers not installed. Using fallback string matcher.")

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _fallback_similarity(self, s1: str, s2: str) -> float:
        """Calculate a basic similarity score using Levenshtein distance."""
        s1, s2 = s1.lower().strip(), s2.lower().strip()
        
        # Exact match (case insensitive)
        if s1 == s2:
            return 1.0
            
        # Substring match bonus
        if s1 in s2 or s2 in s1:
            return 0.9

        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 0.0

        dist = self._levenshtein_distance(s1, s2)
        return 1.0 - (dist / max_len)

    def normalize_skills(self, extracted_skills: List[str]) -> List[Dict[str, Any]]:
        results = []
        if not extracted_skills:
            return results

        # Process each skill
        for ext_skill in extracted_skills:
            cleaned = ext_skill.strip().lower()
            if cleaned in COMMON_ALIASES:
                results.append({
                    "original": ext_skill,
                    "matched_canonical": COMMON_ALIASES[cleaned],
                    "similarity_score": 1.0
                })
                continue

            if self.use_fallback:
                best_match = None
                best_score = 0.0
                for can_skill in self.canonical_skills:
                    score = self._fallback_similarity(ext_skill, can_skill)
                    if score > best_score:
                        best_score = score
                        best_match = can_skill
                
                if best_score >= self.similarity_threshold:
                    results.append({
                        "original": ext_skill,
                        "matched_canonical": best_match,
                        "similarity_score": round(best_score, 4)
                    })
                else:
                    results.append({
                        "original": ext_skill,
                        "matched_canonical": None,
                        "similarity_score": round(best_score, 4)
                    })
            else:
                # Sentence Transformers branch for single unaliased skill
                import torch
                ext_emb = self.model.encode([ext_skill], normalize_embeddings=True)
                if not isinstance(ext_emb, torch.Tensor):
                    ext_emb = torch.tensor(ext_emb)
                if not isinstance(self.canonical_embeddings, torch.Tensor):
                    self.canonical_embeddings = torch.tensor(self.canonical_embeddings)
                
                cos_scores = torch.mm(ext_emb, self.canonical_embeddings.transpose(0, 1))[0]
                best_score, best_idx = torch.max(cos_scores, dim=0)
                best_score_val = best_score.item()
                
                if best_score_val >= self.similarity_threshold:
                    results.append({
                        "original": ext_skill,
                        "matched_canonical": self.canonical_skills[best_idx],
                        "similarity_score": round(best_score_val, 4)
                    })
                else:
                    results.append({
                        "original": ext_skill,
                        "matched_canonical": None,
                        "similarity_score": round(best_score_val, 4)
                    })

        return results

    def get_matched_skills(self, extracted_skills: List[str]) -> List[str]:
        normalized = self.normalize_skills(extracted_skills)
        # Filter out None and return unique matched canonical skills
        matched = {item["matched_canonical"] for item in normalized if item["matched_canonical"] is not None}
        return list(matched)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    matcher = SkillMatcher(similarity_threshold=0.8)
    
    # Example skills mixing exact matches, slight typos, and Thai translations/variants
    sample_skills = [
        "python",
        "React.js",
        "k8s",
        "Machine Learning",
        "ML",
        "การจัดการโครงการ",  # Project Management in Thai
        "Data Sci",
        "Unknown Skill XYZ"
    ]
    
    print(f"Testing with fallback={matcher.use_fallback}")
    print(f"Input skills: {sample_skills}")
    print("-" * 40)
    
    normalized = matcher.normalize_skills(sample_skills)
    for item in normalized:
        print(f"Original: {item['original']:<20} -> Canonical: {str(item['matched_canonical']):<20} (Score: {item['similarity_score']})")
    
    print("-" * 40)
    final_skills = matcher.get_matched_skills(sample_skills)
    print(f"Final distinct canonical skills: {final_skills}")
