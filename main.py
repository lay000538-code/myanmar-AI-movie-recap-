import os
import subprocess
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.post("/process-recap")
async def process_recap(video: UploadFile = File(...)):
    input_video_path = f"temp_{video.filename}"
    audio_path = "burmese_voice.mp3"
    output_video_path = "final_burmese_recap.mp4"

    try:
        with open(input_video_path, "wb") as f:
            f.write(await video.read())

        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = """
        ဒီရုပ်ရှင်ဗီဒီယိုအတွက် ပရိသတ်စိတ်ဝင်စားဖွယ် မြန်မာလို Movie Recap စာသားကို ဇာတ်လမ်းပြောသူ (Narrator) လေသံဖြင့် အကျဉ်းချုပ် ရေးပေးပါ။
        စကားလုံးအရေအတွက်ကို စက္ကန့် ၃၀ စာခန့် ကန့်သတ်ရေးပေးပါ။ ဖတ်ရလွယ်ကူပြီး အသံထွက်ကောင်းမယ့် မြန်မာစာသားသက်သက်ပဲ ပြန်ပေးပါ။
        """
        
        response = model.generate_content(prompt)
        burmese_script = response.text or "ဒီဇာတ်ကားမှာတော့ စိတ်လှုပ်ရှားစရာ ကောင်းတဲ့ အလှည့်အပြောင်းတွေနဲ့ စတင်လိုက်ပါပြီ..."

        tts = gTTS(text=burmese_script, lang="my", slow=False)
        tts.save(audio_path)

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video_path,
            "-i", audio_path,
            "-filter_complex", "[0:a]volume=0.2[a0];[1:a]volume=1.5[a1];[a0][a1]amix=inputs=2:duration=longest[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            output_video_path
        ]
        
        subprocess.run(cmd, check=True)

        return FileResponse(
            output_video_path, 
            media_type="video/mp4", 
            filename="burmese_recap.mp4"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
