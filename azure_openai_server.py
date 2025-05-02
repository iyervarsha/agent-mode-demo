import os
from flask import Flask, request, jsonify, send_from_directory
from openai import AzureOpenAI
from azure.identity import InteractiveBrowserCredential
from flask_cors import CORS
import time
import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urljoin
import hashlib
import threading
import tempfile
import datetime
import base64
import io
from PIL import Image

# Import configuration
try:
    from config import (
        AZURE_OPENAI_ENDPOINT, 
        AZURE_OPENAI_DEPLOYMENT, 
        AZURE_OPENAI_API_VERSION,
        AZURE_OPENAI_API_KEY,
        SERVER_PORT,
        DEBUG_MODE
    )
except ImportError:
    print("Configuration file not found.")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Cache for the token to avoid authentication on each request
token_cache = {
    'token': None,
    'expiry': 0
}

def get_azure_token():
    """Get an Azure AD token for Azure OpenAI, with caching."""
    current_time = time.time()
    
    # If we have a cached token that's not expired (with 5-minute buffer), return it
    if token_cache['token'] and token_cache['expiry'] > current_time + 300:
        return token_cache['token']
    
    try:
        # If API key is provided, use it instead of AAD authentication
        if AZURE_OPENAI_API_KEY:
            return AZURE_OPENAI_API_KEY
        
        # Authenticate using browser-based authentication
        credential = InteractiveBrowserCredential()
        
        # Get the token
        token_response = credential.get_token("https://cognitiveservices.azure.com/.default")
        
        # Cache the token and its expiry time
        token_cache['token'] = token_response.token
        token_cache['expiry'] = token_response.expires_on
        
        return token_response.token
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/enhance-documentation', methods=['POST'])
def enhance_documentation():
    """API endpoint to enhance documentation with Azure OpenAI."""
    data = request.json
    
    if not data or 'markdown' not in data:
        return jsonify({'error': 'Missing required data'}), 400
    
    markdown = data['markdown']
    feature_name = data.get('featureName', 'Feature')
    category = data.get('category', '')
    doc_type = data.get('docType', '')
    enhancement_type = data.get('enhancementType', 'refine')
    
    # Get Azure AD token
    token = get_azure_token()
    if not token:
        return jsonify({'error': 'Failed to authenticate with Azure'}), 401
    
    try:
        # Create the Azure OpenAI client with the token
        if AZURE_OPENAI_API_KEY:
            client = AzureOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_API_KEY,
                api_version=AZURE_OPENAI_API_VERSION
            )
        else:
            client = AzureOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_version=AZURE_OPENAI_API_VERSION,
                azure_ad_token=token
            )
        
        # Create system prompt based on enhancement parameters
        system_prompt = create_system_prompt(category, doc_type, enhancement_type)
        
        # Create user prompt with the original markdown
        user_prompt = f"""Here is the documentation for a Microsoft Dev Box feature called "{feature_name}" that needs to be enhanced:
        
{markdown}

Please improve this documentation according to the instructions I've provided. Return the complete enhanced markdown document. Maintain all section headers and structure, but improve the content. Ensure all markdown formatting is preserved."""

        # Send request to Azure OpenAI
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Get the enhanced markdown
        enhanced_markdown = response.choices[0].message.content
        
        return jsonify({'enhancedMarkdown': enhanced_markdown})
    
    except Exception as e:
        print(f"Azure OpenAI error: {str(e)}")
        return jsonify({'error': f'Azure OpenAI error: {str(e)}'}), 500

