import streamlit as st
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import tempfile
import os
import io
import time
import google.generativeai as genai

# Initialize the speech recognition engine
recognizer = sr.Recognizer()
microphone = sr.Microphone()

def record_speech():
    """Record speech from microphone and convert to text"""
    try:
        with microphone as source:
            st.info("🎤 Listening... Speak now!")
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source)
            # Record audio with timeout
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
        
        st.info("🔄 Processing speech...")
        # Convert speech to text using Google's speech recognition
        text = recognizer.recognize_google(audio)
        return text
    
    except sr.WaitTimeoutError:
        return "Timeout: No speech detected"
    except sr.UnknownValueError:
        return "Could not understand the audio"
    except sr.RequestError as e:
        return f"Error with speech recognition service: {e}"

def get_gemini_response(text, api_key, use_api=True, model_name="gemini-pro"):
    """Get response from Google Gemini AI or placeholder"""
    
    if not use_api or not api_key:
        # Placeholder response
        time.sleep(1)
        responses = {
            "hello": "Hello! How can I help you today?",
            "weather": "I don't have access to current weather data, but I hope it's nice where you are!",
            "time": "I don't have access to real-time data, but you can check your device's clock.",
            "default": f"I heard you say: '{text}'. Hello, this is a sample response from Gemini AI placeholder."
        }
        
        text_lower = text.lower()
        if "hello" in text_lower or "hi" in text_lower:
            return responses["hello"]
        elif "weather" in text_lower:
            return responses["weather"]
        elif "time" in text_lower:
            return responses["time"]
        else:
            return responses["default"]
    
    else:
        # Real Google Gemini AI API call
        try:
            # Configure the API key
            genai.configure(api_key=api_key)
            
            # Initialize the model
            model = genai.GenerativeModel(model_name)
            
            # Generate response
            response = model.generate_content(text)
            
            return response.text
            
        except Exception as e:
            return f"Error calling Gemini API: {str(e)}"

def text_to_speech_gtts(text):
    """Convert text to speech using Google Text-to-Speech"""
    try:
        # Create gTTS object
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            return tmp_file.name
    except Exception as e:
        st.error(f"Error generating speech: {e}")
        return None

def text_to_speech_pyttsx3(text):
    """Convert text to speech using pyttsx3 (offline)"""
    try:
        engine = pyttsx3.init()
        
        # Set properties (optional)
        voices = engine.getProperty('voices')
        if voices:
            engine.setProperty('voice', voices[0].id)  # Use first available voice
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 0.8)  # Volume level (0.0 to 1.0)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            engine.save_to_file(text, tmp_file.name)
            engine.runAndWait()
            return tmp_file.name
    except Exception as e:
        st.error(f"Error with pyttsx3: {e}")
        return None

