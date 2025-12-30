import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz, utils
from telegram import Bot
from telegram.error import TelegramError
import urllib.parse
import asyncio
import concurrent.futures
import requests
import re

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

# Custom CSS with new design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700&family=Poppins:wght@300;400;500;600&display=swap');
    
    /* Main styling */
    .main {
        background-color: #09262e;
        padding: 2rem;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Search bar styling */
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
    
    /* Button styling */
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
    
    /* Search button with icon */
    .search-btn {
        background-color: #db463b;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s;
        cursor: pointer;
    }
    
    .search-btn:hover {
        background-color: #c03a2b;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(219, 70, 59, 0.3);
    }
    
    .search-icon {
        width: 20px;
        height: 20px;
    }
    
    /* Search button icon styling */
    button[kind="secondary"] {
        background-color: #db463b !important;
        color: white !important;
        border: none !important;
    }
    
    button[kind="secondary"]:hover {
        background-color: #c03a2b !important;
    }
    
    /* PDF Tile styling (dark theme) */
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
    
    .download-btn {
        width: 100%;
        background-color: #db463b;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .download-btn:hover {
        background-color: #c03a2b;
    }
    
    /* Title styling */
    h1 {
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 3rem;
        letter-spacing: 2px;
    }
    
    /* Form button styling */
    .stForm {
        background-color: transparent;
    }
    
    .stForm button {
        background-color: #db463b;
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Barlow Condensed', sans-serif;
        font-weight: 600;
    }
    
    /* Markdown links */
    a {
        color: #db463b;
        text-decoration: none;
    }
    
    a:hover {
        color: #c03a2b;
        text-decoration: underline;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main {
            padding: 1rem;
        }
        h1 {
            font-size: 2rem;
        }
        .pdf-tile {
            margin: 5px;
            padding: 15px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cache for 1 hour, or clear cache when CSV changes
def load_master_index():
    """Load the master index CSV file with caching for performance."""
    try:
        # Read CSV and get file modification time to invalidate cache on changes
        import os
        csv_path = 'master_index.csv'
        df = pd.read_csv(csv_path)
        # Handle column names with spaces - normalize to 'File Name' and 'File ID'
        df.columns = df.columns.str.strip()
        # Normalize column names (handle variations like 'File Name', 'File_Name', etc.)
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if 'file' in col_lower and 'name' in col_lower:
                column_mapping[col] = 'File Name'
            elif 'file' in col_lower and 'id' in col_lower:
                column_mapping[col] = 'File ID'
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Ensure we have the required columns, if not, try to infer
        if 'File Name' not in df.columns and len(df.columns) >= 1:
            # Use first column as File Name if not found
            first_col = df.columns[0]
            if 'File Name' not in column_mapping.values():
                df = df.rename(columns={first_col: 'File Name'})
        if 'File ID' not in df.columns and len(df.columns) >= 2:
            # Use second column as File ID if not found
            second_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            if 'File ID' not in column_mapping.values():
                df = df.rename(columns={second_col: 'File ID'})
        return df
    except FileNotFoundError:
        st.error("❌ master_index.csv file not found!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading master_index.csv: {str(e)}")
        return pd.DataFrame()

def normalize_exam_levels(text):
    """Normalize all variations of exam levels to a standard form.
    Converts: A/L, AL, A L, Advanced Level, Advance Level -> al
    """
    if not text:
        return text
    
    # Patterns to match and replace (case-insensitive)
    # All variations of Advanced Level -> al
    patterns = [
        (r'\ba/l\b', 'al'),  # A/L -> al
        (r'\ba\s*l\b', 'al'),  # A L -> al (with space)
        (r'\badvanced\s+level\b', 'al'),  # Advanced Level -> al
        (r'\badvance\s+level\b', 'al'),  # Advance Level -> al
        (r'\badv\s+level\b', 'al'),  # Adv Level -> al
    ]
    
    # Apply patterns (text should already be lowercase when called)
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

def normalize_text(text):
    """Normalize text for better matching: lowercase, remove special chars, normalize spaces."""
    if not text:
        return ""
    # Convert to lowercase first
    text = str(text).lower()
    # Normalize exam level variations (A/L, AL, A L, Advanced Level -> al)
    text = normalize_exam_levels(text)
    # Replace common separators with spaces
    text = re.sub(r'[_\-\.,;:()\[\]{}]', ' ', text)
    # Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_year_from_filename(filename):
    """Extract year from filename (4-digit numbers like 2024, 2025)."""
    filename_lower = normalize_text(filename)
    years = re.findall(r'\b(19\d{2}|20\d{2})\b', filename_lower)
    if years:
        # Return the most recent year if multiple found
        return max(years)
    return None

def extract_subject_from_filename(filename):
    """Extract subject from filename."""
    filename_lower = normalize_text(filename)
    subjects = [
        'physics', 'chemistry', 'mathematics', 'maths', 'biology', 'history', 'geography', 
        'economics', 'accounting', 'business studies', 'business', 'ict', 'computer science', 'computer', 
        'combined mathematics', 'combined', 'applied', 'mechanical technology', 'mechanical', 'technology',
        'bio resource technology', 'bio resource', 'bio systems technology', 'bio systems',
        'engineering technology', 'engineering', 'science for technology', 'science',
        'agriculture', 'agricultural', 'food technology', 'food', 'home economics', 'home',
        'communication and media', 'communication', 'media', 'dancing', 'drama', 'art', 'music',
        'sinhala', 'tamil', 'english', 'pali', 'sanskrit', 'arabic', 'chinese', 'japanese', 'french', 'german',
        'islam civilization', 'islam', 'buddhist civilization', 'buddhist', 'christian civilization', 'christian',
        'hindu civilization', 'hindu', 'catholic', 'statistics', 'logic', 'philosophy', 'psychology',
        'political science', 'political', 'sociology', 'anthropology', 'geography', 'history'
    ]
    
    # Sort by length (longest first) to match more specific subjects first
    subjects_sorted = sorted(subjects, key=len, reverse=True)
    
    for subject in subjects_sorted:
        if subject in filename_lower:
            # Capitalize each word
            return ' '.join(word.capitalize() for word in subject.split())
    
    return "Other"

def extract_medium_from_filename(filename):
    """Extract medium/language from filename."""
    filename_lower = normalize_text(filename)
    mediums = {
        'Sinhala': ['sinhala', 'sinhalese', 's'],
        'Tamil': ['tamil', 't'],
        'English': ['english', 'eng', 'e']
    }
    
    for medium, variants in mediums.items():
        if any(v in filename_lower for v in variants):
            return medium
    
    return None

def extract_keywords(query):
    """Extract meaningful keywords from query, filtering out common words."""
    # Common words to ignore (can be expanded)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from'}
    words = normalize_text(query).split()
    # Filter out stop words and very short words (unless query is very short)
    keywords = [w for w in words if len(w) > 2 or len(words) <= 3]
    keywords = [w for w in keywords if w not in stop_words or len(words) <= 2]
    return keywords if keywords else words  # Return all words if all were filtered

def calculate_relevance_score(query, filename, query_keywords):
    """Calculate relevance score and prime-match flag.
    Prime-match: if average of present components (year, subject, medium)
    is >= 90%. Returns (score, prime_flag).
    """
    query_lower = normalize_text(query)
    filename_lower = normalize_text(filename)

    # Extract years from query and filename (4-digit numbers like 2024, 2025)
    query_years = set(re.findall(r'\b(19\d{2}|20\d{2})\b', query_lower))
    filename_years = set(re.findall(r'\b(19\d{2}|20\d{2})\b', filename_lower))

    # Extract medium/language from query and filename
    mediums = {
        'sinhala': ['sinhala', 'sinhalese', 's'],
        'tamil': ['tamil', 't'],
        'english': ['english', 'eng', 'e']
    }

    query_mediums = set()
    for medium, variants in mediums.items():
        if any(v in query_lower for v in variants):
            query_mediums.add(medium)

    filename_mediums = set()
    for medium, variants in mediums.items():
        if any(v in filename_lower for v in variants):
            filename_mediums.add(medium)

    # Extract subject keywords (limited set used for scoring)
    subjects = ['physics', 'chemistry', 'mathematics', 'maths', 'biology', 'history', 'geography',
                'economics', 'accounting', 'business', 'ict', 'computer', 'combined', 'applied',
                'mechanical', 'technology', 'statistics']

    query_subjects = [s for s in subjects if s in query_lower]
    filename_subjects = [s for s in subjects if s in filename_lower]

    # Compute component percentages (0 or 100 for presence match)
    year_pct = None
    if query_years:
        if filename_years and query_years.intersection(filename_years):
            year_pct = 100
        else:
            year_pct = 0

    subject_pct = None
    if query_subjects:
        if filename_subjects and any(qs in filename_subjects for qs in query_subjects):
            subject_pct = 100
        else:
            subject_pct = 0

    medium_pct = None
    if query_mediums:
        if filename_mediums and query_mediums.intersection(filename_mediums):
            medium_pct = 100
        else:
            medium_pct = 0

    # Other keywords contribution (scaled to 100)
    other_keywords = []
    for kw in query_keywords:
        if re.match(r'^(19\d{2}|20\d{2})$', kw):
            continue
        if any(kw in variants for variants in mediums.values()):
            continue
        if kw in subjects:
            continue
        other_keywords.append(kw)

    other_pct = None
    if other_keywords:
        other_found = sum(1 for kw in other_keywords if kw in filename_lower)
        other_pct = int((other_found / len(other_keywords)) * 100)

    # Base score: weighted combination with heavier weights for year/subject/medium
    score = 0.0
    if year_pct is not None:
        score += (year_pct / 100.0) * 40
    if subject_pct is not None:
        score += (subject_pct / 100.0) * 40
    if medium_pct is not None:
        score += (medium_pct / 100.0) * 20
    if other_pct is not None:
        score += (other_pct / 100.0) * 20

    # Fuzzy bonus for overall phrase if score already decent
    if score > 30:
        token_sort_score = fuzz.token_sort_ratio(query_lower, filename_lower)
        score += token_sort_score * 0.05

    score = max(0, min(score, 100))

    # Determine prime-match based on average of present components
    present_components = [v for v in (year_pct, subject_pct, medium_pct) if v is not None]
    prime_flag = False
    if present_components:
        avg_present = sum(present_components) / len(present_components)
        if avg_present >= 90:
            prime_flag = True

    return score, prime_flag

def fuzzy_search(query, df, limit=20):
    """Perform intelligent fuzzy search with relevance-based scoring."""
    if df.empty or query.strip() == "":
        return pd.DataFrame()
    
    # Find the file name column (handle variations)
    file_name_col = None
    for col in df.columns:
        if 'file' in col.lower() and 'name' in col.lower():
            file_name_col = col
            break
    
    if file_name_col is None:
        # Fallback: use first column if no file name column found
        file_name_col = df.columns[0]
    
    # Extract keywords and core elements from query
    query_keywords = extract_keywords(query)
    query_lower = normalize_text(query)
    # Extract year(s) and medium(s) from query
    query_years = set(re.findall(r'\b(19|20)\d{2}\b', query_lower))
    mediums = {
        'sinhala': ['sinhala', 'sinhalese', 's'],
        'tamil': ['tamil', 't'],
        'english': ['english', 'eng', 'e']
    }
    query_mediums = set()
    for medium, variants in mediums.items():
        if any(v in query_lower for v in variants):
            query_mediums.add(medium)

    # Hard filter: if year or medium is present in query, only show files that match
    filtered_df = df.copy()
    if query_years:
        # Only keep rows where any year in query_years is in the filename
        filtered_df = filtered_df[filtered_df[file_name_col].str.contains('|'.join(query_years), case=False, na=False)]
        # If nothing matches, fall back to original df
        if filtered_df.empty:
            filtered_df = df.copy()
    if query_mediums:
        # Only keep rows where any medium in query_mediums is in the filename
        medium_pattern = '|'.join([v for m in query_mediums for v in mediums[m]])
        filtered_df = filtered_df[filtered_df[file_name_col].str.contains(medium_pattern, case=False, na=False)]
        if filtered_df.empty:
            filtered_df = df.copy()

    # Calculate relevance scores for all files in filtered_df
    scored_results = []
    for idx, row in filtered_df.iterrows():
        filename = row[file_name_col]
        score, prime = calculate_relevance_score(query, filename, query_keywords)
        scored_results.append({
            'index': row.name,
            'score': score,
            'prime': prime,
            'filename': filename
        })

    # Sort by prime flag then by score (prime matches first)
    scored_results.sort(key=lambda x: (x['prime'], x['score']), reverse=True)
    top_results = scored_results[:limit * 3]

    # Filter out results with very low scores (below 15 for better relevance)
    top_results = [r for r in top_results if r['score'] >= 15]
    top_results = top_results[:limit]
    
    if not top_results:
        return pd.DataFrame()
    
    # Get the corresponding rows from dataframe
    top_indices = [r['index'] for r in top_results]
    results = df.loc[top_indices].copy()

    # Add match scores and prime flag
    score_dict = {r['filename']: r['score'] for r in top_results}
    prime_dict = {r['filename']: r['prime'] for r in top_results}
    results['Match Score'] = results[file_name_col].map(score_dict)
    results['Prime Match'] = results[file_name_col].map(prime_dict)

    # Sort by prime flag then by match score
    results = results.sort_values(['Prime Match', 'Match Score'], ascending=[False, False])

    return results

def get_telegram_download_url(file_id):
    """Get the direct download URL for a Telegram file using Bot API."""
    try:
        # Get bot token from Streamlit secrets
        bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            st.error("❌ Telegram Bot Token not configured. Please set it in Streamlit secrets.")
            return None
        
        # Validate file_id
        file_id_str = str(file_id).strip()
        if not file_id_str:
            st.error("❌ Invalid file ID: File ID is empty.")
            return None
        
        # Use Telegram Bot API directly via HTTP
        api_url = f"https://api.telegram.org/bot{bot_token}/getFile"
        params = {"file_id": file_id_str}
        
        response = requests.get(api_url, params=params, timeout=10)
        
        # Get the JSON response to check for errors
        result = response.json()
        
        if not result.get("ok"):
            error_description = result.get("description", "Unknown error")
            error_code = result.get("error_code", "N/A")
            raise Exception(f"Telegram API error ({error_code}): {error_description}")
        
        # If we get here, the request was successful
        response.raise_for_status()
        
        file_path = result["result"]["file_path"]
        
        # Construct direct download URL
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        
        return download_url
    
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        # Try to get more details from the response if available
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                if not error_data.get("ok"):
                    error_desc = error_data.get("description", "Unknown error")
                    error_code = error_data.get("error_code", "N/A")
                    st.error(f"❌ Telegram API Error ({error_code}): {error_desc}")
                    if "file_id" in error_desc.lower() or "invalid" in error_desc.lower():
                        st.warning("💡 **Note:** File IDs are bot-specific. The file ID must come from a message that your bot has access to.")
                else:
                    st.error(f"❌ Network error: {str(e)}")
            except:
                st.error(f"❌ Network error: {str(e)}")
        else:
            st.error(f"❌ Network error: {str(e)}")
        return None
    except KeyError as e:
        st.error(f"❌ Unexpected API response format: {str(e)}")
        return None
    except Exception as e:
        error_msg = str(e)
        if "Telegram API error" in error_msg:
            # Handle Telegram API errors
            if "file_id" in error_msg.lower() or "invalid" in error_msg.lower():
                st.error(f"❌ Invalid file ID: The file ID '{file_id}' is not a valid Telegram file ID.")
                with st.expander("ℹ️ About Telegram File IDs"):
                    st.markdown("""
                    **Telegram File IDs** are unique identifiers for files in Telegram. They:
                    - Are typically long alphanumeric strings (e.g., `BAACAgIAAxkBAAIBY2Zg...`)
                    - Can sometimes be numeric, but must be valid Telegram file IDs
                    - Can expire or become invalid if files are deleted
                    - Are bot-specific: each bot gets different file IDs for the same file
                    
                    **Possible issues:**
                    1. The file IDs might be from a different bot
                    2. The file IDs might be expired or invalid
                    3. The bot might not have access to these files
                    
                    **Note:** File IDs generated by Telethon's `pack_bot_file_id` should work, 
                    but they need to be used with a bot that has access to the files.
                    """)
            else:
                st.error(f"❌ {error_msg}")
        else:
            st.error(f"❌ Error generating download link: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Error generating download link: {str(e)}")
        st.exception(e)  # Show full traceback for debugging
        return None

def main():
    # Title with subtitle
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-family: 'Barlow Condensed', sans-serif; font-weight: 700; color: #ffffff; font-size: 3.5rem; letter-spacing: 3px; margin-bottom: 0.5rem;">📚 PAST PAPER VAULT</h1>
        <p style="font-family: 'Poppins', sans-serif; color: #db463b; font-size: 1rem; font-weight: 400; letter-spacing: 1px; margin-top: 0;">powered by <strong>Examlanka.lk</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load master index
    df = load_master_index()
    
    if df.empty:
        st.warning("⚠️ No data available. Please ensure master_index.csv is present.")
        return
    
    # Get query parameter from URL
    query_params = st.query_params
    url_query = query_params.get("q", "")
    
    # Decode URL-encoded query
    if url_query:
        url_query = urllib.parse.unquote_plus(url_query)
    
    # Initialize session state for search query
    if 'search_query' not in st.session_state:
        st.session_state.search_query = url_query if url_query else ""
    
    # Update search query if URL parameter is present
    if url_query and url_query != st.session_state.search_query:
        st.session_state.search_query = url_query
    
    # Search interface - centered with search button
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
        st.write("")  # Spacing
        # Search button with icon
        search_button = st.button(
            "🔍 Search",
            key="search_btn",
            use_container_width=True,
            type="primary"
        )
    
    # Handle search on button click
    if search_button:
        st.session_state.search_query = search_query
        st.rerun()
    
    # Auto-search on input or URL parameter
    if search_query != st.session_state.search_query:
        st.session_state.search_query = search_query
    elif url_query and st.session_state.search_query:
        st.session_state.search_query = url_query
    
    # Display search results (flat list). Prime (year/subject/medium) matches are shown first.
    if st.session_state.search_query:
        results = fuzzy_search(st.session_state.search_query, df, limit=50)

        if not results.empty:
            # Get column names dynamically
            file_name_col = [col for col in results.columns if 'file' in col.lower() and 'name' in col.lower()]
            file_id_col = [col for col in results.columns if 'file' in col.lower() and 'id' in col.lower()]

            file_name_col = file_name_col[0] if file_name_col else results.columns[0]
            file_id_col = file_id_col[0] if file_id_col else results.columns[1] if len(results.columns) > 1 else results.columns[0]

            # Display flat grid sorted by prime then score
            num_cols = 3
            cols = st.columns(num_cols)
            for idx, (row_idx, row) in enumerate(results.iterrows()):
                file_name = row[file_name_col]
                file_id = str(row[file_id_col])
                match_score = row.get('Match Score', 0)
                prime = bool(row.get('Prime Match', False))

                display_name = file_name.replace('_', ' ').replace('-', ' ')
                col_idx = idx % num_cols

                with cols[col_idx]:
                    # Render compact tile HTML to avoid extra white cards
                    prime_html = ''
                    if prime:
                        prime_html = '<span style="background-color: #ffd700; color: #09262e; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 700; margin-left: 6px;">PRIME</span>'

                    tile_html = f"""
                    <div class="pdf-tile">
                        <div class="pdf-icon">{get_pdf_icon_svg()}</div>
                        <div class="pdf-name">{display_name}</div>
                        <div style='text-align:center; margin-top:6px;'>
                            <span style='background-color: rgba(219, 70, 59, 0.2); color: #db463b; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;'>Match: {match_score:.1f}%</span>
                            {prime_html}
                        </div>
                    </div>
                    """

                    st.markdown(tile_html, unsafe_allow_html=True)

                    # Download form/button
                    with st.form(key=f"form_{file_id}"):
                        submitted = st.form_submit_button("📥 Download", use_container_width=True)
                        if submitted:
                            download_url = get_telegram_download_url(file_id)
                            if download_url:
                                st.markdown(
                                    f'<a href="{download_url}" download="{file_name}" style="display: inline-block; width: 100%; padding: 0.5rem; background-color: #db463b; color: white; text-align: center; text-decoration: none; border-radius: 0.25rem; font-weight: bold; margin-top: 0.5rem; font-family: \'Barlow Condensed\', sans-serif;">⬇️ Click to Download</a>',
                                    unsafe_allow_html=True
                                )
                            else:
                                st.error("❌ Failed to generate link")
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #ffffff;">
                <h2 style="font-family: 'Barlow Condensed', sans-serif; font-size: 2rem; margin-bottom: 1rem;">🔍 No Results Found</h2>
                <p style="font-family: 'Poppins', sans-serif; font-size: 1.1rem;">Try a different search query</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Welcome message when no query
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #ffffff;">
            <h2 style="font-family: 'Barlow Condensed', sans-serif; font-size: 2.5rem; margin-bottom: 1rem; letter-spacing: 2px;">Welcome to Past Paper Vault</h2>
            <p style="font-family: 'Poppins', sans-serif; font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.9;">Search for past papers by subject, year, or school</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show statistics in a nice layout
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
            st.metric("Total Papers", len(df), label_visibility="visible")
        with col2:
            # Safely get unique files count
            try:
                unique_count = df['File Name'].nunique() if 'File Name' in df.columns else len(df)
            except:
                unique_count = len(df)
            st.metric("Unique Files", unique_count, label_visibility="visible")
        with col3:
            st.metric("Status", "🟢 Active", label_visibility="visible")

if __name__ == "__main__":
    main()

