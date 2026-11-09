"""Build the LaTeX guide and PDF from the same eight Markdown walkthrough files."""
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'guide'
REPLACEMENTS = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}


def escape(text):
    return ''.join(REPLACEMENTS.get(char, char) for char in text)


def inline(text):
    # The walkthrough intentionally uses a small, explicit Markdown subset.
    pattern = r'(`[^`]+`|\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*)'
    output = []
    for token in re.split(pattern, text):
        if token.startswith('`'):
            output.append(r'\texttt{' + escape(token[1:-1]).replace('-', r'-\allowbreak{}').replace(r'\_', r'\_\allowbreak{}') + '}')
        elif token.startswith('['):
            label, url = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', token).groups()
            if not url.startswith('https://'):
                url = 'https://github.com/ZoyaV/researcheros_starter_kit/blob/main/walkthrough/' + url
            output.append(r'\href{' + escape(url) + '}{' + escape(label) + '}')
        elif token.startswith('**'):
            output.append(r'\textbf{' + escape(token[2:-2]) + '}')
        else:
            output.append(escape(token))
    return ''.join(output)


def markdown(text):
    output, paragraph, code = [], [], None

    def flush():
        if paragraph:
            output.append(inline(' '.join(paragraph)) + '\n\n')
            paragraph.clear()

    for line in text.splitlines():
        if line.startswith('```'):
            flush()
            if code is None:
                code = []
            else:
                output.append('\\begin{promptbox}\n\\begin{Verbatim}\n' + '\n'.join(code) + '\n\\end{Verbatim}\n\\end{promptbox}\n')
                code = None
        elif code is not None:
            code.append(line)
        elif line.startswith('# '):
            flush()
            output.append('\\clearpage\n\\section{' + inline(line[2:]) + '}\n')
        elif line.startswith('## '):
            flush()
            if line == '## Сообщение для итоговой проверки':
                output.append('\\newpage\n')
            output.append('\\subsection*{' + inline(line[3:]) + '}\n')
        elif re.match(r'^\d+\. ', line):
            flush()
            number, content = line.split('. ', 1)
            output.append(r'\par\noindent\hangindent=1.6em\hangafter=1 \textbf{' + number + '.} ' + inline(content) + '\\par\n')
        elif not line.strip():
            flush()
        else:
            paragraph.append(line.strip())
    flush()
    assert code is None, 'Unclosed code block'
    return ''.join(output)


def main():
    if not shutil.which('xelatex'):
        raise SystemExit('Install XeLaTeX and Noto Sans / Noto Sans Mono to build the PDF.')
    template = (GUIDE / 'template.tex').read_text(encoding='utf-8')
    files = sorted((ROOT / 'walkthrough').glob('[0-9][0-9]-*.md'))
    assert len(files) == 8
    body = '\n'.join(markdown(path.read_text(encoding='utf-8')) for path in files)
    tex = template.replace('% WALKTHROUGH_CONTENT', body)
    GUIDE.mkdir(exist_ok=True)
    (GUIDE / 'starter-kit.tex').write_text(tex, encoding='utf-8')
    for _ in range(2):
        result = subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', 'starter-kit.tex'], cwd=GUIDE, capture_output=True, text=True)
        if result.returncode:
            raise SystemExit(result.stdout[-6000:])
    print(GUIDE / 'starter-kit.pdf')


if __name__ == '__main__':
    main()
