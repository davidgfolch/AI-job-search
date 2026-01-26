import traceback
from pathlib import Path
import pdfplumber
import pandas as pd
from commonlib.terminalColor import yellow, red, cyan

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
            print(yellow('AI_CV_MATCH disabled'))
            return False

        print(f'Loading CV from: {self.cv_location}')
        try:
            filePath = Path(self.cv_location)
            cvLocationTxt = self.cv_location.replace('.pdf', '.txt')
            filePathTxt = Path(cvLocationTxt)
            
            if not filePath.exists() and not filePathTxt.exists():
                print(red(f'CV file not found: {self.cv_location}'))
                return False
                
            fileExtension = filePath.suffix.lower()
            if fileExtension == '.pdf' and not filePathTxt.exists():
                self.cv_content = extractTextFromPDF(self.cv_location)
                print(f'CV (PDF) loaded from: {self.cv_location} ({len(self.cv_content)} chars)')
                try:
                    with open(cvLocationTxt, 'w', encoding='utf-8') as mdFile:
                        mdFile.write(self.cv_content)
                except Exception as e:
                     print(yellow(f"Could not save cached TXT CV: {e}"))
            elif filePathTxt.exists():
                with open(cvLocationTxt, 'r', encoding='utf-8') as f:
                    self.cv_content = f.read()
                print(f'CV (text from PDF) loaded from: {cvLocationTxt} ({len(self.cv_content)} chars)')
            else:
                print(yellow(f'Unsupported CV file format: {fileExtension}. Supported formats: .txt, .pdf'))
                return False
                
            if not self.cv_content or len(self.cv_content.strip()) == 0:
                print(yellow('CV file is empty'))
                return False
                
            return True
        except FileNotFoundError:
            print(red(f'CV file not found: {self.cv_location}'))
            return False
        except Exception:
            print(red(f'Error loading CV:'))
            print(red(traceback.format_exc()))
            return False

    def get_content(self):
        return self.cv_content
