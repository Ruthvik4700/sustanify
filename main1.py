import streamlit as st
import requests
from huggingface_hub import InferenceClient
import json

# Page configuration
st.set_page_config(
    page_title="sustanify",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    div.block-container {padding-top: 1rem;}
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
    }
    div.stButton > button:hover {
        background-color: #45a049;
    }
    </style>
""", unsafe_allow_html=True)

# Define endpoint and API key for OCR API
ocr_url = 'https://api.ocr.space/parse/image'
ocr_api_key = 'K846235862889573'

# Initialize Hugging Face client
client = InferenceClient(api_key="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")

def get_sustainable_alternatives(product_text, overall_score, category_scores):
    """Generate sustainable product recommendations based on analysis"""
    if overall_score >= 7:
        return None  # No recommendations needed for highly sustainable products
    
    prompt = {
        "role": "user",
        "content": f"""Based on the following product information and scores, suggest 3-4 specific sustainable alternatives.
        Focus on addressing the weakest areas. Format recommendations as bullet points.
        
        Product Text: {product_text}
        Overall Sustainability Score: {overall_score}/10
        
        Category Scores:
        Company Impact: {category_scores.get('company', 0)}/10
        Ingredients Quality: {category_scores.get('ingredients', 0)}/10
        Packaging Impact: {category_scores.get('packaging', 0)}/10
        
        Provide specific brand names and explain why each alternative is more sustainable.
        """
    }
    
    try:
        response = client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            messages=[prompt],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating recommendations: {str(e)}")
        return None

def get_score_color(score):
    if score >= 7:
        return "#28a745"  # Green for good scores
    elif score >= 4:
        return "#ffc107"  # Yellow for medium scores
    else:
        return "#dc3545"  # Red for low scores

def display_score(score, parameter):
    score_color = get_score_color(score)
    
    st.markdown(f"""
        <div style='margin-bottom: 1rem;'>
            <div style='font-weight: 500; margin-bottom: 0.5rem;'>{parameter}</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.progress(score/10)
    with col2:
        st.markdown(f"<h3 style='text-align: center; margin: 0; color: {score_color};'>{score}</h3>", unsafe_allow_html=True)

def parse_model_output(response_text):
    try:
        scores = {}
        lines = response_text.split('\n')
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if ":" in line:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    try:
                        numeric_value = float(''.join(filter(lambda x: x.isdigit() or x == '.', value)))
                        numeric_value = min(max(numeric_value, 0), 10)
                        scores[key] = numeric_value
                    except ValueError:
                        continue
        
        return scores
    except Exception as e:
        st.error(f"Error parsing model output: {str(e)}")
        return {}

# Create a centered header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<h1 style='text-align: center; color: #4CAF50; margin-bottom: 0;'>🌱 sustainify</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em; margin-top: 0;'>Your Sustainable Product Analysis Tool</p>", unsafe_allow_html=True)

# Upload section
st.markdown("""
    <div style='padding: 1rem; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 2rem;'>
        <h3 style='margin-bottom: 1rem;'>Upload Product Image</h3>
    </div>
""", unsafe_allow_html=True)

uploaded_image = st.file_uploader(
    "Choose a clear image of the product or packaging",
    type=["jpg", "jpeg", "png"],
    help="Supported formats: JPG, JPEG, PNG"
)

