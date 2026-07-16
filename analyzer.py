import base64
import json
from groq import Groq

def analyze_landing_page(screenshot_path: str, html_content: str, url: str, api_key: str) -> dict:
    client = Groq(api_key=api_key)

    with open(screenshot_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    prompt = """You are a conversion rate optimization (CRO) expert. Analyze this landing page screenshot and the HTML content.

Provide a detailed analysis in JSON format with this exact structure:
{
    "overall_score": <number 0-100>,
    "categories": [
        {
            "name": "Hero Section",
            "score": <1-10>,
            "status": "good" | "warning" | "bad",
            "issues": ["issue1", "issue2"],
            "fixes": ["fix1", "fix2"]
        },
        {
            "name": "CTA Buttons",
            "score": <1-10>,
            "status": "good" | "warning" | "bad",
            "issues": ["issue1"],
            "fixes": ["fix1"]
        },
        {
            "name": "Trust Signals",
            "score": <1-10>,
            "status": "good" | "warning" | "bad",
            "issues": ["issue1"],
            "fixes": ["fix1"]
        },
        {
            "name": "Color Palette",
            "score": <1-10>,
            "status": "good" | "warning" | "bad",
            "issues": ["issue1"],
            "fixes": ["fix1"]
        },
        {
            "name": "Typography",
            "score": <1-10>,
            "status": "good" | "warning" | "bad",
            "issues": ["issue1"],
            "fixes": ["fix1"]
        },
        {
            "name": "Copy Quality",
            "score": <1-10>,
            "status": "good" | "warning" | "bad",
            "issues": ["issue1"],
            "fixes": ["fix1"]
        },
        {
            "name": "Layout and Flow",
            "score": <1-10>,
            "status": "good" | "warning" | "bad",
            "issues": ["issue1"],
            "fixes": ["fix1"]
        },
        {
            "name": "Mobile UX",
            "score": <1-10>,
            "status": "good" | "warning" | "bad",
            "issues": ["issue1"],
            "fixes": ["fix1"]
        },
        {
            "name": "Speed Hints",
            "score": <1-10>,
            "status": "good" | "warning" | "bad",
            "issues": ["issue1"],
            "fixes": ["fix1"]
        },
        {
            "name": "Conversion Barriers",
            "score": <1-10>,
            "status": "good" | "warning" | "bad",
            "issues": ["issue1"],
            "fixes": ["fix1"]
        }
    ],
    "quick_wins": [
        {"impact": "high", "effort": "low", "description": "fix description"},
        {"impact": "high", "effort": "low", "description": "fix description"},
        {"impact": "high", "effort": "low", "description": "fix description"}
    ],
    "summary": "Brief overall assessment in 2-3 sentences"
}

Analyze:
- Hero: headline clarity, value proposition, first impression
- CTA: button text, placement, color contrast, size, urgency
- Trust: testimonials, logos, guarantees, social proof
- Colors: harmony, contrast, distraction, brand consistency
- Typography: readability, hierarchy, font choices
- Copy: persuasion, clarity, objection handling, urgency
- Layout: visual hierarchy, whitespace, information architecture
- Mobile: responsive design, touch targets, readability
- Speed: image size, clutter, load-time red flags
- Barriers: friction points, missing elements, confusing nav

URL analyzed: """ + url

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            }
        ],
        temperature=0.3,
        max_tokens=4096,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)
    return result



