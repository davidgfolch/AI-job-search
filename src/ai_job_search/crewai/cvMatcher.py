import traceback
import pandas as pd
import pdfplumber
from pathlib import Path
from ai_job_search.tools.terminalColor import red, yellow
from ai_job_search.tools.util import getEnv, getEnvBool

# CV content cache
cvContent = None

def extractTextFromPDF(pdf_path: str) -> str:
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                all_text.append(page_text)
            # Extraer tablas y convertirlas a Markdown
            tables = page.extract_tables()
            for table in tables:
                df = pd.DataFrame(table[1:], columns=table[0])
                markdown = df.to_markdown(index=False)
                all_text.append(markdown)
    # Unir todo el contenido en una sola cadena Markdown
    return "\n\n".join(all_text)


def loadCVContent():
    """Loads CV content if AI_CV_MATCH is enabled. Supports txt, md, and pdf formats"""
    global cvContent
    if not getEnvBool('AI_CV_MATCH'):
        cvContent = None
        return    
    if cvContent is not None:
        return
    cvLocation = getEnv('AI_CV_MATCH_LOCATION')
    if not cvLocation:
        print(yellow('AI_CV_MATCH is enabled but AI_CV_MATCH_LOCATION is not set'))
        return
    try:
        filePath = Path(cvLocation)
        cvLocationTxt = cvLocation.replace('.pdf','.txt')
        filePathTxt = Path(cvLocationTxt)
        if not filePath.exists() and not filePathTxt.exists():
            print(red(f'CV file not found: {cvLocation}'))
            return None
        fileExtension = filePath.suffix.lower()
        # Handle PDF files
        if fileExtension == '.pdf' and not filePathTxt.exists():
            cvContent = extractTextFromPDF(cvLocation)
            print(yellow(f'CV (PDF) loaded from: {cvLocation} ({len(cvContent)} chars)'))
            with open(cvLocationTxt, 'w', encoding='utf-8') as mdFile:
                mdFile.write(cvContent)
        # Handle text files (txt, md, markdown)
        elif fileExtension in ['.txt', '.md', '.markdown']:
            with open(cvLocation, 'r', encoding='utf-8') as f:
                cvContent = f.read()
            print(yellow(f'CV (text) loaded from: {cvLocation} ({len(cvContent)} chars)'))
        elif filePathTxt.exists():
            with open(cvLocationTxt, 'r', encoding='utf-8') as f:
                cvContent = f.read()
            print(yellow(f'CV (text from PDF) loaded from: {cvLocationTxt} ({len(cvContent)} chars)'))
        else:
            print(red(f'Unsupported CV file format: {fileExtension}. Supported formats: .txt, .md, .pdf'))
            return None
        if not cvContent or len(cvContent.strip()) == 0:
            print(red('CV file is empty'))
            return None
        return cvContent
    except FileNotFoundError:
        print(red(f'CV file not found: {cvLocation}'))
        return None
    except Exception as ex:
        print(red(f'Error loading CV: {ex}'))
        traceback.print_exc()
        return None


