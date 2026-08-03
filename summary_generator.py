import re
import os
import math
import threading
from collections import defaultdict

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

try:
    from pdfminer.high_level import extract_text
    HAS_PDFMINER = True
except ImportError:
    HAS_PDFMINER = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import textract
    HAS_TEXTRACT = True
except ImportError:
    HAS_TEXTRACT = False

try:
    import win32com.client
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False

# AI模型支持：优先使用 llama_cpp，失败则使用 ctransformers
try:
    import sys
    
    # 设置 LLAMA_CPP_LIB_PATH 环境变量，确保在 PyInstaller 打包后也能找到 DLL 文件
    # llama_cpp 库检查的环境变量是 LLAMA_CPP_LIB_PATH（注意：不是 LLAMA_CPP_LIB）
    # 该变量需要的是包含 llama.dll 的目录路径
    llama_lib_dir = None
    possible_dirs = []
    
    try:
        # PyInstaller 打包后的路径
        base_path = sys._MEIPASS
        possible_dirs.append(os.path.join(base_path, "llama_cpp", "lib"))
        possible_dirs.append(os.path.join(base_path, "llama_cpp"))
        possible_dirs.append(base_path)
    except AttributeError:
        pass
    
    # 开发环境路径
    dev_base_path = os.path.dirname(os.path.abspath(__file__))
    possible_dirs.append(os.path.join(dev_base_path, ".venv", "Lib", "site-packages", "llama_cpp", "lib"))
    possible_dirs.append(os.path.join(dev_base_path, ".venv", "Lib", "site-packages", "llama_cpp"))
    possible_dirs.append(os.path.join(dev_base_path, ".venv", "Lib", "site-packages", "bin"))
    possible_dirs.append(os.path.join(dev_base_path, "llama_cpp", "lib"))
    possible_dirs.append(os.path.join(dev_base_path, "llama_cpp"))
    
    # 尝试查找有效的 DLL 目录（需要包含 llama.dll）
    for dir_path in possible_dirs:
        if os.path.isdir(dir_path) and os.path.exists(os.path.join(dir_path, "llama.dll")):
            llama_lib_dir = dir_path
            break
    
    if llama_lib_dir:
        os.environ["LLAMA_CPP_LIB_PATH"] = llama_lib_dir
        print(f"[DEBUG] Set LLAMA_CPP_LIB_PATH to: {llama_lib_dir}")
    else:
        print(f"[DEBUG] llama.dll not found. Searched dirs: {possible_dirs}")
    
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
    HAS_CTRANSFORMERS = False
    print("[DEBUG] Using llama_cpp for AI summarization")
except (ImportError, FileNotFoundError, RuntimeError) as e:
    print(f"[DEBUG] Failed to initialize llama_cpp: {str(e)}")
    HAS_LLAMA_CPP = False

# 备用：使用 ctransformers
if not HAS_LLAMA_CPP:
    try:
        from ctransformers import AutoModelForCausalLM
        HAS_CTRANSFORMERS = True
        print("[DEBUG] Using ctransformers for AI summarization")
    except ImportError as e:
        print(f"[DEBUG] Failed to import ctransformers: {str(e)}")
        HAS_CTRANSFORMERS = False

# 全局模型实例，避免重复加载
_llm_instance = None
_llm_lock = threading.Lock()

