from pathlib import Path
import pdfplumber
import pandas as pd
from commonlib.observability import get_logger

logger = get_logger("commonlib.cv_loader")

def extractTextFromPDF(pdf_path: str) -> str:
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                all_text.append(page_text)
            # Extract tables and convert to Markdown
            tables = page.extract_tables()
            for table in tables:
                df = pd.DataFrame(table[1:], columns=table[0])
                markdown = df.to_markdown(index=False)
                all_text.append(markdown)
    # Join all content into a single Markdown string
    return "\n\n".join(all_text)

class CVLoader:
    def __init__(self, cv_location: str = './cv/cv.txt', enabled: bool = True):
        self.cv_location = cv_location
        self.enabled = enabled
        self.cv_content = None

    def load_cv_content(self) -> bool:
        if self.cv_content is not None:
            return True
            
        if not self.enabled:
            logger.info("cv.load_skipped", reason="disabled", location=self.cv_location)
            return False

        logger.info("cv.load_started", location=self.cv_location)
        try:
            filePath = Path(self.cv_location)
            cvLocationTxt = self.cv_location.replace('.pdf', '.txt')
            filePathTxt = Path(cvLocationTxt)
            
            if not filePath.exists() and not filePathTxt.exists():
                logger.warning("cv.file_not_found", location=self.cv_location)
                return False
                
            fileExtension = filePath.suffix.lower()
            if fileExtension == '.pdf' and not filePathTxt.exists():
                self.cv_content = extractTextFromPDF(self.cv_location)
                logger.info("cv.loaded", source="pdf", location=self.cv_location, chars=len(self.cv_content))
                try:
                    with open(cvLocationTxt, 'w', encoding='utf-8') as mdFile:
                        mdFile.write(self.cv_content)
                except Exception as e:
                     logger.warning("cv.cache_write_failed", location=cvLocationTxt, error=str(e))
            elif filePathTxt.exists():
                with open(cvLocationTxt, 'r', encoding='utf-8') as f:
                    self.cv_content = f.read()
                logger.info("cv.loaded", source="pdf_text", location=cvLocationTxt, chars=len(self.cv_content))
            else:
                logger.warning("cv.unsupported_format", location=self.cv_location, extension=fileExtension, supported=['.txt', '.pdf'])
                return False
                
            if not self.cv_content or len(self.cv_content.strip()) == 0:
                logger.warning("cv.empty", location=cvLocationTxt)
                return False
                
            return True
        except FileNotFoundError:
            logger.warning("cv.file_not_found", location=self.cv_location)
            return False
        except Exception:
            logger.exception("cv.load_failed", location=self.cv_location)
            return False

    def get_content(self):
        return self.cv_content