# Streamlit App
def main():
    st.title("🎙️ Voice Chat with Google Gemini AI")
    st.markdown("Speak to Gemini and hear its response!")
    
    # API Configuration in main area
    st.subheader("🔧 API Configuration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # API Key input - replace with your real Google AI Studio key
        api_key = st.text_input(
            "Google AI Studio API Key:", 
            value="gvgdygxtgdxgshns",  # Your provided key - change this to your real Google AI key
            type="password",
            help="Get your API key from https://makersuite.google.com/app/apikey"
        )
    
    with col2:
        # Toggle API usage
        use_gemini_api = st.checkbox(
            "Use Real Gemini API", 
            value=True,
            help="Uncheck to use demo responses"
        )
    
    # Model selection (only show if using real API)
    if use_gemini_api and api_key:
        model_choice = st.selectbox(
            "Gemini Model:",
            ["gemini-pro", "gemini-pro-vision","gemini-2.0-flash"],
            help="Choose which Gemini model to use"
        )
    else:
        model_choice = "gemini-pro"
    
    # API Status
    if use_gemini_api and api_key:
        st.success(f"✅ Using Real Gemini API ({model_choice})")
    else:
        st.info("📝 Using Demo Mode")
    
    st.markdown("---")
    
    # Initialize session state
    if 'transcribed_text' not in st.session_state:
        st.session_state.transcribed_text = ""
    if 'llm_response' not in st.session_state:
        st.session_state.llm_response = ""
    
    # Choose TTS method
    tts_method = st.selectbox(
        "Choose Text-to-Speech method:",
        ["Google TTS (gTTS) - Online", "pyttsx3 - Offline"]
    )
    
    # Main interaction
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎤 Start Recording", type="primary"):
            with st.spinner("Recording and processing..."):
                # Step 1: Record speech and convert to text
                transcribed = record_speech()
                st.session_state.transcribed_text = transcribed
                
                if transcribed and not transcribed.startswith(("Timeout", "Could not", "Error")):
                    # Step 2: Get Gemini response
                    with st.spinner("Getting Gemini's response..."):
                        response = get_gemini_response(
                            transcribed, 
                            api_key=api_key,
                            use_api=use_gemini_api,
                            model_name=model_choice
                        )
                        st.session_state.llm_response = response
                    
                    # Step 3: Convert response to speech
                    with st.spinner("Generating audio..."):
                        if tts_method.startswith("Google"):
                            audio_file = text_to_speech_gtts(response)
                        else:
                            audio_file = text_to_speech_pyttsx3(response)
                        
                        if audio_file:
                            st.session_state.audio_file = audio_file
    
    with col2:
        if st.button("🔄 Clear All"):
            st.session_state.transcribed_text = ""
            st.session_state.llm_response = ""
            if 'audio_file' in st.session_state:
                try:
                    os.unlink(st.session_state.audio_file)
                except:
                    pass
                del st.session_state.audio_file
    
    # Display results
    if st.session_state.transcribed_text:
        st.subheader("📝 What you said:")
        st.write(st.session_state.transcribed_text)
    
    if st.session_state.llm_response:
        st.subheader("🤖 Gemini's Response:")
        st.write(st.session_state.llm_response)
        
        # Play audio response
        if 'audio_file' in st.session_state and os.path.exists(st.session_state.audio_file):
            st.subheader("🔊 Listen to Response:")
            try:
                with open(st.session_state.audio_file, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format='audio/mp3' if st.session_state.audio_file.endswith('.mp3') else 'audio/wav')
            except Exception as e:
                st.error(f"Error playing audio: {e}")
    
    # Instructions
    st.markdown("---")
    st.subheader("📋 How to use:")
    st.markdown("""
    1. **Replace the API key above** with your real Google AI Studio API key
    2. **Make sure "Use Real Gemini API" is checked** to get real Gemini responses
    3. **Choose your preferred Gemini model** (gemini-pro or gemini-pro-vision)
    4. **Click 'Start Recording'** - The app will listen for 10 seconds
    5. **Speak clearly** into your microphone
    6. **View your transcribed text** and Gemini's response
    7. **Listen to the response** using the audio player
    8. **Click 'Clear All'** to start over
    
    **Note:** Make sure your microphone is working and you've granted permission to use it.
    """)
    
    # API Setup Guide
    with st.expander("🔑 How to get your Google AI Studio API Key"):
        st.markdown("""
        **Step-by-step guide:**
        1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Sign in with your Google account
        3. Click "Create API Key"
        4. Choose "Create API key in new project" or select existing project
        5. Copy the generated API key
        6. Replace the placeholder key above
        7. Make sure "Use Real Gemini API" is checked
        
        **Free Tier:** Google AI Studio offers generous free usage limits for testing.
        
        **Security:** Your API key is only stored in your browser session.
        """)
    
    # Model Information
    with st.expander("ℹ️ About Gemini Models"):
        st.markdown("""
        **Available Models:**
        - **gemini-pro**: Best for text-based conversations, reasoning, and general tasks
        - **gemini-pro-vision**: Can understand both text and images (for future image features)
        
        **Features:**
        - Fast response times
        - Advanced reasoning capabilities
        - Multi-turn conversations
        - Free tier available
        """)
    
    # Troubleshooting
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **Common issues:**
        - **API Key Error**: Make sure your Google AI Studio API key is valid
        - **Rate Limit**: Wait a moment if you hit rate limits (free tier has limits)
        - **Microphone not working**: Check browser permissions and system microphone settings
        - **PyAudio installation issues**: 
          - Windows: `pip install pipwin && pipwin install pyaudio`
          - Mac: `brew install portaudio && pip install pyaudio`
          - Linux: `sudo apt-get install portaudio19-dev && pip install pyaudio`
        - **No internet for gTTS**: Use the offline pyttsx3 option instead
        - **Audio not playing**: Try refreshing the page or clearing the session
        """)

if __name__ == "__main__":
    main()