class TextRankSummarizer:
    def __init__(self):
        self.damping_factor = 0.85
        self.max_iterations = 100
        self.tolerance = 1e-6
    
    def _tokenize_chinese(self, text):
        if HAS_JIEBA:
            return list(jieba.cut(text))
        else:
            return list(text)
    
    def _tokenize_english(self, text):
        text = text.lower()
        words = re.findall(r'[a-zA-Z]+', text)
        return words
    
    def _tokenize(self, text):
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        english_words = re.findall(r'[a-zA-Z]+', text)
        
        if len(chinese_chars) > len(english_words):
            return self._tokenize_chinese(text)
        else:
            return self._tokenize_english(text)
    
    def _split_sentences(self, text):
        sentence_endings = re.compile(r'([。！？.!?]+|\n\n+)')
        parts = sentence_endings.split(text)
        sentences = []
        for i in range(0, len(parts)-1, 2):
            sentence = (parts[i] + parts[i+1]).strip()
            if sentence:
                sentences.append(sentence)
        if parts[-1].strip():
            sentences.append(parts[-1].strip())
        return sentences
    
    def _calculate_similarity(self, sent1, sent2):
        words1 = set(self._tokenize(sent1))
        words2 = set(self._tokenize(sent2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _build_graph(self, sentences):
        n = len(sentences)
        graph = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    similarity = self._calculate_similarity(sentences[i], sentences[j])
                    if similarity > 0:
                        graph[i][j] = similarity
        
        for i in range(n):
            row_sum = sum(graph[i])
            if row_sum > 0:
                for j in range(n):
                    graph[i][j] /= row_sum
        
        return graph
    
    def _page_rank(self, graph):
        n = len(graph)
        scores = [1.0] * n
        
        for iteration in range(self.max_iterations):
            new_scores = [0.0] * n
            for i in range(n):
                new_scores[i] = 1 - self.damping_factor
                for j in range(n):
                    if graph[j][i] > 0:
                        new_scores[i] += self.damping_factor * scores[j] * graph[j][i]
            
            max_diff = max(abs(new_scores[i] - scores[i]) for i in range(n))
            scores = new_scores
            
            if max_diff < self.tolerance:
                break
        
        return scores
    
    def summarize(self, text, num_sentences=5):
        if not text or text.strip() == "":
            return ""
        
        sentences = self._split_sentences(text)
        
        if len(sentences) <= num_sentences:
            return "\n".join(sentences)
        
        graph = self._build_graph(sentences)
        scores = self._page_rank(graph)
        
        ranked_sentences = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        
        selected_indices = sorted([idx for idx, _ in ranked_sentences[:num_sentences]])
        summary_sentences = [sentences[idx] for idx in selected_indices]
        
        return "\n".join(summary_sentences)

class FileTextExtractor:
    # 文本文件扩展名列表
    TEXT_EXTENSIONS = [
        '.txt', '.md', '.py', '.json', '.xml', '.html', '.htm',
        '.css', '.js', '.java', '.c', '.cpp', '.h', '.hpp',
        '.php', '.go', '.rust', '.rs', '.sql', '.log',
        '.csv', '.tsv', '.jsonl', '.yaml', '.yml', '.toml',
        '.mdx', '.rst', '.tex', '.bib'
    ]
    
    @staticmethod
    def _is_binary(file_path, sample_size=4096):
        """检测文件是否为二进制文件"""
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(sample_size)
                # 如果文件包含大量不可打印字符，可能是二进制文件
                if b'\0' in sample:
                    return True
                # 计算不可打印字符的比例
                printable = sum(1 for c in sample if c >= 32 or c in b'\n\r\t')
                if printable / len(sample) < 0.9:
                    return True
            return False
        except:
            return True
    
    @staticmethod
    def _read_file_with_encoding(file_path):
        """尝试多种编码读取文件，防止乱码"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'utf-16']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # 检查内容是否看起来像乱码（包含大量控制字符）
                    control_chars = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t')
                    if control_chars / max(len(content), 1) < 0.1:
                        return content
            except (UnicodeDecodeError, LookupError):
                continue
        # 最后的尝试，忽略错误
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                control_chars = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t')
                if control_chars / max(len(content), 1) < 0.1:
                    return content
        except:
            pass
        return ""
    
    @staticmethod
    def extract_text_from_file(file_path):
        if not os.path.exists(file_path):
            return ""
        
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            # 对于特殊格式（.docx、.doc、.pdf、.xlsx等），直接使用对应库处理，跳过二进制检测
            if ext == '.docx' and HAS_DOCX:
                doc = docx.Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            
            elif ext == '.doc':
                # 优先使用pywin32（Windows平台专用）
                if HAS_WIN32COM:
                    try:
                        word = win32com.client.Dispatch("Word.Application")
                        word.Visible = False
                        doc = word.Documents.Open(file_path)
                        text = doc.Content.Text
                        doc.Close(False)
                        word.Quit()
                        return text
                    except Exception as e:
                        print(f"[DEBUG] pywin32 failed for {file_path}: {str(e)}")
                        return ""
                # 备选：使用textract
                elif HAS_TEXTRACT:
                    try:
                        text = textract.process(file_path).decode('utf-8', errors='replace')
                        return text
                    except Exception as e:
                        print(f"[DEBUG] textract failed for {file_path}: {str(e)}")
                        return ""
                else:
                    print(f"[DEBUG] No .doc extractor available for {file_path}")
                    return ""
            
            elif ext == '.pdf' and HAS_PDFMINER:
                text = extract_text(file_path)
                # PDF提取的文本可能有编码问题，进行清理
                return text.encode('utf-8', errors='replace').decode('utf-8')
            
            elif ext == '.rtf':
                return FileTextExtractor._extract_rtf(file_path)
            
            elif ext in ['.xls', '.xlsx']:
                return FileTextExtractor._extract_spreadsheet(file_path)
            
            # 对于纯文本格式，直接读取
            elif ext in ['.txt', '.md', '.py', '.json', '.xml', '.html', '.htm',
                       '.css', '.js', '.java', '.c', '.cpp', '.h', '.hpp',
                       '.php', '.go', '.rs', '.sql', '.log', '.jsonl', '.yaml', '.yml', '.toml',
                       '.csv', '.tsv', '.mdx', '.rst', '.tex', '.bib']:
                return FileTextExtractor._read_file_with_encoding(file_path)
            
            # 对于未知格式，先检测是否为二进制文件
            else:
                if FileTextExtractor._is_binary(file_path):
                    print(f"[DEBUG] {file_path} appears to be binary, skipping")
                    return ""
                return FileTextExtractor._read_file_with_encoding(file_path)
        
        except Exception as e:
            print(f"[DEBUG] Failed to extract text from {file_path}: {str(e)}")
            return ""
    
    @staticmethod
    def _extract_rtf(file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return re.sub(r'\\[a-z]+\s*|\\[{}]|[\x00-\x1f]', '', content)
    
    @staticmethod
    def _extract_spreadsheet(file_path):
        try:
            import pandas as pd
            df = pd.read_excel(file_path) if file_path.endswith(('.xls', '.xlsx')) else pd.read_csv(file_path)
            return df.to_string()
        except ImportError:
            return ""
        except Exception as e:
            return ""

def generate_summary(file_path, num_sentences=5):
    text = FileTextExtractor.extract_text_from_file(file_path)
    
    if not text:
        return None
    
    summarizer = TextRankSummarizer()
    summary = summarizer.summarize(text, num_sentences)
    
    return summary

def generate_summary_from_text(text, num_sentences=5, callback=None):
    if not text or text.strip() == "":
        return ""
    
    summarizer = TextRankSummarizer()
    summary = summarizer.summarize(text, num_sentences)
    
    # 如果有回调，进行流式输出
    if callback:
        for char in summary:
            callback(char)
    
    return summary


def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和 PyInstaller 打包后的环境"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def _get_llm_instance():
    """获取全局LLM实例（优先使用llama_cpp，失败则使用ctransformers）"""
    global _llm_instance
    
    if _llm_instance is not None:
        return _llm_instance
    
    with _llm_lock:
        if _llm_instance is not None:
            return _llm_instance
        
        # 查找模型文件（兼容打包后的环境）
        # 支持多种模型格式，优先使用 Q3_K_M
        import glob
        
        # 尝试多个可能的目录
        possible_dirs = []
        
        # 1. 资源目录（打包后为 _internal 目录）
        possible_dirs.append(resource_path("."))
        
        # 2. 当前脚本所在目录
        possible_dirs.append(os.path.dirname(os.path.abspath(__file__)))
        
        # 3. 当前工作目录
        possible_dirs.append(os.getcwd())
        
        # 4. EXE 所在目录（打包后）
        try:
            exe_dir = os.path.dirname(sys.executable)
            possible_dirs.append(exe_dir)
        except:
            pass
        
        # 5. 上级目录（打包后 _internal 的上级）
        try:
            exe_dir = os.path.dirname(sys.executable)
            possible_dirs.append(os.path.dirname(exe_dir))
        except:
            pass
        
        gguf_files = []
        for model_dir in possible_dirs:
            if model_dir and os.path.isdir(model_dir):
                files = glob.glob(os.path.join(model_dir, "*.gguf"))
                if files:
                    gguf_files = files
                    print(f"[DEBUG] Found model files in: {model_dir}")
                    break
        
        model_path = None
        # 优先模式列表（按优先级排序）
        priority_patterns = [
            "q3_k_m",
            "q4_k_m",
            "q3_k_s",
            "q4_k_s",
            "iq3_s",
        ]
        
        # 按优先级查找匹配的模型文件
        for pattern in priority_patterns:
            for gguf_file in gguf_files:
                if pattern.lower() in os.path.basename(gguf_file).lower():
                    model_path = gguf_file
                    print(f"[DEBUG] Found model file: {model_path}")
                    break
            if model_path:
                break
        
        # 如果没有找到匹配的，使用第一个找到的 gguf 文件
        if not model_path and gguf_files:
            model_path = gguf_files[0]
            print(f"[DEBUG] Using first found model file: {model_path}")
        
        if not model_path:
            print(f"[DEBUG] No model file found in: {model_dir}")
            return None
        
        # 优先尝试 llama_cpp
        if HAS_LLAMA_CPP:
            try:
                _llm_instance = Llama(
                    model_path=model_path,
                    n_ctx=2048,  # 上下文窗口大小
                    n_threads=8,  # 使用的线程数
                    n_gpu_layers=0,  # CPU运行
                    verbose=True
                )
                print(f"[DEBUG] LLM model loaded successfully with llama_cpp: {model_path}")
                return _llm_instance
            except Exception as e:
                print(f"[DEBUG] Failed to load LLM model with llama_cpp: {str(e)}")
                # llama_cpp加载失败，继续尝试ctransformers
        
        # 备用：使用 ctransformers
        if HAS_CTRANSFORMERS:
            try:
                from ctransformers import AutoModelForCausalLM
                _llm_instance = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    model_type="llama",
                    context_length=2048,
                    threads=8,
                    verbose=True
                )
                print(f"[DEBUG] LLM model loaded successfully with ctransformers: {model_path}")
                return _llm_instance
            except Exception as e:
                print(f"[DEBUG] Failed to load LLM model with ctransformers: {str(e)}")
        
        return None


# 临时禁用AI模型，直接使用TextRank算法
USE_AI = False  # 设置为True以启用AI模型（需要正确安装llama-cpp-python）

def generate_summary_with_ai(text, language="zh", callback=None):
    """
    使用AI模型生成摘要（支持流式输出）
    注意：当前AI功能已禁用，使用TextRank算法代替
    
    Args:
        text: 要生成摘要的文本
        language: 语言（zh/zh-CN/zh-TW 为中文，其他为英文）
        callback: 流式输出回调函数，接收生成的文本片段
    
    Returns:
        生成的摘要文本
    """
    if not text or text.strip() == "":
        return ""
    
    # 判断语言
    is_chinese = language.lower() in ["zh", "zh-cn", "zh-tw", "zh-hans", "zh-hant"]
    
    # AI功能已禁用，直接使用TextRank
    if not USE_AI:
        print("[DEBUG] AI disabled, using TextRank")
        return generate_summary_from_text(text, 5, callback)
    
    # 获取LLM实例
    llm = _get_llm_instance()
    if llm is None:
        # 如果LLM不可用，回退到TextRank算法
        print("[DEBUG] LLM model not available, falling back to TextRank")
        return generate_summary_from_text(text, 5, callback)
    
    try:
        full_response = ""
        
        # 判断使用的是 llama_cpp 还是 ctransformers（通过检查实例类型）
        is_ctransformers = False
        if HAS_CTRANSFORMERS:
            from ctransformers import AutoModelForCausalLM
            if isinstance(llm, AutoModelForCausalLM):
                is_ctransformers = True
        
        if is_ctransformers:
            # ctransformers API
            if is_chinese:
                prompt = f"你是一个专业的中文文本摘要助手。请对以下文本进行详细的中文总结，输出完整的摘要内容，不要包含任何前缀或解释：\n\n{text}"
            else:
                prompt = f"You are a professional English text summarization assistant. Please provide a detailed English summary of the following text. Output the summary directly without any prefix, explanation, or extra words:\n\n{text}"
            
            # 流式生成
            for token in llm.create_stream(
                prompt,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.9
            ):
                full_response += token
                
                # 调用回调函数进行流式输出
                if callback:
                    callback(token)
        else:
            # llama_cpp API - 使用聊天格式生成摘要
            if is_chinese:
                messages = [
                    {"role": "system", "content": "你是一个专业的中文文本摘要助手。你必须用中文回答，不要使用任何英文。"},
                    {"role": "user", "content": f"请对以下文本进行详细的中文总结，输出完整的摘要内容，不要包含任何前缀或解释：\n\n{text}"}
                ]
            else:
                messages = [
                    {"role": "system", "content": "You are a professional English text summarization assistant. You MUST respond in ENGLISH ONLY. Do NOT use any Chinese characters at all."},
                    {"role": "user", "content": f"Please provide a detailed English summary of the following text. Output the summary directly without any prefix, explanation, or extra words:\n\n{text}"}
                ]
            
            # 流式生成
            for chunk in llm.create_chat_completion(
                messages=messages,
                max_tokens=1024,
                stream=True,
                temperature=0.7,
                top_p=0.9
            ):
                token = chunk["choices"][0]["delta"].get("content", "")
                full_response += token
                
                # 调用回调函数进行流式输出
                if callback:
                    callback(token)
        
        return full_response.strip()
    
    except Exception as e:
        print(f"[DEBUG] LLM generation failed: {str(e)}")
        # 失败时回退到TextRank算法，传递回调函数
        return generate_summary_from_text(text, 5, callback)


def generate_summary_with_ai_from_file(file_path, language="zh", callback=None):
    """
    从文件生成AI摘要（支持流式输出）
    
    Args:
        file_path: 文件路径
        language: 语言（zh/zh-CN/zh-TW 为中文，其他为英文）
        callback: 流式输出回调函数，接收生成的文本片段
    
    Returns:
        生成的摘要文本
    """
    text = FileTextExtractor.extract_text_from_file(file_path)
    
    if not text:
        return None
    
    return generate_summary_with_ai(text, language, callback)