if uploaded_image is not None:
    img_col, status_col = st.columns([2, 1])
    
    with img_col:
        st.image(uploaded_image, use_column_width=True)
    
    with status_col:
        st.markdown("### Analysis Status")
        with st.spinner("🔍 Processing image..."):
            response = requests.post(
                ocr_url,
                files={'filename': uploaded_image},
                data={'apikey': ocr_api_key, 'language': 'eng'}
            )

            if response.status_code == 200:
                result = response.json()
                if 'ParsedResults' in result and result['ParsedResults']:
                    text = result['ParsedResults'][0]['ParsedText']
                    with st.expander("📝 View Extracted Text"):
                        st.text(text)
                    company_info = text
                    st.success("✅ Text extraction complete")
                else:
                    st.error("❌ No text could be extracted from the image.")
            else:
                st.error("⚠️ Error with OCR service. Please try again.")

        if 'company_info' in locals():
            with st.spinner("🤖 Analyzing sustainability..."):
                # Prompts for analysis
                prompts = {
                    'company': {
                        "role": "user",
                        "content": f"""Analyze this product text and rate each company parameter on a scale of 1-10:
                        Text: '{company_info}'
                        Parameters to rate:
                        - Environmental Impact
                        - Supply Chain Responsibility
                        - Product Lifecycle
                        - Social Responsibility and Ethics
                        - Sustainability Reporting and Certification
                        
                        Provide only the parameter name and score, like this:
                        Parameter: Score"""
                    },
                    'ingredients': {
                        "role": "user",
                        "content": f"""Analyze this product text and rate each ingredient parameter on a scale of 1-10:
                        Text: '{company_info}'
                        Parameters to rate:
                        - Sourcing and Origin
                        - Environmental Impact of Production
                        - Ethical Labor Practices
                        - Health and Safety
                        - Toxicity
                        
                        Provide only the parameter name and score, like this:
                        Parameter: Score"""
                    },
                    'packaging': {
                        "role": "user",
                        "content": f"""Analyze this product text and rate each packaging parameter on a scale of 1-10:
                        Text: '{company_info}'
                        Parameters to rate:
                        - Material Sustainability
                        - Recyclability and Circular Economy
                        - Reduction in Material Use
                        - Energy and Water Consumption in Production
                        - Brand Transparency and Certifications
                        
                        Provide only the parameter name and score, like this:
                        Parameter: Score"""
                    }
                }

                # Get scores for each category
                company_response = client.chat.completions.create(
                    model="mistralai/Mistral-7B-Instruct-v0.3",
                    messages=[prompts['company']],
                    max_tokens=500,
                    temperature=0.7
                )
                
                ingredients_response = client.chat.completions.create(
                    model="mistralai/Mistral-7B-Instruct-v0.3",
                    messages=[prompts['ingredients']],
                    max_tokens=500,
                    temperature=0.7
                )
                
                packaging_response = client.chat.completions.create(
                    model="mistralai/Mistral-7B-Instruct-v0.3",
                    messages=[prompts['packaging']],
                    max_tokens=500,
                    temperature=0.7
                )

                # Parse scores
                company_scores = parse_model_output(company_response.choices[0].message.content)
                ingredients_scores = parse_model_output(ingredients_response.choices[0].message.content)
                packaging_scores = parse_model_output(packaging_response.choices[0].message.content)

                st.success("✅ Analysis complete")

    # Display results
    st.markdown("## 📊 Sustainability Assessment Results")
    
    # Calculate overall scores
    overall_company = sum(company_scores.values()) / len(company_scores) if company_scores else 0
    overall_ingredients = sum(ingredients_scores.values()) / len(ingredients_scores) if ingredients_scores else 0
    overall_packaging = sum(packaging_scores.values()) / len(packaging_scores) if packaging_scores else 0
    
    # Calculate overall sustainability score
    overall_sustainability = (overall_company + overall_ingredients + overall_packaging) / 3
    
    # Display overall sustainability score
    st.markdown(f"""
        <div style='text-align: center; padding: 2rem; background-color: #f8f9fa; border-radius: 10px; margin: 2rem 0;'>
            <h2 style='color: #4CAF50; margin-bottom: 0.5rem;'>Overall Sustainability Score</h2>
            <div style='font-size: 3em; font-weight: bold; color: #2E7D32;'>
                {overall_sustainability:.1f}/10
            </div>
            <div style='color: #666; margin-top: 0.5rem;'>
                Based on company impact, ingredients, and packaging analysis
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Create a visual gauge for the overall score
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.progress(overall_sustainability/10)
        
        # Add a rating text based on the score
        rating_text = ""
        if overall_sustainability >= 8:
            rating_text = "🌟 Excellent Sustainability"
        elif overall_sustainability >= 6:
            rating_text = "✅ Good Sustainability"
        elif overall_sustainability >= 4:
            rating_text = "⚠️ Average Sustainability"
        else:
            rating_text = "❌ Poor Sustainability"
            
        st.markdown(f"<p style='text-align: center; font-size: 1.2em; color: {get_score_color(overall_sustainability)};'>{rating_text}</p>", unsafe_allow_html=True)

    # Display category scores
    st.markdown("### Category Scores")
    category_cols = st.columns(3)
    with category_cols[0]:
        st.metric("Company Impact", f"{overall_company:.1f}/10", 
                 delta="Environmental & Social" if overall_company >= 6 else "Needs Improvement")
    with category_cols[1]:
        st.metric("Ingredients Quality", f"{overall_ingredients:.1f}/10", 
                 delta="Sustainable Sourcing" if overall_ingredients >= 6 else "Needs Improvement")
    with category_cols[2]:
        st.metric("Packaging Impact", f"{overall_packaging:.1f}/10", 
                 delta="Eco-Friendly" if overall_packaging >= 6 else "Needs Improvement")

    # Create tabs for detailed scores
    tab1, tab2, tab3 = st.tabs(["🏢 Company Impact", "🌿 Ingredients", "📦 Packaging"])
    
    with tab1:
        st.markdown("### Company Sustainability Metrics")
        for parameter, rating in company_scores.items():
            display_score(rating, parameter)

    with tab2:
        st.markdown("### Ingredients Assessment")
        for parameter, rating in ingredients_scores.items():
            display_score(rating, parameter)

    with tab3:
        st.markdown("### Packaging Evaluation")
        for parameter, rating in packaging_scores.items():
            display_score(rating, parameter)

    # Add recommendations section if sustainability score is low
    if overall_sustainability < 7:
        st.markdown("""
            <div style='background-color: #fff3cd; padding: 1rem; border-radius: 10px; margin: 2rem 0;'>
                <h3 style='color: #856404; margin-bottom: 1rem;'>🌱 Sustainable Alternatives</h3>
            </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("Generating sustainable alternatives..."):
            recommendations = get_sustainable_alternatives(
                company_info, 
                overall_sustainability,
                {
                    'company': overall_company,
                    'ingredients': overall_ingredients,
                    'packaging': overall_packaging
                }
            )
            
            if recommendations:
                # Create columns for better visual organization
                rec_col1, rec_col2 = st.columns([3, 1])
                
                with rec_col1:
                    st.markdown(recommendations)
                
                with rec_col2:
                    st.markdown("""
                        <div style='background-color: #e8f5e9; padding: 1rem; border-radius: 10px;'>
                            <h4 style='color: #2e7d32; margin-bottom: 0.5rem;'>Why Consider Alternatives?</h4>
                            <p style='font-size: 0.9em; color: #1b5e20;'>
                                These recommendations are based on:
                                <ul>
                                    <li>Higher sustainability scores</li>
                                    <li>Better environmental impact</li>
                                    <li>Improved ethical practices</li>
                                    <li>More eco-friendly packaging</li>
                                </ul>
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Add a call-to-action button
                st.markdown("""
                    <div style='text-align: center; margin-top: 1rem;'>
                        <p style='color: #666; font-size: 0.9em;'>
                            Learn more about these sustainable alternatives and their environmental impact.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔍 Compare Products in Detail"):
                    st.info("This feature will allow you to compare detailed sustainability metrics of alternative products. Coming soon!")

else:
    st.markdown("""
        <div style='text-align: center; padding: 2rem; background-color: #f8f9fa; border-radius: 10px; margin: 2rem 0;'>
            <h2 style='color: #4CAF50;'>👆 Get Started</h2>
            <p style='font-size: 1.1em; color: #666;'>Upload a product image to analyze its sustainability metrics</p>
        </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <p style='color: #666;'>Making sustainable choices easier, one product at a time.</p>
    </div>
""", unsafe_allow_html=True)