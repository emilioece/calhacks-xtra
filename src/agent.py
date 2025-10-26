from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import base64
import io
from PIL import Image
from typing import Optional
import logging
from .config import ALLOWED_ORIGINS, LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET

# Import LiveKit and LLM components
from livekit import rtc
from livekit.agents import llm
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Log startup info
logger.info("🚀 Starting Quit Trigger Filter Agent")
logger.info("📦 LiveKit Agents version check...")
try:
    import livekit.agents
    logger.info(f"✅ LiveKit Agents loaded successfully")
    logger.info(f"   Version: {livekit.agents.__version__ if hasattr(livekit.agents, '__version__') else 'unknown'}")
except Exception as e:
    logger.error(f"❌ Failed to load LiveKit Agents: {e}")

try:
    from livekit import rtc
    logger.info("✅ LiveKit RTC loaded")
except Exception as e:
    logger.error(f"❌ Failed to load LiveKit RTC: {e}")

logger.info("🎯 Vision processing enabled via LiveKit LLM integration")


class FrameIn(BaseModel):
    pageUrl: str
    ts: int
    contentType: str
    frameB64: str


app = FastAPI(title="Quit Trigger Filter Ingest")

allow_origins = [o.strip() for o in (ALLOWED_ORIGINS or "").split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"]
)


# Configuration for trigger detection
TRIGGER_LIST = [
    "smoking",
    "cigarette",
    "vape",
    "alcohol",
    "drinking",
    "drug paraphernalia",
    "weapon",
    "violence",
    "harmful substances",
    "inappropriate content",
]

TRIGGER_DETECTION_PROMPT = f"""You are a content moderation system for addiction recovery support. Analyze this image and determine if it contains ANY of these triggers:

{', '.join(TRIGGER_LIST)}

Respond ONLY with JSON in this exact format:
{{"hasTrigger": true/false, "reason": "brief explanation"}}

If you detect ANY trigger, set hasTrigger to true."""

# Log the trigger detection prompt on startup
logger.info("🔧 Trigger Detection Configuration:")
logger.info(f"   Targets: {', '.join(TRIGGER_LIST)}")
logger.info(f"   Expected JSON format: {{\"hasTrigger\": true/false, \"reason\": \"explanation\"}}")
logger.info(f"   Prompt length: {len(TRIGGER_DETECTION_PROMPT)} chars")


