from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import tempfile
import os
import sys
import spacy

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.preprocessing.ocr_engine import extract_text_from_pdf
from src.postprocessing.rule_based_processer import RuleBasedProcessor

app = FastAPI(
    title="LexiScan API",
    description="Legal Contract Entity Extraction Service",
    version="1.0.0"
)

# Load model at startup
MODEL_PATH = os.path.join("models", "ner_model_v1")
nlp = None

@app.on_event("startup")
async def load_model():
    """Load NER model on startup"""
    global nlp
    try:
        if os.path.exists(MODEL_PATH):
            nlp = spacy.load(MODEL_PATH)
            print(f"✅ Model loaded from {MODEL_PATH}")
        else:
            print(f"⚠️ Warning: Model not found at {MODEL_PATH}")
            print("   API will run but extraction will fail")
    except Exception as e:
        print(f"❌ Error loading model: {e}")


class Entity(BaseModel):
    text: str
    label: str
    original_text: Optional[str] = None


class ExtractionResponse(BaseModel):
    success: bool
    message: str
    entities: List[Entity]
    metadata: Dict[str, any]


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "LexiScan API",
        "status": "running",
        "model_loaded": nlp is not None,
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "model_loaded": nlp is not None,
        "model_path": MODEL_PATH,
        "ready": nlp is not None
    }


@app.post("/extract", response_model=ExtractionResponse)
async def extract_entities(file: UploadFile = File(...)):
    """
    Extract entities from uploaded PDF contract
    
    Args:
        file: PDF file to process
    
    Returns:
        JSON with extracted entities
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Check if model is loaded
    if nlp is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Service unavailable."
        )
    
    # Save uploaded file temporarily
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            contents = await file.read()
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        # Step 1: Extract text using OCR
        print(f"Processing: {file.filename}")
        text = extract_text_from_pdf(tmp_path)
        
        if not text or len(text.strip()) < 50:
            os.unlink(tmp_path)
            return ExtractionResponse(
                success=False,
                message="Failed to extract text from PDF. File may be corrupted or empty.",
                entities=[],
                metadata={"filename": file.filename}
            )
        
        # Step 2: Extract entities using NER model
        doc = nlp(text)
        raw_entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        # Step 3: Apply post-processing rules
        cleaned_entities = apply_rules(raw_entities)
        final_entities = deduplicate_entities(cleaned_entities)
        
        # Convert to response format
        entities = [
            Entity(
                text=e['text'],
                label=e['label'],
                original_text=e.get('original_text')
            )
            for e in final_entities
        ]
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        # Prepare metadata
        metadata = {
            "filename": file.filename,
            "text_length": len(text),
            "entities_found": len(entities),
            "entities_by_type": {}
        }
        
        # Count entities by type
        for entity in entities:
            label = entity.label
            metadata["entities_by_type"][label] = metadata["entities_by_type"].get(label, 0) + 1
        
        return ExtractionResponse(
            success=True,
            message=f"Successfully extracted {len(entities)} entities",
            entities=entities,
            metadata=metadata
        )
    
    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )


@app.post("/extract-text")
async def extract_text_only(file: UploadFile = File(...)):
    """
    Extract only text from PDF (no entity extraction)
    Useful for debugging OCR quality
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            contents = await file.read()
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        text = extract_text_from_pdf(tmp_path)
        os.unlink(tmp_path)
        
        return {
            "success": True,
            "filename": file.filename,
            "text": text,
            "text_length": len(text)
        }
    
    except Exception as e:
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting text: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)