@app.route('/api/analyze-screenshots', methods=['POST'])
def analyze_screenshots():
    """API endpoint to analyze screenshots and generate documentation."""
    data = request.json
    
    if not data or 'screenshots' not in data or not data['screenshots']:
        return jsonify({'error': 'No screenshots provided'}), 400
    
    feature_name = data.get('featureName', 'Feature')
    category = data.get('category', '')
    doc_type = data.get('docType', '')
    additional_context = data.get('additionalContext', '')
    enhancement_type = data.get('enhancementType', 'refine')
    screenshots = data.get('screenshots', [])
    
    # Get Azure AD token
    token = get_azure_token()
    if not token:
        return jsonify({'error': 'Failed to authenticate with Azure'}), 401
    
    try:
        # Create the Azure OpenAI client with the token
        if AZURE_OPENAI_API_KEY:
            client = AzureOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_key=AZURE_OPENAI_API_KEY,
                api_version=AZURE_OPENAI_API_VERSION
            )
        else:
            client = AzureOpenAI(
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_version=AZURE_OPENAI_API_VERSION,
                azure_ad_token=token
            )
        
        # Process screenshots
        screenshot_analysis = []
        
        # Create system prompt for vision model
        system_prompt = """You are an expert technical documentation writer for Microsoft. 
You are analyzing screenshots of a Microsoft Dev Box feature to help create documentation.
Provide a detailed analysis of what you see in the screenshots, including:
1. UI elements and their functions
2. Feature capabilities shown
3. Any configuration options visible
4. User workflow steps that can be inferred
5. Error messages or warnings visible
6. Any notable interface design patterns

Be specific and technical in your analysis."""
        
        # Process each screenshot with GPT-4 Vision capabilities
        for screenshot in screenshots:
            name = screenshot.get('name', 'Screenshot')
            base64_data = screenshot.get('base64', '')
            
            if not base64_data:
                continue
            
            # Create the message with image content
            user_prompt = f"Please analyze this screenshot of the {feature_name} feature in Microsoft Dev Box and describe what you see."
            
            # Add the additional context if provided
            if additional_context:
                user_prompt += f"\n\nAdditional context about this feature: {additional_context}"
            
            try:
                # Call Azure OpenAI with vision capabilities
                # Note: Using GPT-4 Vision through the chat completions endpoint
                response = client.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT,  # Ensure this deployment supports vision
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}}
                        ]}
                    ],
                    max_tokens=1000
                )
                
                # Extract the analysis
                analysis = response.choices[0].message.content
                screenshot_analysis.append({
                    "name": name,
                    "analysis": analysis
                })
                
            except Exception as e:
                print(f"Error processing screenshot {name}: {str(e)}")
                screenshot_analysis.append({
                    "name": name,
                    "analysis": f"Error analyzing this screenshot: {str(e)}",
                    "error": True
                })
        
        # Generate documentation based on screenshot analysis
        if screenshot_analysis:
            # Combine all analyses
            combined_analysis = "\n\n".join([
                f"### {analysis['name']}:\n{analysis['analysis']}" 
                for analysis in screenshot_analysis
            ])
            
            # Create system prompt for documentation generation
            doc_system_prompt = create_system_prompt(category, doc_type, enhancement_type)
            
            # Create user prompt with the screenshot analysis
            user_prompt = f"""Based on the following analysis of screenshots for the Microsoft Dev Box feature "{feature_name}", generate comprehensive documentation that matches Microsoft's documentation style:

{combined_analysis}

Additional context: {additional_context if additional_context else "No additional context provided."}

Create a full, well-structured documentation page with appropriate sections typical for Microsoft documentation, including:
1. Overview of the feature
2. Prerequisites (if applicable)
3. How to use/configure the feature
4. Best practices
5. Troubleshooting tips (if applicable)
6. References to related features

Ensure the documentation is clear, technically accurate, and follows Microsoft's documentation style."""

            # Send request to Azure OpenAI for documentation generation
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": doc_system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Get the generated markdown
            markdown = response.choices[0].message.content
            
            return jsonify({'markdown': markdown, 'analysis': screenshot_analysis})
        else:
            return jsonify({'error': 'No valid screenshots could be analyzed'}), 400
    
    except Exception as e:
        print(f"Screenshot analysis error: {str(e)}")
        return jsonify({'error': f'Screenshot analysis error: {str(e)}'}), 500