async def detect_triggers_in_frame(image_bytes: bytes, llm_client: Optional[llm.LLM] = None) -> dict:
    """
    Detect triggers in a frame using an LLM vision model.
    
    Args:
        image_bytes: JPEG/PNG bytes
        llm_client: Optional LLM client (if None, uses OpenAI)
    
    Returns:
        dict with 'hasTrigger' (bool) and 'reason' (str)
    """
    logger.info(f"🔍 Starting vision analysis on {len(image_bytes)} bytes")
    
    if llm_client is None:
        logger.info("🔧 Initializing LLM client via LiveKit OpenAI plugin...")
        from livekit.plugins import openai as openai_plugin
        llm_client = openai_plugin.LLM(model="gpt-4o-mini")  # Can also use "gpt-4o" for better accuracy
        logger.info("✅ LiveKit OpenAI LLM initialized - using gpt-4o-mini for vision")
    
    # Convert bytes to PIL Image
    try:
        img = Image.open(io.BytesIO(image_bytes))
        logger.info(f"📷 Decoded image: {img.size[0]}x{img.size[1]} pixels, mode={img.mode}")
    except Exception as e:
        logger.error(f"❌ Failed to decode image: {e}")
        return {"hasTrigger": False, "reason": f"Failed to decode image: {e}", "error": True}
    
    # Convert to RGB if necessary
    if img.mode != "RGB":
        img = img.convert("RGB")
        logger.info(f"🎨 Converted image to RGB")
    
    # Save as JPEG to data URL for the LLM
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{img_b64}"
    logger.info(f"📦 Encoded image to base64: {len(img_b64)} chars")
    
    # Create chat context with the image using LiveKit's ImageContent
    chat_ctx = llm.ChatContext()
    image_content = llm.ImageContent(image=data_url)
    logger.info(f"📸 Created LiveKit ImageContent object")
    
    # Log the prompt being sent to the LLM
    logger.info("📋 Sending this prompt to LLM:")
    logger.info(f"   Prompt: {TRIGGER_DETECTION_PROMPT[:150]}...")
    logger.info(f"   Expected response: JSON with 'hasTrigger' and 'reason' fields")
    
    chat_ctx.add_message(
        role="user",
        content=[
            TRIGGER_DETECTION_PROMPT,
            image_content,
        ],
    )
    logger.info("🧠 Sending image + prompt to LiveKit LLM vision model...")
    
    # Call LLM via LiveKit
    try:
        logger.info("📡 Calling LiveKit LLM.chat() with vision context...")
        response = await llm_client.chat(ctx=chat_ctx)
        logger.info("✅ Received response from LiveKit LLM")
        
        # Parse response
        import json
        # Extract JSON from markdown if present
        text = response.choices[0].message.content
        logger.info(f"📝 Raw LLM response: {text[:200]}...")  # Log first 200 chars
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(text)
        
        # Show the full JSON response structure
        logger.info("📊 LLM Response (Full JSON):")
        logger.info(f"   {json.dumps(result, indent=2)}")
        logger.info(f"✅ Parsed: hasTrigger={result.get('hasTrigger')}, reason='{result.get('reason', 'N/A')}'")
        
        detection_result = {
            "hasTrigger": result.get("hasTrigger", False),
            "reason": result.get("reason", "No triggers detected"),
            "error": False
        }
        
        logger.info(f"🎯 Returning detection result: {json.dumps(detection_result)}")
        
        return detection_result
    except Exception as e:
        logger.error(f"❌ LLM error: {e}", exc_info=True)
        return {"hasTrigger": False, "reason": f"LLM error: {e}", "error": True}


@app.get("/health")
def health():
    logger.info("🏥 Health check")
    return {"ok": True}


@app.post("/ingest/frame")
async def ingest_frame(frame: FrameIn):
    logger.info(f"📨 Received frame from {frame.pageUrl} at timestamp {frame.ts}")
    
    try:
        data = base64.b64decode(frame.frameB64)
        logger.info(f"📦 Decoded frame: {len(data)} bytes, type={frame.contentType}")
    except Exception as exc:
        logger.error(f"❌ Failed to decode base64: {exc}")
        raise HTTPException(status_code=400, detail="invalid base64") from exc
    
    # For now, skip actual vision processing in MVP
    # In production, uncomment this:
    # logger.info("🔍 Processing frame through vision model...")
    # trigger_result = await detect_triggers_in_frame(data)
    # logger.info(f"🎯 Vision result: {trigger_result}")
    
    # MVP: Just validate and return metadata
    response = {
        "ok": True,
        "bytes": len(data),
        "pageUrl": frame.pageUrl,
        "contentType": frame.contentType,
        # Uncomment for production:
        # "hasTrigger": trigger_result.get("hasTrigger", False),
        # "reason": trigger_result.get("reason", "Not analyzed"),
    }
    logger.info(f"✅ Returning response for {frame.pageUrl}")
    return response

@app.post("/ingest/frame-with-vision")
async def ingest_frame_with_vision(frame: FrameIn):
    """Process frame through vision model for trigger detection. Use this endpoint for testing vision."""
    logger.info(f"🎯 TEST MODE: Processing frame with vision from {frame.pageUrl}")
    
    try:
        data = base64.b64decode(frame.frameB64)
        logger.info(f"📦 Decoded {len(data)} bytes")
    except Exception as exc:
        logger.error(f"❌ Failed to decode: {exc}")
        raise HTTPException(status_code=400, detail="invalid base64") from exc

    logger.info("🔍 Starting vision analysis...")
    trigger_result = await detect_triggers_in_frame(data)
    logger.info(f"🎯 Vision complete: {trigger_result}")

    return {
        "ok": True,
        "bytes": len(data),
        "pageUrl": frame.pageUrl,
        "hasTrigger": trigger_result.get("hasTrigger", False),
        "reason": trigger_result.get("reason", "No triggers detected"),
    }




