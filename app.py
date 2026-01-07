import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz, utils
import urllib.parse
import requests
import re
import html


def sanitize_filename(raw_name: str) -> str:
    """Unescape HTML entities repeatedly and strip HTML/div fragments in many encoded forms."""
    if raw_name is None:
        return ''
    s = str(raw_name)
    # Unescape HTML entities multiple times to handle double-encoding
    for _ in range(4):
        s = html.unescape(s)

    # Remove common numeric entity forms like &#60; and variations
    s = re.sub(r'&#\s*0*6?0?;?', '', s)

    # Remove encoded or literal div tags in many variants
    s = re.sub(r'(?i)(?:&lt;|&amp;lt;|<|\\u003c)\s*/?\s*div[^>;&]*?(?:&gt;|&amp;gt;|>|;)?', '', s)

    # Remove any remaining entity-encoded tags
    s = re.sub(r'(?i)&lt;[^&]+&gt;', '', s)

    # Remove any normal HTML tags
    s = re.sub(r'<[^>]+>', '', s)

    # Trim whitespace
    return s.strip()


# Page configuration
st.set_page_config(
    page_title="Past Paper Vault",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def get_pdf_icon_svg():
    """Return PDF icon SVG"""
    return """
    <svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="60" height="60" rx="8" fill="#db463b"/>
        <path d="M18 15h14l8 8v22H18V15z" fill="white"/>
        <path d="M32 15v8h8" stroke="#db463b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M22 28h16M22 35h12M22 42h16" stroke="#09262e" stroke-width="2" stroke-linecap="round"/>
    </svg>
    """


# Custom CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700&family=Poppins:wght@300;400;500;600&display=swap');
    
    .main {
        background-color: #09262e;
        padding: 2rem;
        font-family: 'Poppins', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stTextInput>div>div>input {
        background-color: #ffffff;
        color: #09262e;
        border-radius: 8px;
        border: 2px solid #db463b;
        font-family: 'Poppins', sans-serif;
        font-size: 16px;
        padding: 12px;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #db463b;
        box-shadow: 0 0 0 3px rgba(219, 70, 59, 0.1);
    }
    
    .stButton>button {
        background-color: #db463b;
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
        font-size: 16px;
        padding: 12px 24px;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #c03a2b;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(219, 70, 59, 0.3);
    }
    
    .stDownloadButton>button {
        background-color: #28a745;
        color: white;
    }
    
    .stDownloadButton>button:hover {
        background-color: #218838;
    }
    
    .pdf-tile {
        background: rgba(255,255,255,0.02);
        border-radius: 12px;
        padding: 18px;
        margin: 10px 0;
        transition: all 0.18s;
        border: 1px solid rgba(255,255,255,0.03);
    }

    .pdf-tile:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
        border-color: rgba(219, 70, 59, 0.25);
    }

    .pdf-icon {
        width: 60px;
        height: 60px;
        margin: 0 auto 12px;
        display: block;
        text-align: center;
    }

    .pdf-name {
        font-family: 'Poppins', sans-serif;
        font-weight: 500;
        font-size: 15px;
        color: #ffffff;
        text-align: center;
        margin-bottom: 8px;
        line-height: 1.3;
        min-height: 40px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    h1 {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 3rem;
        letter-spacing: 2px;
    }
    
    @media (max-width: 768px) {
        .main {
            padding: 0.3rem;
        }
        h1 {
            font-size: 1.8rem;
        }
        .pdf-tile {
            margin: 4px 0;
            padding: 10px;
        }
        /* Mobile title - bigger font */
        .vault-title {
            font-size: 2rem !important;
            letter-spacing: 1px !important;
            margin-bottom: 0.1rem !important;
            margin-top: 0 !important;
        }
        .vault-subtitle {
            font-size: 0.75rem !important;
            margin-bottom: 0 !important;
        }
        .title-container {
            margin-bottom: 0.4rem !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        /* Smaller PDF icon on mobile */
        .pdf-icon {
        .pdf-icon {
            width: 40px;
            height: 40px;
            margin-bottom: 8px;
        }
        .pdf-icon svg {
            width: 40px;
            height: 40px;
        }
        /* Smaller filename text on mobile */
        .pdf-name {
            font-size: 12px;
            min-height: 30px;
            margin-bottom: 4px;
        }
        /* Welcome text smaller on mobile */
        .welcome-text {
            padding: 1rem 0.5rem !important;
        }
        .welcome-text h2 {
            font-size: 1.3rem !important;
        }
        .welcome-text p {
            font-size: 0.9rem !important;
            margin-bottom: 1rem !important;
        }
        /* No results text smaller */
        .no-results {
            padding: 1rem 0.5rem !important;
        }
        .no-results h2 {
            font-size: 1.3rem !important;
        }
        .no-results p {
            font-size: 0.9rem !important;
        }
        /* Reduce button font size */
        .stButton>button {
            font-size: 13px;
            padding: 8px 12px;
        }
        /* Search input smaller */
        .stTextInput>div>div>input {
            font-size: 14px;
            padding: 8px;
        }
        /* Reduce column gaps */
        .stColumns {
            gap: 0.3rem !important;
        }
        /* Match score badge smaller */
        .match-badge {
            font-size: 10px !important;
            padding: 2px 6px !important;
        }
    }
    
    /* Space for fixed social bar at bottom */
    .main .block-container {
        padding-bottom: 70px !important;
    }
    
    /* Reduce top padding on mobile */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem !important;
        }
        .main {
            padding-top: 0 !important;
        }
        /* Remove Streamlit default header */
        .stApp > header,
        [data-testid="stHeader"] {
            display: none !important;
        }
        .stApp {
            padding-top: 0 !important;
        }
        [data-testid="stAppViewContainer"] {
            padding-top: 0 !important;
        }
        section.main {
            padding-top: 0 !important;
        }
        .block-container {
            padding-top: 1rem !important;
        }
    }
    </style>
    
    <!-- Social Bar Ad - Fixed at bottom of viewport -->
    <script>
    (function() {
        if (document.getElementById('fixed-social-bar-container')) return;
        var container = document.createElement('div');
        container.id = 'fixed-social-bar-container';
        container.style.cssText = 'position: fixed; bottom: 0; left: 0; width: 100%; z-index: 999999; text-align: center; background: rgba(9, 38, 46, 0.95); padding: 5px 0; box-shadow: 0 -2px 10px rgba(0,0,0,0.3);';
        var script = document.createElement('script');
        script.src = 'https://levitydinerdowny.com/f3/2b/9c/f32b9c36b68689794113c5a42fa355c8.js';
        container.appendChild(script);
        document.body.appendChild(container);
    })();
    </script>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_master_index():
    """Load the master index CSV file with caching for performance."""
    try:
        csv_path = 'master_index.csv'
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        
        # Normalize column names
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'file' in col_lower and 'name' in col_lower:
                column_mapping[col] = 'File Name'
            elif 'file' in col_lower and 'id' in col_lower:
                column_mapping[col] = 'File ID'
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        if 'File Name' not in df.columns and len(df.columns) >= 1:
            df = df.rename(columns={df.columns[0]: 'File Name'})
        if 'File ID' not in df.columns and len(df.columns) >= 2:
            df = df.rename(columns={df.columns[1]: 'File ID'})
        
        return df
    except FileNotFoundError:
        st.error("❌ master_index.csv file not found!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading master_index.csv: {str(e)}")
        return pd.DataFrame()


def normalize_text(text):
    """Normalize text for better matching."""
    if not text:
        return ""
    text = str(text).lower()
    # Normalize exam levels
    text = re.sub(r'\ba/l\b', 'al', text, flags=re.IGNORECASE)
    text = re.sub(r'\ba\s*l\b', 'al', text, flags=re.IGNORECASE)
    text = re.sub(r'\badvanced?\s+level\b', 'al', text, flags=re.IGNORECASE)
    text = re.sub(r'\bo/l\b', 'ol', text, flags=re.IGNORECASE)
    text = re.sub(r'\bo\s*l\b', 'ol', text, flags=re.IGNORECASE)
    text = re.sub(r'\bordinary\s+level\b', 'ol', text, flags=re.IGNORECASE)
    # Replace separators with spaces
    text = re.sub(r'[_\-\.,;:()\[\]{}]', ' ', text)
    # Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def fuzzy_search(query, df, limit=50):
    """Perform intelligent hierarchical search with strict subject filtering.
    
    Query Pattern: {year} {exam type} {Subject} {pastpaper/marking} {medium}
    
    Search Strategy:
    1. FILTER by subject (MANDATORY - if no match, return empty for "content uploading" message)
    2. SORT by year (exact match first, then by proximity)
    3. SORT by document type (marking/paper based on query)
    4. SORT by medium (exact match first)
    """
    if df.empty or query.strip() == "":
        return pd.DataFrame()
    
    # Find the file name column
    file_name_col = None
    for col in df.columns:
        if 'file' in col.lower() and 'name' in col.lower():
            file_name_col = col
            break
    
    if file_name_col is None:
        file_name_col = df.columns[0]
    
    query_lower = normalize_text(query)
    query_words = set(query_lower.split())
    
    # Extract year patterns from query
    query_years = set(re.findall(r'\b(19\d{2}|20\d{2})\b', query))
    
    # Define categories with priority weights
    # Include common abbreviations and full names
    subjects = [
        'physics', 'chemistry', 'chem', 'biology', 'bio', 'mathematics', 'maths', 'math',
        'combined', 'commerce', 'history', 'geography', 'geo', 'economics', 'econ',
        'accounting', 'accounts', 'science', 'ict', 'technology', 'buddhism', 'hinduism',
        'islam', 'christianity', 'art', 'music', 'drama', 'dancing', 'agriculture', 'agri',
        'business', 'botany', 'zoology', 'logic', 'statistics', 'stats', 'political',
        'sft', 'git', 'egt', 'bst', 'est',  # Common subject codes
        'general', 'knowledge', 'gk'  # General knowledge
    ]
    mediums = ['sinhala', 'tamil', 'english']
    levels = ['al', 'ol', 'grade', 'a/l', 'o/l']
    doc_types = ['marking', 'scheme', 'paper', 'pastpaper', 'past', 'mcq', 'essay']
    
    # Extract query components
    query_subjects = set([word for word in query_words if word in subjects])
    query_mediums = set([word for word in query_words if word in mediums])
    query_levels = set([word for word in query_words if word in levels])
    query_doc_types = set([word for word in query_words if word in doc_types])
    
    # STEP 1: STRICT SUBJECT FILTERING
    # If query has a subject, ONLY keep files that CONTAIN that exact subject
    # FALLBACK: If no subject matches found, show files matching exam level (A/L, O/L)
    filtered_results = []
    fallback_results = []
    
    for idx, row in df.iterrows():
        filename = str(row[file_name_col])
        filename_lower = normalize_text(filename)
        filename_words = set(filename_lower.split())
        
        # Extract components from filename
        file_years = set(re.findall(r'\b(19\d{2}|20\d{2})\b', filename_lower))
        file_subjects = set([word for word in filename_words if word in subjects])
        file_mediums = set([word for word in filename_words if word in mediums])
        file_doc_types = set([word for word in filename_words if word in doc_types])
        file_levels = set([word for word in filename_words if word in levels])
        
        # MANDATORY SUBJECT CHECK - STRICT MODE
        if query_subjects:
            # Check if file contains the queried subject
            has_matching_subject = bool(query_subjects & file_subjects)
            
            if has_matching_subject:
                pass  # Will add to filtered_results below
            else:
                # NOT matching subject - add to fallback only if level matches
                if query_levels and file_levels and (query_levels & file_levels):
                    fallback_results.append({
                        'index': idx,
                        'filename': filename,
                        'year_match': 9999,
                        'doc_type_match': 1,
                        'medium_match': 1,
                        'word_match': 0
                    })
                continue  # Skip to next file - DO NOT add to filtered_results
        
        # Calculate sorting keys for hierarchical sort
        
        # Sort Key 1: Year Match (0 = perfect, higher = worse)
        year_match_score = 9999  # Default: no year
        if query_years and file_years:
            query_year = int(list(query_years)[0])
            closest_file_year = min(file_years, key=lambda y: abs(int(y) - query_year))
            year_match_score = abs(int(closest_file_year) - query_year)
        elif query_years and not file_years:
            year_match_score = 9998  # Has query year but file doesn't - lower priority
        elif not query_years and file_years:
            year_match_score = 100  # No query year but file has year - decent priority
        
        # Sort Key 2: Document Type Match (0 = perfect match, 1 = no match)
        doc_type_match = 1 if query_doc_types else 0
        if query_doc_types and file_doc_types:
            doc_type_match = 0 if (query_doc_types & file_doc_types) else 1
        
        # Sort Key 3: Medium Match (0 = perfect match, 1 = no match)
        medium_match = 1 if query_mediums else 0
        if query_mediums and file_mediums:
            medium_match = 0 if (query_mediums & file_mediums) else 1
        
        # Sort Key 4: Overall relevance (word matches)
        common_words = query_words & filename_words
        word_match_count = -len(common_words)  # Negative for descending sort
        
        result_entry = {
            'index': idx,
            'filename': filename,
            'year_match': year_match_score,
            'doc_type_match': doc_type_match,
            'medium_match': medium_match,
            'word_match': word_match_count
        }
        
        # Add to filtered_results (only reaches here if subject matched or no subject in query)
        filtered_results.append(result_entry)
    
    # Use fallback only if no subject matches found
    if not filtered_results and fallback_results:
        filtered_results = fallback_results
    
    # STEP 2: HIERARCHICAL SORT
    # Sort by: Year (ascending) → Doc Type (ascending) → Medium (ascending) → Word matches (descending)
    filtered_results.sort(key=lambda x: (x['year_match'], x['doc_type_match'], x['medium_match'], x['word_match']))
    
    # Limit results
    top_results = filtered_results[:limit]
    
    if not top_results:
        return pd.DataFrame()
    
    # Get corresponding rows
    top_indices = [r['index'] for r in top_results]
    results = df.loc[top_indices].copy()
    
    # Calculate match percentage for display
    match_scores = []
    for r in top_results:
        # Perfect match = 100%, decreases with year diff, doc type, medium mismatch
        score = 100.0
        
        # Year penalty: -5% per year difference
        if r['year_match'] < 9990:
            score -= min(r['year_match'] * 5, 50)
        
        # Doc type penalty: -10% if mismatch
        if r['doc_type_match'] == 1:
            score -= 10
        
        # Medium penalty: -15% if mismatch
        if r['medium_match'] == 1:
            score -= 15
        
        match_scores.append(max(score, 10.0))  # Minimum 10%
    
    results['Match Score'] = match_scores
    
    # Preserve the sort order (already sorted hierarchically)
    results = results.reset_index(drop=True)
    
    return results


def get_telegram_file_content(file_id, bot_token):
    """Download file content from Telegram and return bytes."""
    try:
        # Validate inputs
        if not bot_token:
            return None, "❌ Telegram Bot Token not configured."
        
        file_id_str = str(file_id).strip()
        if not file_id_str:
            return None, "❌ Invalid file ID: File ID is empty."
        
        # Get file path from Telegram
        api_url = f"https://api.telegram.org/bot{bot_token}/getFile"
        params = {"file_id": file_id_str}
        
        response = requests.get(api_url, params=params, timeout=10)
        result = response.json()
        
        if not result.get("ok"):
            error_description = result.get("description", "Unknown error")
            error_code = result.get("error_code", "N/A")
            return None, f"❌ Telegram API error ({error_code}): {error_description}"
        
        file_path = result["result"]["file_path"]
        
        # Download the file content
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        file_response = requests.get(download_url, timeout=30)
        file_response.raise_for_status()
        
        return file_response.content, None
    
    except requests.exceptions.Timeout:
        return None, "❌ Request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return None, f"❌ Network error: {str(e)}"
    except KeyError as e:
        return None, f"❌ Unexpected API response format: {str(e)}"
    except Exception as e:
        return None, f"❌ Error downloading file: {str(e)}"


def main():
    # Initialize session state
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'download_cache' not in st.session_state:
        st.session_state.download_cache = {}
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Show loading screen while data loads
    loading_placeholder = st.empty()
    
    if not st.session_state.data_loaded:
        with loading_placeholder.container():
            st.markdown("""
            <style>
            .loading-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 60vh;
                text-align: center;
            }
            .loading-icon {
                font-size: 4rem;
                animation: bounce 1s ease-in-out infinite;
            }
            .loading-text {
                font-family: 'Barlow Condensed', sans-serif;
                font-size: 1.8rem;
                color: #ffffff;
                margin-top: 1rem;
                letter-spacing: 2px;
            }
            .loading-subtext {
                font-family: 'Poppins', sans-serif;
                font-size: 1rem;
                color: #db463b;
                margin-top: 0.5rem;
                opacity: 0.9;
            }
            .loading-dots {
                display: inline-block;
            }
            .loading-dots::after {
                content: '';
                animation: dots 1.5s steps(4, end) infinite;
            }
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-15px); }
            }
            @keyframes dots {
                0% { content: ''; }
                25% { content: '.'; }
                50% { content: '..'; }
                75% { content: '...'; }
                100% { content: ''; }
            }
            .loading-spinner {
                width: 50px;
                height: 50px;
                border: 4px solid rgba(219, 70, 59, 0.3);
                border-top: 4px solid #db463b;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 1.5rem auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            </style>
            <div class="loading-container">
                <div class="loading-icon">📚</div>
                <div class="loading-text">Loading Your PDFs<span class="loading-dots"></span></div>
                <div class="loading-spinner"></div>
                <div class="loading-subtext">Preparing thousands of past papers for you</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Title
    st.markdown("""
    <div class="title-container" style="text-align: center; margin-bottom: 0.8rem;">
        <h1 class="vault-title" style="font-family: 'Barlow Condensed', sans-serif; font-weight: 700; color: #ffffff; font-size: 3rem; letter-spacing: 3px; margin-bottom: 0.3rem;">📚 PAST PAPER VAULT</h1>
        <p class="vault-subtitle" style="font-family: 'Poppins', sans-serif; color: #db463b; font-size: 0.85rem; font-weight: 400; letter-spacing: 1px; margin-top: 0;">powered by <strong>Examlanka.lk</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Native Banner Ad
    import streamlit.components.v1 as components
    components.html("""
    <div style="text-align: center; margin: 0.3rem auto; max-width: 100%;">
        <script>
          atOptions = {
            'key' : '8147f01382ece9e1740ef1187319a8b7',
            'format' : 'iframe',
            'height' : 90,
            'width' : 728,
            'params' : {}
          };
        </script>
        <script src="https://levitydinerdowny.com/8147f01382ece9e1740ef1187319a8b7/invoke.js"></script>
    </div>
    """, height=95)
    
    # Check for bot token
    try:
        bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            st.error("❌ Telegram Bot Token not configured. Please add it to .streamlit/secrets.toml")
            st.stop()
    except Exception as e:
        st.error(f"❌ Error accessing secrets: {str(e)}")
        st.stop()
    
    # Load data
    df = load_master_index()
    
    # Clear loading screen once data is loaded
    if not st.session_state.data_loaded:
        st.session_state.data_loaded = True
        loading_placeholder.empty()
    
    if df.empty:
        st.warning("⚠️ No data available. Please ensure master_index.csv is present.")
        return
    
    # Get query parameter from URL
    query_params = st.query_params
    url_query = query_params.get("q", "")
    if url_query:
        url_query = urllib.parse.unquote_plus(url_query)
        if url_query != st.session_state.search_query:
            st.session_state.search_query = url_query
    
    # Search interface
    col1, col2, col3, col4 = st.columns([1, 4, 0.8, 1])
    with col2:
        search_query = st.text_input(
            "Search",
            value=st.session_state.search_query,
            placeholder="Search for past papers... (e.g., physics 2021, mathematics, chemistry)",
            key="search_input",
            label_visibility="collapsed"
        )
    with col3:
        st.write("")
        search_button = st.button(
            "🔍 Search",
            key="search_btn",
            use_container_width=True,
            type="primary"
        )
    
    # Handle search
    if search_button or search_query != st.session_state.search_query:
        st.session_state.search_query = search_query
        st.session_state.download_cache = {}  # Clear download cache on new search
    
    # Display results
    if st.session_state.search_query:
        with st.spinner('🔍 Searching for your past papers... Please wait'):
            results = fuzzy_search(st.session_state.search_query, df, limit=30)

        if not results.empty:
            file_name_col = [col for col in results.columns if 'file' in col.lower() and 'name' in col.lower()]
            file_id_col = [col for col in results.columns if 'file' in col.lower() and 'id' in col.lower()]

            file_name_col = file_name_col[0] if file_name_col else results.columns[0]
            file_id_col = file_id_col[0] if file_id_col else results.columns[1]

            num_cols = 3
            cols = st.columns(num_cols)

            for idx, (row_idx, row) in enumerate(results.iterrows()):
                file_name = row[file_name_col]
                file_id = str(row[file_id_col])
                match_score = row.get('Match Score', 0)

                # Clean filename
                raw_name = str(file_name)
                cleaned = sanitize_filename(raw_name)
                display_name = html.escape(cleaned.replace('_', ' ').replace('-', ' '))
                
                col_idx = idx % num_cols

                with cols[col_idx]:
                    # Render tile
                    tile_html = f"""
                    <div class="pdf-tile">
                        <div class="pdf-icon">{get_pdf_icon_svg()}</div>
                        <div class="pdf-name">{display_name}</div>
                        <div style='text-align:center; margin-top:4px;'>
                            <span class="match-badge" style='background-color: rgba(219, 70, 59, 0.2); color: #db463b; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;'>Match: {match_score:.1f}%</span>
                        </div>
                    </div>
                    """
                    st.markdown(tile_html, unsafe_allow_html=True)
                    
                    # Download button with caching
                    cache_key = f"file_content_{file_id}"
                    
                    if cache_key in st.session_state.download_cache:
                        # File already downloaded, show download button
                        file_content, error = st.session_state.download_cache[cache_key]
                        if error:
                            st.error(error)
                        else:
                            filename = cleaned if cleaned.lower().endswith('.pdf') else f"{cleaned}.pdf"
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=file_content,
                                file_name=filename,
                                mime="application/pdf",
                                use_container_width=True,
                                key=f"download_{file_id}_{idx}"
                            )
                    else:
                        # Prepare download button
                        if st.button("📥 Prepare Download", key=f"prepare_{file_id}_{idx}", use_container_width=True):
                            with st.spinner("⏳ Preparing your download... Please wait"):
                                file_content, error = get_telegram_file_content(file_id, bot_token)
                                st.session_state.download_cache[cache_key] = (file_content, error)
                                st.rerun()
        else:
            st.markdown("""
            <div class="no-results" style="text-align: center; padding: 2rem 1rem; color: #ffffff;">
                <h2 style="font-family: 'Barlow Condensed', sans-serif; font-size: 1.8rem; margin-bottom: 1rem;">� Content Still Uploading</h2>
                <p style="font-family: 'Poppins', sans-serif; font-size: 1rem;">The papers you're looking for are not available yet. Please try again later or search for a different subject.</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Welcome message
        st.markdown("""
        <div class="welcome-text" style="text-align: center; padding: 2rem 1rem; color: #ffffff;">
            <h2 style="font-family: 'Barlow Condensed', sans-serif; font-size: 2rem; margin-bottom: 1rem; letter-spacing: 2px;">Welcome to Past Paper Vault</h2>
            <p style="font-family: 'Poppins', sans-serif; font-size: 1rem; margin-bottom: 1.5rem; opacity: 0.9;">Search for past papers by subject, year, or school</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Statistics
        st.markdown("""
        <style>
        .stMetric {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid rgba(219, 70, 59, 0.3);
        }
        .stMetric label {
            color: #ffffff;
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
        }
        .stMetric [data-testid="stMetricValue"] {
            color: #db463b;
            font-family: 'Barlow Condensed', sans-serif;
            font-weight: 700;
            font-size: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Papers", len(df))
        with col2:
            try:
                unique_count = df['File Name'].nunique() if 'File Name' in df.columns else len(df)
            except:
                unique_count = len(df)
            st.metric("Unique Files", unique_count)
        with col3:
            st.metric("Status", "🟢 Active")


if __name__ == "__main__":
    main()