# Cache directory for storing scraped documentation
CACHE_DIR = os.path.join(tempfile.gettempdir(), "devbox_docs_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

class DevBoxDocAnalyzer:
    """Class to analyze Microsoft Dev Box documentation style and content."""
    
    BASE_URL = "https://learn.microsoft.com/en-us/azure/dev-box/"
    TOC_URL = "https://learn.microsoft.com/en-us/azure/dev-box/toc.json"
    CACHE_DURATION = 24 * 60 * 60  # 24 hours in seconds
    
    def __init__(self):
        self.session = requests.Session()
        self.docs_content = {}
        self.toc_data = None
        self.categories = {}
        self.doc_cache = {}
        
        # Set up headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def get_cache_path(self, url):
        """Generate a cache file path for a URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(CACHE_DIR, f"{url_hash}.json")
    
    def is_cache_valid(self, cache_path):
        """Check if the cache file exists and is still valid."""
        if not os.path.exists(cache_path):
            return False
        
        # Check if the cache is still valid based on creation time
        cache_time = os.path.getmtime(cache_path)
        current_time = time.time()
        return (current_time - cache_time) < self.CACHE_DURATION
    
    def load_from_cache(self, url):
        """Load content from cache if available and valid."""
        cache_path = self.get_cache_path(url)
        if self.is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache: {str(e)}")
        return None
    
    def save_to_cache(self, url, content):
        """Save content to cache."""
        cache_path = self.get_cache_path(url)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(content, f)
        except Exception as e:
            print(f"Error saving to cache: {str(e)}")
    
    def fetch_toc(self):
        """Fetch the table of contents for Dev Box documentation."""
        cached_toc = self.load_from_cache(self.TOC_URL)
        if cached_toc:
            self.toc_data = cached_toc
            return cached_toc
        
        try:
            response = self.session.get(self.TOC_URL)
            response.raise_for_status()
            toc_data = response.json()
            self.toc_data = toc_data
            self.save_to_cache(self.TOC_URL, toc_data)
            return toc_data
        except Exception as e:
            print(f"Error fetching TOC: {str(e)}")
            return None
    
    def extract_categories(self):
        """Extract document categories from the TOC."""
        if not self.toc_data:
            self.fetch_toc()
        
        if not self.toc_data:
            return {}
        
        categories = {}
        
        # Process the TOC to identify main categories and their documents
        for item in self.toc_data['items']:
            if 'items' in item:
                category_name = item.get('name', '')
                category_docs = []
                
                for child in item.get('items', []):
                    if 'href' in child:
                        doc_url = child['href']
                        if doc_url.startswith('/'):
                            full_url = urljoin("https://learn.microsoft.com", doc_url)
                            category_docs.append({
                                'title': child.get('name', ''),
                                'url': full_url
                            })
                
                if category_docs:
                    categories[category_name] = category_docs
        
        self.categories = categories
        return categories
    
    def fetch_document(self, url):
        """Fetch and parse a specific document."""
        if url in self.doc_cache:
            return self.doc_cache[url]
        
        cached_doc = self.load_from_cache(url)
        if cached_doc:
            self.doc_cache[url] = cached_doc
            return cached_doc
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main content
            main_content = soup.find('main')
            if not main_content:
                main_content = soup.find('div', {'id': 'main'})
            if not main_content:
                main_content = soup.find('div', {'class': 'content'})
            
            if not main_content:
                return {'title': '', 'content': '', 'headings': [], 'paragraphs': []}
            
            # Extract title
            title_elem = main_content.find(['h1'])
            title = title_elem.get_text().strip() if title_elem else ''
            
            # Extract headings
            headings = []
            for heading in main_content.find_all(['h2', 'h3']):
                headings.append({
                    'level': int(heading.name[1]),
                    'text': heading.get_text().strip()
                })
            
            # Extract paragraphs
            paragraphs = []
            for p in main_content.find_all('p'):
                text = p.get_text().strip()
                if text:
                    paragraphs.append(text)
            
            # Extract lists
            lists = []
            for list_elem in main_content.find_all(['ul', 'ol']):
                list_items = []
                for li in list_elem.find_all('li'):
                    list_items.append(li.get_text().strip())
                lists.append({
                    'type': list_elem.name,
                    'items': list_items
                })
            
            # Extract code blocks
            code_blocks = []
            for code in main_content.find_all('code'):
                code_text = code.get_text().strip()
                if code_text:
                    code_blocks.append(code_text)
            
            # Extract note blocks
            notes = []
            for note in main_content.find_all(['div', 'aside'], {'class': re.compile(r'(note|alert|tip|warning|caution)')}):
                notes.append(note.get_text().strip())
            
            # Get full content as text
            content = main_content.get_text().strip()
            
            document = {
                'title': title,
                'content': content,
                'headings': headings,
                'paragraphs': paragraphs,
                'lists': lists,
                'code_blocks': code_blocks,
                'notes': notes,
                'url': url
            }
            
            self.doc_cache[url] = document
            self.save_to_cache(url, document)
            return document
        
        except Exception as e:
            print(f"Error fetching document {url}: {str(e)}")
            return {'title': '', 'content': '', 'headings': [], 'paragraphs': []}
    
    def analyze_docs_by_category(self, category):
        """Analyze documentation style and content for a specific category."""
        if not self.categories:
            self.extract_categories()
        
        if category not in self.categories:
            return None
        
        documents = []
        for doc_info in self.categories[category]:
            doc = self.fetch_document(doc_info['url'])
            if doc['content']:
                documents.append(doc)
        
        if not documents:
            return None
        
        # Analyze document structure and style
        analysis = {
            'category': category,
            'document_count': len(documents),
            'common_headings': self._extract_common_headings(documents),
            'style_patterns': self._extract_style_patterns(documents),
            'terminology': self._extract_terminology(documents),
            'example_snippets': self._extract_example_snippets(documents)
        }
        
        return analysis
    
    def _extract_common_headings(self, documents):
        """Extract common headings across documents."""
        heading_counts = {}
        
        for doc in documents:
            for heading in doc['headings']:
                heading_text = heading['text'].lower()
                if heading_text not in heading_counts:
                    heading_counts[heading_text] = 0
                heading_counts[heading_text] += 1
        
        # Get headings that appear in multiple documents
        common_headings = [
            {'text': heading, 'count': count}
            for heading, count in heading_counts.items()
            if count > 1
        ]
        
        # Sort by frequency
        common_headings.sort(key=lambda x: x['count'], reverse=True)
        return common_headings[:10]  # Return the top 10
    
    def _extract_style_patterns(self, documents):
        """Extract writing style patterns."""
        patterns = {
            'avg_paragraph_length': 0,
            'avg_sentence_length': 0,
            'sentence_starters': {},
            'transitions': [],
        }
        
        total_paragraphs = 0
        total_paragraph_length = 0
        all_text = ""
        
        for doc in documents:
            all_text += doc['content'] + " "
            for para in doc['paragraphs']:
                total_paragraphs += 1
                total_paragraph_length += len(para.split())
        
        if total_paragraphs > 0:
            patterns['avg_paragraph_length'] = total_paragraph_length / total_paragraphs
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', all_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            # Calculate average sentence length
            total_words = sum(len(s.split()) for s in sentences)
            patterns['avg_sentence_length'] = total_words / len(sentences)
            
            # Extract common sentence starters
            for sentence in sentences:
                words = sentence.split()
                if words:
                    first_word = words[0].lower()
                    if first_word not in patterns['sentence_starters']:
                        patterns['sentence_starters'][first_word] = 0
                    patterns['sentence_starters'][first_word] += 1
        
        # Sort and limit sentence starters
        sorted_starters = sorted(
            patterns['sentence_starters'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        patterns['sentence_starters'] = dict(sorted_starters[:10])
        
        # Common transitions
        transitions = ["however", "therefore", "additionally", "furthermore", 
                      "moreover", "in addition", "for example", "in conclusion"]
        for transition in transitions:
            count = len(re.findall(r'\b' + transition + r'\b', all_text, re.IGNORECASE))
            if count > 0:
                patterns['transitions'].append({'text': transition, 'count': count})
        
        return patterns
    
    def _extract_terminology(self, documents):
        """Extract commonly used terminology."""
        all_text = " ".join(doc['content'] for doc in documents)
        
        # Potential Dev Box specific terms
        dev_box_terms = [
            "Microsoft Dev Box", "dev box", "dev center", "developer",
            "project", "pool", "environment", "network connection", "virtual machine",
            "administrator", "Azure Active Directory", "dev box definition", "image", 
            "compute", "VM", "hybrid", "remote", "cloud", "desktop", "workspace"
        ]
        
        terminology = {}
        for term in dev_box_terms:
            count = len(re.findall(r'\b' + re.escape(term) + r'\b', all_text, re.IGNORECASE))
            if count > 0:
                terminology[term] = count
        
        # Sort by frequency
        sorted_terms = sorted(terminology.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_terms)
    
    def _extract_example_snippets(self, documents):
        """Extract example content snippets."""
        snippets = {
            'paragraphs': [],
            'instructions': [],
            'notes': [],
            'code_samples': []
        }
        
        # Sample a few paragraphs
        all_paragraphs = []
        for doc in documents:
            all_paragraphs.extend(doc['paragraphs'])
        
        if all_paragraphs:
            # Take a few representative paragraphs
            sample_size = min(5, len(all_paragraphs))
            step = len(all_paragraphs) // sample_size if len(all_paragraphs) > sample_size else 1
            for i in range(0, len(all_paragraphs), step):
                if len(snippets['paragraphs']) < sample_size:
                    snippets['paragraphs'].append(all_paragraphs[i])
        
        # Look for instruction patterns
        instruction_patterns = [
            r'\b\d+\.\s+[A-Z].*\.',  # Numbered steps
            r'\bTo\s+[a-z]+.*:',     # "To do something:" pattern
            r'\bSelect\s+.*\.',      # UI instructions
            r'\bClick\s+.*\.',
            r'\bEnter\s+.*\.',
            r'\bChoose\s+.*\.'
        ]
        
        for doc in documents:
            for pattern in instruction_patterns:
                matches = re.findall(pattern, doc['content'])
                snippets['instructions'].extend(matches[:3])  # Limit to 3 per pattern
        
        # Get notes
        for doc in documents:
            snippets['notes'].extend(doc['notes'][:3])  # Limit to 3 notes per doc
        
        # Get code samples
        for doc in documents:
            snippets['code_samples'].extend(doc['code_blocks'][:3])  # Limit to 3 samples per doc
        
        return snippets
    
    def get_style_guide(self, category=None, doc_type=None):
        """Generate a style guide based on documentation analysis."""
        categories_to_analyze = []
        
        if category and category in self.categories:
            categories_to_analyze.append(category)
        else:
            # If no specific category, analyze a few main ones
            main_categories = list(self.categories.keys())[:3] if self.categories else []
            categories_to_analyze.extend(main_categories)
        
        analyses = []
        for cat in categories_to_analyze:
            analysis = self.analyze_docs_by_category(cat)
            if analysis:
                analyses.append(analysis)
        
        if not analyses:
            return "No documentation analysis available. Using default style guidance."
        
        # Combine analyses
        combined = {
            'common_headings': [],
            'terminology': {},
            'style_patterns': {
                'avg_paragraph_length': 0,
                'avg_sentence_length': 0,
                'sentence_starters': {},
                'transitions': []
            },
            'example_snippets': {
                'paragraphs': [],
                'instructions': [],
                'notes': [],
                'code_samples': []
            }
        }
        
        # Merge analyses
        for analysis in analyses:
            # Merge common headings
            for heading in analysis['common_headings']:
                combined['common_headings'].append(heading)
            
            # Merge terminology
            for term, count in analysis['terminology'].items():
                if term not in combined['terminology']:
                    combined['terminology'][term] = 0
                combined['terminology'][term] += count
            
            # Merge style patterns
            combined['style_patterns']['avg_paragraph_length'] += analysis['style_patterns']['avg_paragraph_length']
            combined['style_patterns']['avg_sentence_length'] += analysis['style_patterns']['avg_sentence_length']
            
            for word, count in analysis['style_patterns']['sentence_starters'].items():
                if word not in combined['style_patterns']['sentence_starters']:
                    combined['style_patterns']['sentence_starters'][word] = 0
                combined['style_patterns']['sentence_starters'][word] += count
            
            for transition in analysis['style_patterns']['transitions']:
                existing = next((t for t in combined['style_patterns']['transitions'] 
                               if t['text'] == transition['text']), None)
                if existing:
                    existing['count'] += transition['count']
                else:
                    combined['style_patterns']['transitions'].append(transition.copy())
            
            # Merge snippets
            combined['example_snippets']['paragraphs'].extend(analysis['example_snippets']['paragraphs'])
            combined['example_snippets']['instructions'].extend(analysis['example_snippets']['instructions'])
            combined['example_snippets']['notes'].extend(analysis['example_snippets']['notes'])
            combined['example_snippets']['code_samples'].extend(analysis['example_snippets']['code_samples'])
        
        # Average the style metrics
        if analyses:
            combined['style_patterns']['avg_paragraph_length'] /= len(analyses)
            combined['style_patterns']['avg_sentence_length'] /= len(analyses)
        
        # Sort and limit combined data
        combined['common_headings'].sort(key=lambda x: x['count'], reverse=True)
        combined['common_headings'] = combined['common_headings'][:15]
        
        # Sort terminology by count
        sorted_terms = sorted(combined['terminology'].items(), key=lambda x: x[1], reverse=True)
        combined['terminology'] = dict(sorted_terms[:20])
        
        # Sort sentence starters by count
        sorted_starters = sorted(
            combined['style_patterns']['sentence_starters'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        combined['style_patterns']['sentence_starters'] = dict(sorted_starters[:10])
        
        # Sort transitions by count
        combined['style_patterns']['transitions'].sort(key=lambda x: x['count'], reverse=True)
        combined['style_patterns']['transitions'] = combined['style_patterns']['transitions'][:10]
        
        # Limit snippet counts
        combined['example_snippets']['paragraphs'] = combined['example_snippets']['paragraphs'][:5]
        combined['example_snippets']['instructions'] = combined['example_snippets']['instructions'][:5]
        combined['example_snippets']['notes'] = combined['example_snippets']['notes'][:5]
        combined['example_snippets']['code_samples'] = combined['example_snippets']['code_samples'][:5]
        
        return self._format_style_guide(combined, doc_type)
    
    def _format_style_guide(self, combined, doc_type=None):
        """Format the style guide as text."""        
        guide = []
        
        guide.append("# Microsoft Dev Box Documentation Style Guide")
        guide.append("\n## Document Structure")
        
        if combined['common_headings']:
            guide.append("\nCommon section headings in Microsoft Dev Box documentation:")
            for heading in combined['common_headings'][:10]:
                guide.append(f"- {heading['text']}")
        
        guide.append("\n## Terminology")
        if combined['terminology']:
            guide.append("\nCommonly used terminology in Microsoft Dev Box documentation:")
            for term, count in list(combined['terminology'].items())[:15]:
                guide.append(f"- {term}")
        
        guide.append("\n## Writing Style")
        guide.append(f"\n- Average paragraph length: {combined['style_patterns']['avg_paragraph_length']:.1f} words")
        guide.append(f"- Average sentence length: {combined['style_patterns']['avg_sentence_length']:.1f} words")
        
        if combined['style_patterns']['sentence_starters']:
            guide.append("\nCommon sentence starters:")
            for word, count in list(combined['style_patterns']['sentence_starters'].items())[:5]:
                guide.append(f"- {word}")
        
        if combined['style_patterns']['transitions']:
            guide.append("\nCommonly used transitions:")
            for transition in combined['style_patterns']['transitions'][:5]:
                guide.append(f"- {transition['text']}")
        
        guide.append("\n## Example Content")
        
        if combined['example_snippets']['paragraphs']:
            guide.append("\nExample paragraph styles:")
            for i, paragraph in enumerate(combined['example_snippets']['paragraphs'][:2], 1):
                guide.append(f"\nExample {i}: \"{paragraph[:100]}...\"")
        
        if combined['example_snippets']['instructions']:
            guide.append("\nExample instruction formats:")
            for i, instruction in enumerate(combined['example_snippets']['instructions'][:3], 1):
                guide.append(f"\nExample {i}: \"{instruction}\"")
        
        if combined['example_snippets']['notes']:
            guide.append("\nExample note formats:")
            for i, note in enumerate(combined['example_snippets']['notes'][:2], 1):
                note_preview = note[:100].replace("\n", " ")
                guide.append(f"\nExample {i}: \"{note_preview}...\"")
        
        # Add specific guidance based on document type
        if doc_type:
            guide.append(f"\n## {doc_type.upper()} Document Specific Guidance")
            
            if doc_type == 'overview':
                guide.append("\nFor OVERVIEW documents:")
                guide.append("- Begin with a clear definition of the feature/concept")
                guide.append("- Explain the benefits and use cases")
                guide.append("- Keep technical details minimal")
                guide.append("- Use diagrams where helpful")
                guide.append("- End with next steps or related features")
                
            elif doc_type == 'quickstart':
                guide.append("\nFor QUICKSTART documents:")
                guide.append("- Start with prerequisites")
                guide.append("- Use numbered steps for procedures")
                guide.append("- Keep explanations brief")
                guide.append("- Focus on the minimum steps needed")
                guide.append("- End with a verification step and next steps")
                
            elif doc_type == 'how-to':
                guide.append("\nFor HOW-TO documents:")
                guide.append("- Begin with a clear objective statement")
                guide.append("- Include detailed prerequisites")
                guide.append("- Use numbered steps with screenshots")
                guide.append("- Provide explanations for complex steps")
                guide.append("- Include troubleshooting tips")
                guide.append("- End with related tasks or next steps")
                
            elif doc_type == 'reference':
                guide.append("\nFor REFERENCE documents:")
                guide.append("- Organized in a logical structure")
                guide.append("- Comprehensive coverage of options/settings")
                guide.append("- Use tables for parameters and options")
                guide.append("- Include examples for complex items")
                guide.append("- Technical accuracy is essential")
                
            elif doc_type == 'sample':
                guide.append("\nFor SAMPLE documents:")
                guide.append("- Clear explanation of what the sample demonstrates")
                guide.append("- Include complete code samples")
                guide.append("- Add comments in code for clarity")
                guide.append("- Explain key parts of the implementation")
                guide.append("- Include expected output or results")
        
        return "\n".join(guide)

# Initialize the document analyzer as a global variable
doc_analyzer = DevBoxDocAnalyzer()

# Start a background thread to pre-fetch and analyze docs
def initialize_doc_analyzer():
    """Initialize the document analyzer in the background."""
    print("Starting background initialization of Dev Box documentation analyzer...")
    doc_analyzer.fetch_toc()
    doc_analyzer.extract_categories()
    
    # Pre-fetch a few key documents from main categories
    for category_name, docs in list(doc_analyzer.categories.items())[:3]:
        for doc_info in docs[:2]:  # Just fetch first 2 docs from each category
            doc_analyzer.fetch_document(doc_info['url'])
    
    print(f"Dev Box documentation analyzer initialized. Found {len(doc_analyzer.categories)} categories.")

# Start the background initialization
bg_init_thread = threading.Thread(target=initialize_doc_analyzer)
bg_init_thread.daemon = True
bg_init_thread.start()

def create_system_prompt(category, doc_type, enhancement_type):
    """Create a system prompt for Azure OpenAI based on enhancement parameters and documentation analysis."""    
    # Get documentation style guide
    style_guide = doc_analyzer.get_style_guide(category, doc_type)
    
    base_prompt = """You are an expert technical documentation writer for Microsoft Azure services, specifically for Microsoft Dev Box. 
You are going to enhance documentation for a Microsoft Dev Box feature to ensure it:
1. Matches Microsoft's documentation style and tone
2. Is clear, concise, and technically accurate
3. Follows proper documentation structure
4. Uses correct terminology consistent with Microsoft Dev Box documentation
5. Maintains the original markdown formatting and section structure"""

    # Add category-specific guidance
    category_guidance = {
        'overview': "This document is for the Overview section, which should provide a high-level understanding of the feature without deep technical details.",
        'deploy': "This document is for the Deploy section, which should focus on implementation steps and configuration details.",
        'get-started': "This document is for the Get Started section, which should be beginner-friendly and focus on initial setup and basic usage.",
        'cost-management': "This document is for the Dev Box Cost Management section, which should provide information on optimizing costs and understanding pricing implications.",
        'secure-access': "This document is for the Provide Secure Access section, which should focus on security best practices and access control.",
        'custom-dev-boxes': "This document is for the Create Custom Dev Boxes section, which should provide detailed guidance on customization options.",
        'support': "This document is for the Support & Reference section, which should provide troubleshooting tips, reference information, and guidance for users seeking help."
    }
    
    if category in category_guidance:
        base_prompt += f"\n\n{category_guidance[category]}"
    
    # Add documentation type-specific guidance
    doc_type_guidance = {
        'overview': "This is an OVERVIEW document that should provide a broad understanding of the feature without deep technical details.",
        'quickstart': "This is a QUICKSTART document that should provide the shortest path to success, with minimal steps and complexity.",
        'how-to': "This is a HOW-TO GUIDE that should provide practical step-by-step instructions for completing a specific task.",
        'reference': "This is a REFERENCE document that should provide detailed technical information and specifications.",
        'sample': "This is a SAMPLE document that should provide example code or configurations with explanations."
    }
    
    if doc_type in doc_type_guidance:
        base_prompt += f"\n\n{doc_type_guidance[doc_type]}"
    
    # Add enhancement type-specific guidance
    enhancement_guidance = {
        'refine': "Your task is to refine and polish the content while maintaining its basic structure and length. Focus on clarity, consistency, and correctness.",
        'expand': "Your task is to expand the content with additional helpful details, examples, and context while maintaining the original structure.",
        'technical': "Your task is to make the content more technically detailed and precise, suitable for an advanced audience of developers and IT professionals.",
        'simplify': "Your task is to simplify the content for a broader audience, using clearer language and additional explanations of technical concepts.",
        'match-style': "Your task is to ensure the content perfectly matches Microsoft's documentation style and formatting conventions. Focus on tone, terminology, and presentation."
    }
    
    if enhancement_type in enhancement_guidance:
        base_prompt += f"\n\n{enhancement_guidance[enhancement_type]}"
    
    # Add the style guide from documentation analysis
    base_prompt += f"\n\n## Microsoft Dev Box Documentation Analysis\n\n{style_guide}"
    
    # Add today's date for context
    today = datetime.datetime.now().strftime("%B %d, %Y")
    base_prompt += f"\n\nToday's date is {today}."
    
    return base_prompt

if __name__ == '__main__':
    print("Starting Azure OpenAI Documentation Enhancement Server...")
    print("Note: A browser window will open for authentication when the first request is received")
    app.run(port=SERVER_PORT, debug=DEBUG_MODE)