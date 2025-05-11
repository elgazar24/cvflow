import re
import json
import logging
import unicodedata
import os
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from datetime import datetime
from collections import defaultdict

# Optional imports with fallbacks
try:
    from PyPDF2 import PdfReader
except ImportError:
    logging.warning("PyPDF2 not installed. PDF parsing will not be available.")
    PdfReader = None

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    # Download necessary NLTK resources if not already downloaded
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        nltk.download('averaged_perceptron_tagger', quiet=True)
    try:
        nltk.data.find('chunkers/maxent_ne_chunker')
    except LookupError:
        nltk.download('maxent_ne_chunker', quiet=True)
    try:
        nltk.data.find('corpora/words')
    except LookupError:
        nltk.download('words', quiet=True)
    HAS_NLTK = True
except ImportError:
    logging.warning("NLTK not installed. Advanced NLP features will not be available.")
    HAS_NLTK = False

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logging.warning("Spacy model not found. Downloading model...")
        from spacy.cli import download
        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    HAS_SPACY = True
except ImportError:
    logging.warning("spaCy not installed. Advanced NLP features will not be available.")
    HAS_SPACY = False
    nlp = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AdvancedCVParser')


class AdvancedResumeParser:
    """
    An advanced CV/resume parser that accurately extracts structured data from PDF resumes
    using NLP techniques and robust pattern matching.
    """
    
    def __init__(self, debug_mode=False, use_nlp=True, output_dir=None):
        """
        Initialize the parser with configurable options.
        
        Args:
            debug_mode: Enable detailed logging for debugging
            use_nlp: Enable NLP-based enhancements when available
            output_dir: Directory to save intermediate and final outputs
        """
        self.debug_mode = debug_mode
        self.use_nlp = use_nlp and (HAS_NLTK or HAS_SPACY)
        self.output_dir = output_dir
        
        if self.output_dir and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Define section patterns with common variations
        self.section_patterns = {
            'personal_info': r'(^|^.*?\n)((?:[A-Z][a-z]+ )+[A-Z][a-z]+)(?:\s*\n)(.+?(?=\n\s*\n|\n\s*[A-Z]))',
            'objective': r'(?i)(^|\n)\s*(career\s+objective|professional\s+summary|summary|profile|about|objective|career\s+profile|professional\s+profile|career\s+overview|executive\s+summary)\s*(?:\:|\n)',
            'experience': r'(?i)(^|\n)\s*(experience|work\s+history|employment(\s+history)?|professional\s+experience|work\s+experience|career\s+history|professional\s+background)\s*(?:\:|\n)',
            'education': r'(?i)(^|\n)\s*(education|academic|educational\s+background|academic\s+background|educational\s+qualifications|academic\s+qualifications)\s*(?:\:|\n)',
            'skills': r'(?i)(^|\n)\s*(skills|technical\s+skills|technology|technologies|technical\s+expertise|key\s+skills|core\s+competencies|competencies|areas\s+of\s+expertise|areas\s+of\s+strength|professional\s+skills|digital\s+skills)\s*(?:\:|\n)',
            'projects': r'(?i)(^|\n)\s*(projects|project\s+experience|personal\s+projects|professional\s+projects|portfolio|case\s+studies|notable\s+projects)\s*(?:\:|\n)',
            'languages': r'(?i)(^|\n)\s*(languages|language\s+proficiency|language\s+skills|foreign\s+languages)\s*(?:\:|\n)',
            'certifications': r'(?i)(^|\n)\s*(certifications|certificates|qualifications|professional\s+certifications|professional\s+development|accreditations|training)\s*(?:\:|\n)',
            'achievements': r'(?i)(^|\n)\s*(achievements|honors|awards|recognitions|accomplishments|accolades)\s*(?:\:|\n)',
            'publications': r'(?i)(^|\n)\s*(publications|research|papers|articles|published\s+work)\s*(?:\:|\n)',
            'interests': r'(?i)(^|\n)\s*(interests|hobbies|activities|personal\s+interests|extracurricular\s+activities)\s*(?:\:|\n)',
            'references': r'(?i)(^|\n)\s*(references|referees|recommendations|testimonials|professional\s+references)\s*(?:\:|\n)',
            'volunteer': r'(?i)(^|\n)\s*(volunteer(\s+experience)?|community\s+service|charity\s+work|pro\s+bono|community\s+involvement)\s*(?:\:|\n)',
            'leadership': r'(?i)(^|\n)\s*(leadership(\s+experience)?|leadership\s+roles|leadership\s+positions|management\s+experience)\s*(?:\:|\n)',
            'coursework': r'(?i)(^|\n)\s*(coursework|courses|relevant\s+courses|relevant\s+coursework|key\s+courses)\s*(?:\:|\n)',
            'contact': r'(?i)(^|\n)\s*(contact|contact\s+details|contact\s+information|personal\s+details|personal\s+information)\s*(?:\:|\n)',
        }
        
        # Define regex patterns for extracting common information
        self.patterns = {
            'email': r'[\w.+-]+@[\w-]+\.[\w.-]+',
            'phone': r'(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+\d{1,3}[-\s]?\d{1,14})',
            'linkedin': r'(?:linkedin\.com/in/|linkedin\.com/profile/view\?id=|linkedin\.com/pub/)([a-zA-Z0-9_-]+)',
            'github': r'(?:github\.com/)([a-zA-Z0-9_-]+)',
            'website': r'(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]{0,62}(?:\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\.?)',
            'date_range': r'(?:(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|(?:\d{1,2}/\d{1,2}/|)\d{4})',            'date_range_short': r'\d{4}\s*(?:to|-|–|—)\s*(?:\d{4}|Present|Current|Now|Ongoing|Today)',
            'location': r'(?:\n|^| )([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z]{2}|[A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z][a-z]+|[A-Z][a-z]+\s+[A-Z][a-z]+)',            'education_degree': r'(?:Bachelor|Master|Ph\.?D\.?|Doctorate|B\.S\.|M\.S\.|M\.B\.A\.|B\.Tech|M\.Tech|B\.A\.|M\.A\.|B\.Eng\.|M\.Eng\.|Associate|A\.A\.|B\.Sc\.|M\.Sc\.|B\.Com\.|M\.Com\.|LL\.B\.|J\.D\.)(?:\s+of\s+|\s+in\s+|\'\s+)?(?:Science|Arts|Engineering|Technology|Business|Administration|Computer|Finance|Management|Law|Medicine|Education|Economics|Psychology|Philosophy|Communication|Marketing|Accounting|Information|Systems)?',
            'gpa': r'(?:GPA|Grade Point Average)(?:\s+of|\:)?\s+(\d+\.\d+)(?:/\d+\.\d+)?',
            'bullet_point': r'(?:^|\n)(?:\s*[•●■◦○❖✦★✓-]|\s*\d+\.\s+|\s*\(\d+\)\s+|\s*[A-Z]\.|\s*[ivxIVX]+\.\s+|\s*[a-z]\)\s+)(.+?)(?=\n|$)',
            'bullet_point_start': r'(?:^|\n)(?:\s*[•●■◦○❖✦★✓-]|\s*\d+\.\s+|\s*\(\d+\)\s+|\s*[A-Z]\.|\s*[ivxIVX]+\.\s+|\s*[a-z]\)\s+)',
            'name': r'^([A-Z][a-z]+(?:[\s\'-][A-Z][a-z]+)+)'
        }
        
        # Compile common technology and skill keywords
        self.tech_keywords = self._compile_tech_keywords()
        self.skill_categories = self._compile_skill_categories()
        
        # Define common job titles and roles for better extraction
        self.job_titles = self._compile_job_titles()
        
        # Common education institutions and degrees
        self.education_keywords = self._compile_education_keywords()
        
        # Language database with ISO codes and proficiency levels
        self.language_data = self._compile_language_data()
        
        # Define section content templates for structured output
        self.section_templates = {
            'personal_info': {
                'name': '',
                'email': '',
                'phone': '',
                'location': '',
                'linkedin': '',
                'github': '',
                'website': '',
                'image': ''
            },
            'education': {
                'degree': '',
                'university': '',
                'startDate': '',
                'endDate': '',
                'gpa': '',
                'certificate': 'N/A',
                'coursework': '',
                'location': ''
            },
            'experience': {
                'role': '',
                'company': '',
                'location': '',
                'startDate': '',
                'endDate': '',
                'responsibilities': []
            },
            'project': {
                'title': '',
                'github_link': '',
                'timeframe': '',
                'technologies': [],
                'responsibilities': []
            }
        }
    
    ################################################################################
    # Main parsing methods
    ################################################################################
    
    def parse_resume(self, file_path: str, output_format: str = 'json') -> Union[Dict, str]:
        """
        Parse a resume file and return structured data.
        
        Args:
            file_path: Path to the resume file (PDF supported)
            output_format: Format of output ('json', 'dict', or 'text')
            
        Returns:
            Structured resume data in requested format
        """
        logger.info(f"Starting to parse resume: {file_path}")
        
        try:
            # Extract text from file based on file extension
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                if PdfReader is None:
                    raise ImportError("PyPDF2 is required for PDF parsing but not installed")
                text = self._extract_text_from_pdf(file_path)
            elif file_extension in ['.txt', '.text']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Process and return the parsed data
            return self.parse_text(text, output_format)
            
        except Exception as e:
            logger.error(f"Error parsing resume: {e}", exc_info=True)
            # Return basic structure in case of error
            empty_result = {
                "personal_info": {},
                "sections": {},
                "content": {
                    "objective": "",
                    "education": [],
                    "experience": [],
                    "projects": [],
                    "languages": [],
                    "technologies": [],
                    "certifications": [],
                    "skills": []
                }
            }
            
            if output_format == 'json':
                return json.dumps(empty_result, indent=2)
            return empty_result

    def parse_text(self, text: str, output_format: str = 'json') -> Union[Dict, str]:
        """
        Parse resume text and return structured data.
        
        Args:
            text: Resume text content
            output_format: Format of output ('json', 'dict', or 'text')
            
        Returns:
            Structured resume data in requested format
        """
        try:
            # Preprocess the text
            text = self._preprocess_text(text)
            
            if self.debug_mode and self.output_dir:
                # Save extracted text for debugging
                with open(os.path.join(self.output_dir, "extracted_text.txt"), "w", encoding="utf-8") as f:
                    f.write(text)
                logger.debug(f"Extracted text written to extracted_text.txt")
            
            # Apply NLP preprocessing if enabled
            if self.use_nlp:
                text = self._apply_nlp_preprocessing(text)
            
            # Identify sections in the text
            sections = self._identify_sections(text)
            
            if self.debug_mode and self.output_dir:
                # Save sections for debugging
                with open(os.path.join(self.output_dir, "sections.json"), "w", encoding="utf-8") as f:
                    json.dump({k: v for k, v in sections.items()}, f, indent=2)
                logger.debug(f"Sections written to sections.json")
            
            # Parse sections into structured data
            parsed_data = {
                "personal_info": self._parse_personal_info(text, sections),
                "sections": self._detect_sections_presence(sections),
                "content": {
                    "objective": self._parse_objective(sections.get('objective', '')),
                    "education": self._parse_education(sections.get('education', ''), text),
                    "experience": self._parse_experience(sections.get('experience', ''), text),
                    "projects": self._parse_projects(sections.get('projects', ''), text),
                    "languages": self._parse_languages(sections.get('languages', ''), text),
                    "technologies": self._parse_technologies(sections.get('skills', ''), text),
                    "certifications": self._parse_certifications(sections.get('certifications', ''), text),
                    "skills": self._extract_skills(text, sections)
                }
            }
            
            # Post-processing: remove empty lists and dictionaries
            parsed_data = self._clean_parsed_data(parsed_data)
            
            logger.info("Resume parsing completed successfully")
            
            # Return in requested format
            if output_format == 'json':
                return json.dumps(parsed_data, indent=2)
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing text: {e}", exc_info=True)
            # Return basic structure in case of error
            empty_result = {
                "personal_info": {},
                "sections": {},
                "content": {
                    "objective": "",
                    "education": [],
                    "experience": [],
                    "projects": [],
                    "languages": [],
                    "technologies": [],
                    "certifications": [],
                    "skills": []
                }
            }
            
            if output_format == 'json':
                return json.dumps(empty_result, indent=2)
            return empty_result
    
    ################################################################################
    # Text extraction and preprocessing methods
    ################################################################################
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file with error handling."""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            
            # Handle empty text
            if not text.strip():
                logger.warning("PDF text extraction returned empty text. Trying alternative method.")
                # Implement alternative extraction method if needed
                
            # Normalize text
            text = self._normalize_text(text)
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}", exc_info=True)
            raise
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing excessive whitespace and normalizing Unicode."""
        # Normalize Unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove page numbers
        text = re.sub(r'\n\s*\d+\s*\n', '\n\n', text)
        
        # Normalize bullet points
        text = re.sub(r'[•●■◦○❖✦★✓]', '•', text)
        
        return text.strip()
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better parsing."""
        # Handle special characters and formatting issues
        text = self._normalize_text(text)
        
        # Remove headers and footers (common in PDFs)
        # This is a simplified approach - more sophisticated header/footer detection may be needed
        lines = text.split('\n')
        if len(lines) > 4:
            # Check if first or last lines contain page numbers, dates, etc.
            header_footer_patterns = [
                r'^\s*Page\s+\d+\s*$',
                r'^\s*\d+\s*of\s*\d+\s*$',
                r'^\s*Resume\s*$',
                r'^\s*CV\s*$',
                r'^\s*Curriculum\s+Vitae\s*$'
            ]
            
            filtered_lines = []
            for i, line in enumerate(lines):
                # Skip lines that match header/footer patterns
                if i < 2 or i >= len(lines) - 2:  # Check only first and last two lines
                    if any(re.match(pattern, line) for pattern in header_footer_patterns):
                        continue
                filtered_lines.append(line)
            
            text = '\n'.join(filtered_lines)
        
        # Remove unnecessary characters
        text = re.sub(r'[\u2022\u2023\u2043\u204C\u204D\u2219\u25D8\u25E6\u2619\u2765\u2767\u29BE\u29BF]', '•', text)
        
        # Ensure sections are properly separated
        for section_pattern in self.section_patterns.values():
            text = re.sub(section_pattern, lambda m: f"\n\n{m.group(0)}", text)
        
        # Normalize section headers (ensure they're followed by newline)
        for pattern in self.section_patterns.values():
            text = re.sub(pattern, lambda m: m.group(0) if m.group(0).endswith('\n') else m.group(0) + '\n', text)
        
        return text
    
    def _apply_nlp_preprocessing(self, text: str) -> str:
        """Apply NLP preprocessing if available."""
        if not self.use_nlp:
            return text
            
        try:
            if HAS_SPACY and nlp:
                # Use spaCy for NLP preprocessing
                doc = nlp(text[:100000])  # Limit to prevent memory issues with very large texts
                
                # Entity recognition for better section detection
                entities = [(ent.text, ent.label_) for ent in doc.ents]
                
                # Add annotations for recognized entities
                for entity, label in entities:
                    if label in ('PERSON', 'ORG', 'GPE', 'LOC', 'DATE'):
                        # Mark important entities in text for better recognition
                        # This is subtle and doesn't modify the actual text structure
                        text = text.replace(entity, entity)  # Placeholder, actual NLP use is handled in specific parsers
            
            elif HAS_NLTK:
                # Use NLTK for preprocessing
                sentences = sent_tokenize(text)
                tokens = [word_tokenize(sentence) for sentence in sentences]
                
                # POS tagging for better entity recognition
                pos_tags = [nltk.pos_tag(sentence_tokens) for sentence_tokens in tokens]
                
                # Named Entity Recognition
                for i, sentence_pos in enumerate(pos_tags):
                    if i < len(sentences):  # Safety check
                        chunked = nltk.ne_chunk(sentence_pos)
                        # Extract named entities (subtle preprocessing)
                        # No actual text modification, just analysis for later use
                        
            return text
            
        except Exception as e:
            logger.warning(f"Error in NLP preprocessing: {e}")
            return text
    
    ################################################################################
    # Section identification methods
    ################################################################################
    
    def _identify_sections(self, text: str) -> Dict[str, str]:
        """
        Identify and extract sections from the resume text.
        
        Args:
            text: Full text from resume
            
        Returns:
            Dictionary with section names as keys and section content as values
        """
        sections = {}
        section_boundaries = []
        
        # Find all section headings and their positions
        for section_name, pattern in self.section_patterns.items():
            for match in re.finditer(pattern, text, re.MULTILINE):
                # Store the starting position of the section heading
                position = match.end()
                section_boundaries.append((position, section_name))
        
        # Sort boundaries by position
        section_boundaries.sort()
        
        # Extract content between section boundaries
        for i, (start_pos, section_name) in enumerate(section_boundaries):
            # Get end position (either next section or end of text)
            end_pos = section_boundaries[i+1][0] if i < len(section_boundaries) - 1 else len(text)
            
            # Extract section content
            section_content = text[start_pos:end_pos].strip()
            
            # Store the section content
            sections[section_name] = section_content
            
            if self.debug_mode:
                logger.debug(f"Found section '{section_name}' with {len(section_content)} characters")
        
        # Apply NLP-based section detection for unlabeled content
        if self.use_nlp and (HAS_SPACY or HAS_NLTK):
            sections = self._enhance_section_detection(text, sections)
        
        # Handle special cases where sections might be incorrectly identified
        sections = self._refine_sections(sections, text)
        
        # If no sections were found, try to extract basic info
        if not sections and len(text) > 0:
            logger.warning("No sections identified. Treating entire document as unstructured text.")
            sections = self._extract_implicit_sections(text)
        
        return sections
    
    def _enhance_section_detection(self, text: str, sections: Dict[str, str]) -> Dict[str, str]:
        """Use NLP to enhance section detection."""
        try:
            # Only process if a significant portion of the text hasn't been assigned to sections
            total_text_len = len(text)
            assigned_text_len = sum(len(content) for content in sections.values())
            
            if assigned_text_len / total_text_len < 0.7:
                unassigned_text = text
                for section_content in sections.values():
                    unassigned_text = unassigned_text.replace(section_content, '')
                
                # Use NLP to identify additional sections
                if HAS_SPACY and nlp:
                    doc = nlp(unassigned_text[:100000])  # Limit size to prevent memory issues
                    
                    # Identify potential sections based on linguistic patterns
                    for para in doc.sents:
                        para_text = para.text.strip()
                        if len(para_text) > 50:  # Only consider substantial paragraphs
                            # Check for education keywords
                            if any(keyword in para_text.lower() for keyword in ['university', 'college', 'degree', 'graduated']):
                                if 'education' not in sections:
                                    sections['education'] = para_text
                            
                            # Check for experience keywords
                            elif any(keyword in para_text.lower() for keyword in ['worked', 'managed', 'led', 'developed', 'responsible']):
                                if 'experience' not in sections:
                                    sections['experience'] = sections.get('experience', '') + '\n' + para_text
            
            return sections
            
        except Exception as e:
            logger.warning(f"Error in NLP section enhancement: {e}")
            return sections
    
    def _refine_sections(self, sections: Dict[str, str], full_text: str) -> Dict[str, str]:
        """Refine and correct section assignments."""
        refined_sections = {}
        
        # Handle overlapping or duplicate sections
        seen_content = set()
        for name, content in sections.items():
            # Skip empty sections
            if not content.strip():
                continue
                
            # Check if content is already assigned to another section
            content_hash = hash(content.strip())
            if content_hash in seen_content:
                continue
            
            seen_content.add(content_hash)
            refined_sections[name] = content
        
        # Handle common misidentifications
        if 'objective' in refined_sections and 'summary' in refined_sections:
            # Often these are the same section with different names
            # Keep the longer one
            if len(refined_sections['objective']) >= len(refined_sections['summary']):
                refined_sections.pop('summary')
            else:
                refined_sections.pop('objective')
                refined_sections['objective'] = refined_sections.pop('summary')
        
        # Ensure education and experience sections are properly identified
        if 'education' not in refined_sections:
            # Try to find education section based on keywords
            education_keywords = ['university', 'college', 'degree', 'bachelor', 'master', 'phd', 'b.s.', 'm.s.', 'gpa']
            education_section = self._find_section_by_keywords(full_text, education_keywords)
            if education_section:
                refined_sections['education'] = education_section
        
        if 'experience' not in refined_sections:
            # Try to find experience section based on keywords
            experience_keywords = ['experience', 'work history', 'employment', 'job', 'position', 'role']
            experience_section = self._find_section_by_keywords(full_text, experience_keywords)
            if experience_section:
                refined_sections['experience'] = experience_section
        
        return refined_sections
    
    def _find_section_by_keywords(self, text: str, keywords: List[str]) -> str:
        """Find a section in text based on keywords."""
        lines = text.split('\n')
        section_start = -1
        section_end = -1
        
        # Find starting line containing one of the keywords
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in keywords):
                section_start = i
                break
        
        # If section start found, find end (next section header or end of text)
        if section_start >= 0:
            for i in range(section_start + 1, len(lines)):
                # Check if this line could be a section header
                if re.match(r'^[A-Z][A-Za-z\s]+:?\s*$', lines[i].strip()):
                    section_end = i
                    break
            
            # If no end found, use the end of text
            if section_end == -1:
                section_end = len(lines)
            
            return '\n'.join(lines[section_start:section_end])
        
        return ""
    
    def _extract_implicit_sections(self, text: str) -> Dict[str, str]:
        """Extract implicit sections from unstructured text."""
        sections = {}
        
        # Try to identify key sections from unstructured text
        if re.search(r'experience|work|job|position', text, re.IGNORECASE):
            sections['experience'] = text
        if re.search(r'education|university|college|school|degree', text, re.IGNORECASE):
            sections['education'] = text
        if re.search(r'skill|proficiency|expertise', text, re.IGNORECASE):
            sections['skills'] = text
        if re.search(r'project|portfolio', text, re.IGNORECASE):
            sections['projects'] = text
        if re.search(r'objective|summary|profile', text, re.IGNORECASE):
            sections['objective'] = text
        
        return sections
    
    def _detect_sections_presence(self, sections: Dict[str, str]) -> Dict[str, bool]:
        """
        Detect the presence of each section in the resume.
        
        Args:
            sections: Dictionary of identified sections
            
        Returns:
            Dictionary indicating presence of each section
        """
        section_presence = {}
        for section_name in self.section_patterns.keys():
            section_presence[section_name] = section_name in sections and bool(sections[section_name].strip())
        return section_presence
    
    ################################################################################
    # Section parsing methods
    ################################################################################
    
    def _parse_personal_info(self, text: str, sections: Dict[str, str]) -> Dict[str, str]:
        """
        Extract personal information like name, email, phone, etc.
        
        Args:
            text: Full resume text
            sections: Dictionary of identified sections
            
        Returns:
            Dictionary of personal information
        """
        info = self.section_templates['personal_info'].copy()
        
        # Check if there's a dedicated contact or personal info section
        contact_text = sections.get('contact', text[:1000])  # Use first 1000 chars if no dedicated section
        personal_text = sections.get('personal_info', contact_text)
        
        # Combine both sections for better extraction
        search_text = personal_text + "\n" + contact_text + "\n" + text[:1000]
        
        # Extract email
        email_match = re.search(self.patterns['email'], search_text)
        if email_match:
            info['email'] = email_match.group(0)
        
        # Extract phone
        phone_match = re.search(self.patterns['phone'], search_text)
        if phone_match:
            # Clean and format phone number
            phone = phone_match.group(0)
            phone = re.sub(r'[^0-9+]', '', phone)  # Keep only digits and + symbol
            info['phone'] = phone
        
        # Extract LinkedIn
        linkedin_match = re.search(self.patterns['linkedin'], search_text)
        if linkedin_match:
            info['linkedin'] = f"linkedin.com/in/{linkedin_match.group(1)}"
        
        # Extract GitHub
        github_match = re.search(self.patterns['github'], search_text)
        if github_match:
            info['github'] = f"github.com/{github_match.group(1)}"
        
        # Extract website
        website_match = re.search(self.patterns['website'], search_text)
        if website_match and not any(domain in website_match.group(0) for domain in ['linkedin.com', 'github.com']):
            info['website'] = website_match.group(0)
        
        # Extract name using various approaches
        name = ""
        
        # Method 1: Look for name at the beginning of the document
        name_match = re.search(self.patterns['name'], text[:500])
        if name_match:
            name = name_match.group(1)
        
        # Method 2: Use NLP if available
        if not name and self.use_nlp:
            if HAS_SPACY and nlp:
                doc = nlp(text[:1000])
                for ent in doc.ents:
                    if ent.label_ == 'PERSON':
                        name = ent.text
                        break
            elif HAS_NLTK:
                tokens = word_tokenize(text[:1000])
                pos_tags = nltk.pos_tag(tokens)
                chunked = nltk.ne_chunk(pos_tags)
                for chunk in chunked:
                    if hasattr(chunk, 'label') and chunk.label() == 'PERSON':
                        name = ' '.join(c[0] for c in chunk)
                        break
        
        # Method 3: Look for patterns like "Name: John Doe"
        if not name:
            name_pattern = r'(?i)(?:^|\n)(?:name|full name|candidate)[:\s]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)'
            name_match = re.search(name_pattern, text[:1000])
            if name_match:
                name = name_match.group(1)
        
        info['name'] = name
        
        # Extract location
        location_match = re.search(self.patterns['location'], search_text)
        if location_match:
            info['location'] = location_match.group(0).strip()
        
        return info
    
    def _parse_objective(self, text: str) -> str:
        """
        Parse objective or summary section.
        
        Args:
            text: Objective section text
            
        Returns:
            Cleaned and formatted objective text
        """
        if not text:
            return ""
        
        # Remove section title if present
        text = re.sub(r'(?i)^(?:career\s+objective|professional\s+summary|summary|profile|about|objective|career\s+profile)[\s:]*', '', text)
        
        # Split by newlines and keep first paragraph or bullet points
        paragraphs = text.split('\n\n')
        objective = paragraphs[0] if paragraphs else ""
        
        # Clean up any bullet points
        objective = re.sub(self.patterns['bullet_point_start'], '', objective)
        
        # Limit length and clean up
        if len(objective) > 500:
            # Try to find a good breaking point
            sentences = re.split(r'(?<=[.!?])\s+', objective[:500])
            objective = ' '.join(sentences[:-1]) if len(sentences) > 1 else objective[:500]
        
        return objective.strip()
    
    def _parse_education(self, text: str, full_text: str) -> List[Dict[str, Any]]:
        """
        Parse education section into structured format.
        
        Args:
            text: Education section text
            full_text: Full resume text for fallback
            
        Returns:
            List of education entries
        """
        education_entries = []
        
        if not text:
            # Try to find education information in full text if no dedicated section
            education_keywords = ['degree', 'university', 'college', 'bachelor', 'master', 'phd', 'gpa']
            for paragraph in full_text.split('\n\n'):
                if any(keyword.lower() in paragraph.lower() for keyword in education_keywords):
                    text = paragraph
                    break
            
            if not text:
                return education_entries
        
        # Remove section header
        text = re.sub(r'(?i)^education[\s:]*', '', text)
        
        # Split text into education entries
        entries = self._split_section_into_entries(text)
        
        for entry in entries:
            education_item = self.section_templates['education'].copy()
            
            # Extract degree
            degree_match = re.search(self.patterns['education_degree'], entry)
            if degree_match:
                education_item['degree'] = degree_match.group(0).strip()
            
            # Extract university
            university_pattern = r'(?:university|college|institute|school) (?:of|for)? [A-Z][a-zA-Z\s,]+'
            university_match = re.search(university_pattern, entry, re.IGNORECASE)
            if university_match:
                education_item['university'] = university_match.group(0).strip()
            else:
                # Try to find university name using common keywords
                lines = entry.split('\n')
                for line in lines:
                    if any(kw in line.lower() for kw in ['university', 'college', 'institute', 'school']) and line.strip():
                        education_item['university'] = line.strip()
                        break
            
            # Extract date range
            date_match = re.search(self.patterns['date_range'], entry)
            if date_match:
                dates = date_match.group(0).split('to')
                if len(dates) == 2:
                    education_item['startDate'] = dates[0].strip()
                    education_item['endDate'] = dates[1].strip()
                else:
                    # Try shorter date pattern (e.g., "2018-2022")
                    date_match = re.search(self.patterns['date_range_short'], entry)
                    if date_match:
                        dates = re.split(r'[-–—]', date_match.group(0))
                        if len(dates) == 2:
                            education_item['startDate'] = dates[0].strip()
                            education_item['endDate'] = dates[1].strip()
            
            # Extract GPA
            gpa_match = re.search(self.patterns['gpa'], entry)
            if gpa_match:
                education_item['gpa'] = gpa_match.group(1)
            
            # Extract location
            location_match = re.search(self.patterns['location'], entry)
            if location_match:
                education_item['location'] = location_match.group(0).strip()
            
            # Extract coursework
            coursework_pattern = r'(?i)(?:relevant coursework|key courses|courses)[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)'
            coursework_match = re.search(coursework_pattern, entry)
            if coursework_match:
                education_item['coursework'] = coursework_match.group(1).strip()
            
            # Only add if we have at least degree or university
            if education_item['degree'] or education_item['university']:
                education_entries.append(education_item)
        
        return education_entries
    
    def _parse_experience(self, text: str, full_text: str) -> List[Dict[str, Any]]:
        """
        Parse work experience into structured format.
        
        Args:
            text: Experience section text
            full_text: Full resume text for fallback
            
        Returns:
            List of experience entries
        """
        experience_entries = []
        
        if not text:
            # Try to find experience information in full text
            experience_keywords = ['experience', 'work history', 'employment']
            for paragraph in full_text.split('\n\n'):
                if any(keyword.lower() in paragraph.lower() for keyword in experience_keywords):
                    text = paragraph
                    break
            
            if not text:
                return experience_entries
        
        # Remove section header
        text = re.sub(r'(?i)^(?:experience|work history|employment)[\s:]*', '', text)
        
        # Split text into experience entries
        entries = self._split_section_into_entries(text)
        
        for entry in entries:
            experience_item = self.section_templates['experience'].copy()
            
            # Extract company and role
            lines = entry.split('\n')
            if lines:
                # Company and role typically appear at the beginning
                potential_role_company = lines[0].strip()
                
                # Check for common patterns like "Job Title | Company" or "Job Title at Company"
                separator_pattern = r'(?:\s+at\s+|\s+[|@]\s+|\s+\-\s+|\s*,\s+|\s+\(|\s+\-\s+)'
                parts = re.split(separator_pattern, potential_role_company, maxsplit=1)
                
                if len(parts) == 2:
                    experience_item['role'] = parts[0].strip()
                    # Clean up company name (remove trailing parentheticals like "(Remote)")
                    experience_item['company'] = re.sub(r'\s*\([^)]*\)\s*$', '', parts[1].strip())
                else:
                    # Check if this is a known job title
                    job_title_match = False
                    for title in self.job_titles:
                        if title.lower() in potential_role_company.lower():
                            experience_item['role'] = title
                            # Assume remainder is company name
                            experience_item['company'] = potential_role_company.replace(title, '').strip(',- ')
                            job_title_match = True
                            break
                    
                    if not job_title_match:
                        # Default: use first line as role if no clear parsing
                        experience_item['role'] = potential_role_company
                        
                        # Try to extract company from second line
                        if len(lines) > 1:
                            experience_item['company'] = lines[1].strip()
            
            # Extract date range
            date_match = re.search(self.patterns['date_range'], entry)
            if date_match:
                date_text = date_match.group(0)
                
                # Handle different date formats
                if 'to' in date_text:
                    dates = date_text.split('to')
                elif '-' in date_text:
                    dates = date_text.split('-')
                elif '–' in date_text:
                    dates = date_text.split('–')
                elif '—' in date_text:
                    dates = date_text.split('—')
                else:
                    dates = [date_text, 'Present']
                
                if len(dates) == 2:
                    experience_item['startDate'] = dates[0].strip()
                    experience_item['endDate'] = dates[1].strip()
            
            # Extract location
            location_match = re.search(self.patterns['location'], entry)
            if location_match:
                experience_item['location'] = location_match.group(0).strip()
            
            # Extract responsibilities (bullet points)
            responsibilities = []
            for bullet_match in re.finditer(self.patterns['bullet_point'], entry):
                responsibility = bullet_match.group(1).strip()
                if responsibility:
                    responsibilities.append(responsibility)
            
            # If no bullet points found, try to use remaining lines as responsibilities
            if not responsibilities and len(lines) > 2:
                for line in lines[2:]:
                    line = line.strip()
                    if line and not re.search(self.patterns['date_range'], line) and line != experience_item['location']:
                        responsibilities.append(line)
            
            experience_item['responsibilities'] = responsibilities
            
            # Only add if we have at least role or company
            if experience_item['role'] or experience_item['company']:
                experience_entries.append(experience_item)
        
        return experience_entries
    
    def _parse_projects(self, text: str, full_text: str) -> List[Dict[str, Any]]:
        """
        Parse projects section into structured format.
        
        Args:
            text: Projects section text
            full_text: Full resume text for fallback
            
        Returns:
            List of project entries
        """
        project_entries = []
        
        if not text:
            # Try to find project information in full text
            project_keywords = ['project', 'portfolio', 'application', 'developed', 'created', 'built']
            for paragraph in full_text.split('\n\n'):
                if any(keyword.lower() in paragraph.lower() for keyword in project_keywords):
                    text = paragraph
                    break
            
            if not text:
                return project_entries
        
        # Remove section header
        text = re.sub(r'(?i)^(?:projects|project experience)[\s:]*', '', text)
        
        # Split text into project entries
        entries = self._split_section_into_entries(text)
        
        for entry in entries:
            project_item = self.section_templates['project'].copy()
            
            # Extract project title
            lines = entry.split('\n')
            if lines:
                project_item['title'] = lines[0].strip()
            
            # Extract GitHub link
            github_match = re.search(r'github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+', entry)
            if github_match:
                project_item['github_link'] = github_match.group(0)
            
            # Extract timeframe
            date_match = re.search(self.patterns['date_range'], entry)
            if date_match:
                project_item['timeframe'] = date_match.group(0)
            
            # Extract technologies used
            tech_keywords = []
            for keyword in self.tech_keywords:
                if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', entry.lower()):
                    tech_keywords.append(keyword)
            project_item['technologies'] = tech_keywords
            
            # Extract responsibilities/description (bullet points)
            responsibilities = []
            for bullet_match in re.finditer(self.patterns['bullet_point'], entry):
                responsibility = bullet_match.group(1).strip()
                if responsibility:
                    responsibilities.append(responsibility)
            
            # If no bullet points found, try to use remaining lines as description
            if not responsibilities and len(lines) > 1:
                for line in lines[1:]:
                    line = line.strip()
                    if line and not re.search(self.patterns['date_range'], line) and line != project_item['github_link']:
                        responsibilities.append(line)
            
            project_item['responsibilities'] = responsibilities
            
            # Only add if we have at least a title
            if project_item['title']:
                project_entries.append(project_item)
        
        return project_entries
    
    def _parse_languages(self, text: str, full_text: str) -> List[Dict[str, str]]:
        """
        Parse languages section into structured format.
        
        Args:
            text: Languages section text
            full_text: Full resume text for fallback
            
        Returns:
            List of language entries with proficiency levels
        """
        languages = []
        
        if not text:
            # Try to find language information in full text
            language_keywords = ['language', 'proficiency', 'fluent', 'native', 'speak']
            for paragraph in full_text.split('\n\n'):
                if any(keyword.lower() in paragraph.lower() for keyword in language_keywords):
                    text = paragraph
                    break
            
            if not text:
                return languages
        
        # Known languages to look for
        known_languages = ['english', 'spanish', 'french', 'german', 'italian', 'russian', 'chinese', 'japanese', 
                          'korean', 'arabic', 'portuguese', 'hindi', 'bengali', 'dutch', 'turkish', 'polish',
                          'vietnamese', 'thai', 'swedish', 'romanian', 'greek', 'czech', 'danish', 'finnish',
                          'hebrew', 'hungarian', 'norwegian']
        
        # Proficiency levels
        proficiency_levels = ['native', 'fluent', 'proficient', 'intermediate', 'advanced', 'beginner', 'basic',
                             'elementary', 'professional', 'working', 'limited', 'conversational', 'business',
                             'mother tongue', 'c2', 'c1', 'b2', 'b1', 'a2', 'a1']
        
        # Look for patterns like "Language: Proficiency" or "Language (Proficiency)"
        language_pattern = r'(?i)({})\s*(?::|\s*[-:]\s*|\s*\(\s*|\s+)([^,;\n\)]+)'.format('|'.join(known_languages))
        
        for match in re.finditer(language_pattern, text):
            language = match.group(1).capitalize()
            proficiency = match.group(2).strip().lower()
            
            # Check if the proficiency description contains a known level
            level = None
            for plevel in proficiency_levels:
                if plevel in proficiency:
                    level = plevel.capitalize()
                    break
            
            if not level:
                # If no level found, check if it's a CEFR level (A1-C2)
                cefr_match = re.search(r'(?i)(a1|a2|b1|b2|c1|c2)', proficiency)
                if cefr_match:
                    level = cefr_match.group(1).upper()
                else:
                    level = "Proficient"  # Default level
            
            languages.append({
                "language": language,
                "proficiency": level
            })
        
        # If no matches found with the pattern, look for language names and try to infer proficiency
        if not languages:
            for language in known_languages:
                if re.search(r'\b' + re.escape(language) + r'\b', text.lower()):
                    # Try to find a nearby proficiency level
                    context = re.search(r'.{0,30}' + re.escape(language) + r'.{0,30}', text.lower())
                    level = "Proficient"  # Default
                    
                    if context:
                        for plevel in proficiency_levels:
                            if plevel in context.group(0):
                                level = plevel.capitalize()
                                break
                    
                    languages.append({
                        "language": language.capitalize(),
                        "proficiency": level
                    })
        
        return languages
    
    def _parse_technologies(self, text: str, full_text: str) -> List[str]:
        """
        Parse technologies and technical skills.
        
        Args:
            text: Skills section text
            full_text: Full resume text for fallback
            
        Returns:
            List of identified technologies and technical skills
        """
        technologies = set()
        
        # Search text options
        search_texts = [text, full_text] if text else [full_text]
        
        for search_text in search_texts:
            # Extract technologies using predefined list
            for tech in self.tech_keywords:
                if re.search(r'\b' + re.escape(tech.lower()) + r'\b', search_text.lower()):
                    technologies.add(tech)
            
            # Extract skill lists
            skill_lists = re.finditer(r'(?i)(skills|technologies|technical|programming|software)(?:[:\s])(.*?)(?=\n\n|\n[A-Z]|$)', search_text)
            for skill_list in skill_lists:
                skill_text = skill_list.group(2)
                
                # Try to extract comma-separated values or bullet points
                items = re.split(r',|\n|•', skill_text)
                for item in items:
                    item = item.strip()
                    if item and len(item) > 1:
                        # Check against our tech keywords
                        for tech in self.tech_keywords:
                            if tech.lower() == item.lower() or tech.lower() in item.lower().split():
                                technologies.add(tech)
        
        return list(technologies)
    
    def _parse_certifications(self, text: str, full_text: str) -> List[Dict[str, str]]:
        """
        Parse certifications section.
        
        Args:
            text: Certifications section text
            full_text: Full resume text for fallback
            
        Returns:
            List of certification entries
        """
        certifications = []
        
        if not text:
            # Try to find certification information in full text
            cert_keywords = ['certification', 'certificate', 'certified', 'license', 'accreditation']
            for paragraph in full_text.split('\n\n'):
                if any(keyword.lower() in paragraph.lower() for keyword in cert_keywords):
                    text = paragraph
                    break
            
            if not text:
                return certifications
        
        # Look for certification entries
        cert_patterns = [
            # Pattern: Certification Name (Issuer, Date)
            r'(?i)([A-Za-z0-9\s\'\",&.®™\-]+)\s*(?:\(|\s*-\s*)([A-Za-z\s]+)(?:,\s*|\s*-\s*)(\w+\s*\d{4}|\d{4})',
            # Pattern: Certification Name - Issuer - Date
            r'(?i)([A-Za-z0-9\s\'\",&.®™\-]+)\s*(?:-|–|—)\s*([A-Za-z\s]+)\s*(?:-|–|—)\s*(\w+\s*\d{4}|\d{4})',
            # Pattern: Certification Name, Issuer, Date
            r'(?i)([A-Za-z0-9\s\'\",&.®™\-]+),\s*([A-Za-z\s]+),\s*(\w+\s*\d{4}|\d{4})',
            # Pattern: Certification Name
            r'(?i)(?:^|\n|\s*•\s*)([A-Za-z0-9\s\'\",&.®™\-]{5,}?)(?:$|\n)'
        ]
        
        for pattern in cert_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                groups = match.groups()
                
                if len(groups) >= 3:
                    cert_name = groups[0].strip()
                    issuer = groups[1].strip()
                    date = groups[2].strip()
                    
                    certifications.append({
                        "name": cert_name,
                        "issuer": issuer,
                        "date": date
                    })
                elif len(groups) >= 1:
                    cert_name = groups[0].strip()
                    
                    # Try to find issuer in the same line or next line
                    if " - " in cert_name:
                        parts = cert_name.split(" - ")
                        cert_name = parts[0].strip()
                        issuer = parts[1].strip() if len(parts) > 1 else "Unknown"
                    else:
                        issuer = "Unknown"
                    
                    # Look for a date near the certification
                    date_match = re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|\d{4}', 
                                          match.group(0))
                    date = date_match.group(0) if date_match else "Unknown"
                    
                    certifications.append({
                        "name": cert_name,
                        "issuer": issuer,
                        "date": date
                    })
        
        # If no certifications found with patterns, look for bullet point entries
        if not certifications:
            bullet_matches = re.finditer(self.patterns['bullet_point'], text)
            
            for bullet_match in bullet_matches:
                item = bullet_match.group(1).strip()
                if item and len(item) > 5:
                    # Look for certification keywords
                    if any(keyword in item.lower() for keyword in ['certification', 'certificate', 'certified']):
                        certifications.append({
                            "name": item,
                            "issuer": "Unknown",
                            "date": "Unknown"
                        })
        
        return certifications
    
    def _extract_skills(self, text: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extract and categorize skills from resume.
        
        Args:
            text: Full resume text
            sections: Dictionary of identified sections
            
        Returns:
            List of skill categories with skill lists
        """
        all_skills = []
        
        # First check the skills section
        skills_text = sections.get('skills', '')
        
        # If no dedicated skills section, look at full text
        if not skills_text:
            for paragraph in text.split('\n\n'):
                if any(keyword in paragraph.lower() for keyword in ['skill', 'technology', 'competency', 'expertise']):
                    skills_text += paragraph + '\n\n'
        
        # Extract skills from different categories
        for category, keywords in self.skill_categories.items():
            category_skills = []
            
            # Check for category-specific section
            category_pattern = r'(?i)(?:^|\n)\s*(' + re.escape(category) + r'|' + re.escape(category.replace(' ', r'\s+')) + r')(?:\s+skills)?(?:\:|\n)'
            category_match = re.search(category_pattern, skills_text)
            
            if category_match:
                # Extract skills from this specific category section
                start_idx = category_match.end()
                # Find end of this category (next category or end of skills section)
                end_match = re.search(r'(?i)(?:^|\n)\s*([A-Za-z\s]+)(?:\s+skills)?(?:\:|\n)', skills_text[start_idx:])
                end_idx = start_idx + end_match.start() if end_match else len(skills_text)
                
                category_text = skills_text[start_idx:end_idx]
            else:
                # Use full skills text for this category
                category_text = skills_text
            
            # Look for skills from this category in the text
            for skill in keywords:
                if re.search(r'\b' + re.escape(skill.lower()) + r'\b', category_text.lower()):
                    category_skills.append(skill)
                # Also check full text for important skills
                elif category in ['Programming Languages', 'Frameworks', 'Tools'] and re.search(r'\b' + re.escape(skill.lower()) + r'\b', text.lower()):
                    category_skills.append(skill)
            
            # Add non-empty skill categories
            if category_skills:
                all_skills.append({
                    "category": category,
                    "skills": category_skills
                })
        
        # Add general unclassified skills
        general_skills = []
        
        # Extract skills from bullet points
        bullet_matches = re.finditer(self.patterns['bullet_point'], skills_text)
        for bullet_match in bullet_matches:
            skill = bullet_match.group(1).strip()
            # Make sure it's a reasonable skill (not too long or short)
            if 2 < len(skill) < 50 and not any(skill in cat_skills for cat in all_skills for cat_skills in cat["skills"]):
                general_skills.append(skill)
        
        # Extract comma-separated skills
        skill_lists = re.finditer(r'(?i)(?:skills|abilities|proficiencies)(?::|include|are)?\s*(.+?)(?=\n\n|\n[A-Z]|$)', skills_text)
        for skill_list in skill_lists:
            skills_text = skill_list.group(1)
            skills = [s.strip() for s in re.split(r',|\n|•', skills_text)]
            for skill in skills:
                if 2 < len(skill) < 50 and skill not in general_skills and not any(skill in cat_skills for cat in all_skills for cat_skills in cat["skills"]):
                    general_skills.append(skill)
        
        # Add general skills if found
        if general_skills:
            all_skills.append({
                "category": "General Skills",
                "skills": general_skills
            })
        
        return all_skills
    
    ################################################################################
    # Helper methods
    ################################################################################
    
    def _split_section_into_entries(self, text: str) -> List[str]:
    
        """
        Split a section text into separate entries.

        Args:
            text: Section text to split

        Returns:
            List of entry texts
        """
        entries = []

        # Approach 1: Split by date range patterns
        date_matches = list(re.finditer(self.patterns['date_range'], text))
        if date_matches:
            # Split text at each date match
            start_idx = 0
            for i, match in enumerate(date_matches):
                entry_start = match.start()
                if i > 0:
                    # Add the previous entry
                    entries.append(text[start_idx:entry_start].strip())
                start_idx = entry_start

            # Add the last entry
            entries.append(text[start_idx:].strip())
            return entries
        
        # Approach 3: Split by double newlines if they exist
        if '\n\n' in text:
            entries = [entry.strip() for entry in text.split('\n\n') if entry.strip()]
            if len(entries) > 1:
                return entries
        
        # Default approach: Return the entire text as one entry
        return [text.strip()] if text.strip() else []

    def _clean_parsed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean parsed data by removing empty fields and lists.
        
        Args:
            data: Parsed resume data
            
        Returns:
            Cleaned resume data
        """
        def remove_empty(obj):
            if isinstance(obj, dict):
                return {k: remove_empty(v) for k, v in obj.items() if v not in ([], {}, "", None)}
            elif isinstance(obj, list):
                return [remove_empty(v) for v in obj if v not in ([], {}, "", None)]
            else:
                return obj
        
        return remove_empty(data)

    def _compile_tech_keywords(self) -> List[str]:
        """Compile a list of common technology keywords."""
        return [
            # Programming Languages
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust',
            'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl', 'Dart', 'Elixir', 'Clojure', 'Haskell',
            
            # Web Technologies
            'HTML', 'CSS', 'SASS', 'LESS', 'Bootstrap', 'jQuery', 'React', 'Angular', 'Vue.js', 'Ember.js',
            'Node.js', 'Express.js', 'Django', 'Flask', 'Spring', 'Laravel', 'Ruby on Rails', 'ASP.NET',
            
            # Databases
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQL Server', 'SQLite', 'Cassandra',
            'Elasticsearch', 'Neo4j', 'Firebase', 'DynamoDB',
            
            # DevOps & Cloud
            'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'Jenkins',
            'GitHub Actions', 'CI/CD', 'Nginx', 'Apache', 'Linux', 'Unix', 'Bash', 'Shell Scripting',
            
            # Data Science & ML
            'Pandas', 'NumPy', 'SciPy', 'Scikit-learn', 'TensorFlow', 'PyTorch', 'Keras', 'OpenCV',
            'NLTK', 'spaCy', 'Hadoop', 'Spark', 'Tableau', 'Power BI',
            
            # Mobile
            'Android', 'iOS', 'React Native', 'Flutter', 'Xamarin', 'Ionic',
            
            # Other Technologies
            'Git', 'SVN', 'Mercurial', 'REST', 'GraphQL', 'gRPC', 'WebSockets', 'OAuth', 'JWT',
            'Blockchain', 'Ethereum', 'Solidity', 'Web3'
        ]

    def _compile_skill_categories(self) -> Dict[str, List[str]]:
        """Compile categorized skill keywords."""
        return {
            'Programming Languages': [
                'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust',
                'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl', 'Dart', 'Elixir', 'Clojure', 'Haskell'
            ],
            'Web Development': [
                'HTML', 'CSS', 'SASS', 'LESS', 'Bootstrap', 'jQuery', 'React', 'Angular', 'Vue.js',
                'Node.js', 'Express.js', 'Django', 'Flask', 'Spring', 'Laravel', 'Ruby on Rails'
            ],
            'Databases': [
                'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQL Server', 'SQLite', 'Cassandra',
                'Elasticsearch', 'Neo4j', 'Firebase', 'DynamoDB'
            ],
            'DevOps & Cloud': [
                'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'Jenkins',
                'CI/CD', 'Nginx', 'Apache', 'Linux', 'Unix', 'Bash', 'Shell Scripting'
            ],
            'Data Science': [
                'Pandas', 'NumPy', 'SciPy', 'Scikit-learn', 'TensorFlow', 'PyTorch', 'Keras', 'OpenCV',
                'NLTK', 'spaCy', 'Hadoop', 'Spark', 'Tableau', 'Power BI'
            ],
            'Mobile Development': [
                'Android', 'iOS', 'React Native', 'Flutter', 'Xamarin', 'Ionic'
            ],
            'Soft Skills': [
                'Communication', 'Leadership', 'Teamwork', 'Problem Solving', 'Critical Thinking',
                'Time Management', 'Adaptability', 'Creativity', 'Collaboration', 'Presentation'
            ],
            'Project Management': [
                'Agile', 'Scrum', 'Kanban', 'Waterfall', 'JIRA', 'Trello', 'Confluence',
                'Project Planning', 'Risk Management', 'Budgeting'
            ]
        }

    def _compile_job_titles(self) -> List[str]:
        """Compile common job titles for better role extraction."""
        return [
            'Software Engineer', 'Senior Software Engineer', 'Software Developer', 'Web Developer',
            'Frontend Developer', 'Backend Developer', 'Full Stack Developer', 'DevOps Engineer',
            'Data Scientist', 'Machine Learning Engineer', 'Data Engineer', 'Data Analyst',
            'Systems Administrator', 'Network Engineer', 'Security Engineer', 'QA Engineer',
            'Product Manager', 'Project Manager', 'Technical Lead', 'Engineering Manager',
            'CTO', 'CIO', 'IT Director', 'Solutions Architect', 'UX Designer', 'UI Designer'
        ]

    def _compile_education_keywords(self) -> List[str]:
        """Compile common education institution and degree keywords."""
        return [
            'University', 'College', 'Institute', 'School', 'Academy', 
            'Bachelor', 'Master', 'PhD', 'Doctorate', 'B.S.', 'M.S.', 'MBA',
            'B.Tech', 'M.Tech', 'B.A.', 'M.A.', 'B.Sc.', 'M.Sc.', 'B.E.', 'M.E.'
        ]

    def _compile_language_data(self) -> Dict[str, Dict[str, str]]:
        """Compile language data with ISO codes and proficiency levels."""
        return {
            'English': {'iso_code': 'en', 'proficiency_levels': ['Native', 'Fluent', 'Professional']},
            'Spanish': {'iso_code': 'es', 'proficiency_levels': ['Native', 'Fluent', 'Intermediate']},
            'French': {'iso_code': 'fr', 'proficiency_levels': ['Native', 'Fluent', 'Intermediate']},
            'German': {'iso_code': 'de', 'proficiency_levels': ['Native', 'Fluent', 'Intermediate']},
            'Chinese': {'iso_code': 'zh', 'proficiency_levels': ['Native', 'Fluent', 'Intermediate']},
            'Japanese': {'iso_code': 'ja', 'proficiency_levels': ['Native', 'Fluent', 'Intermediate']},
            'Russian': {'iso_code': 'ru', 'proficiency_levels': ['Native', 'Fluent', 'Intermediate']},
            'Portuguese': {'iso_code': 'pt', 'proficiency_levels': ['Native', 'Fluent', 'Intermediate']},
            'Arabic': {'iso_code': 'ar', 'proficiency_levels': ['Native', 'Fluent', 'Intermediate']},
            'Hindi': {'iso_code': 'hi', 'proficiency_levels': ['Native', 'Fluent', 'Intermediate']}
        }

    def save_to_file(self, data: Dict, filename: str = 'resume_data.json') -> None:
        """
        Save parsed resume data to a JSON file.
        
        Args:
            data: Parsed resume data
            filename: Name of the output file
        """
        if not self.output_dir:
            raise ValueError("Output directory not specified in parser initialization")
            
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved parsed resume data to {output_path}")


# Example usage
if __name__ == "__main__":
    parser = AdvancedResumeParser(debug_mode=True, output_dir='./output')
    resume_data = parser.parse_resume('/Users/elgazar/Desktop/cvflow_server/cv_gen/instance/pdf_outputs/00a39ffd-1f6b-4bcb-a463-77c91c3d4c27.pdf')
    
    if isinstance(resume_data, dict):
        parser.save_to_file(resume_data)
    else:
        print(resume_data)